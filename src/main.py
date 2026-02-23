from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user, UserMixin
from .models import Administrator, Offer, Application, OrganizationWorker, Project, Rating, User, Inquiry
from . import db
from datetime import datetime


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    # If user is currently logged in, we redirect him to dashboard.html
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    # Fetching admins just in case we need to display contact info on the landing page
    admins = Administrator.query.all()
    # Renders the main authentication/landing page
    return render_template('auth/auth.html', admins=admins)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    my_type = current_user.user_type
    all_offers = Offer.query.filter_by(status='approved').order_by(Offer.date_created.desc()).all()
    projects = Project.query.all()

    inquiries = []
    if current_user.user_type == 'worker':
        inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()

    return render_template('dashboard.html',
                           user_type=my_type,
                           offers=all_offers,
                           projects=projects,
                           inquiries=inquiries)


@main_bp.route('/create-offer', methods=['GET', 'POST'])
@login_required
def create_offer():
    # Security check: Only Donors and Administrators can create offers
    if current_user.user_type not in ['donor', 'administrator']:
        flash('Permission denied. Only donors can create offers.', category='error')
        return redirect(url_for('main.dashboard'))

    # Fetch active projects to display in the dropdown menu
    projects = Project.query.all()

    if request.method == "POST":
        # Retrieve data from the HTML form
        title = request.form.get('title')
        description = request.form.get('description')
        offer_type = request.form.get('type')

        # Get selected src ID from the form
        project_id = request.form.get('project_id')

        if project_id:
            project = Project.query.get(project_id)
            if project and project.status == 'finished':
                flash('You cannot add offers to a finished src.', category='error')
                return redirect(url_for('main.dashboard'))


        # Handle "No Project" selection (value '0' or empty) - set to None
        if not project_id or project_id == '0':
            project_id = None

        # Create a new Offer object
        new_offer = Offer(
            title=title,
            description=description,
            offer_type=offer_type,
            donor_id=current_user.id,
            status='pending',  # New offers must wait for Worker approval
            project_id=project_id  # Link offer to a specific src (optional)
        )

        # Save the new offer to the database
        db.session.add(new_offer)
        db.session.commit()

        flash("Your offer has been successfully added!", category='success')
        return redirect(url_for('main.dashboard'))

    # If the request method is GET, show the form and pass the projects list
    return redirect(url_for('main.dashboard'))


@main_bp.route('/offer/<int:offer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    # 1. Security check: Tylko właściciel (donor) lub administrator może edytować ofertę
    if current_user.id != offer.donor_id and current_user.user_type != 'administrator':
        flash('Nie masz uprawnień do edycji tej oferty.', category='error')
        return redirect(url_for('main.dashboard'))

    # 2. Pobierz listę projektów do dropdowna
    projects = Project.query.all()

    if request.method == 'POST':
        # 3. Pobranie danych z formularza
        title = request.form.get('title')
        description = request.form.get('description')
        offer_type = request.form.get('type')
        project_id = request.form.get('project_id')

        # 4. Walidacja projektu (podobnie jak w create_offer)
        if project_id and project_id != '0':
            project = Project.query.get(project_id)
            if project and project.status == 'finished':
                flash('Nie możesz przypisać oferty do zakończonego projektu.', category='error')
                return redirect(url_for('main.edit_offer', offer_id=offer.id))
            offer.project_id = project_id
        else:
            offer.project_id = None

        # 5. Aktualizacja pól
        offer.title = title
        offer.description = description
        offer.offer_type = offer_type


        db.session.commit()
        flash('Oferta została pomyślnie zaktualizowana!', category='success')
        return redirect(url_for('main.dashboard'))

    # Jeśli GET - renderujemy formularz edycji (np. ten sam co create_offer, ale z danymi)
    return redirect(url_for('main.dashboard'))

@main_bp.route('/offer/<int:offer_id>')
@login_required
def offer_details(offer_id):
    # Try to get the offer, return 404 error if not found
    offer = Offer.query.get_or_404(offer_id)

    # Security check:
    # If the offer is NOT approved, only the Admin, Worker, or the Owner (Donor) can see it.
    # This prevents users from guessing URLs to see hidden/pending offers.
    if offer.status != 'approved' and current_user.user_type not in ['administrator', 'worker'] and current_user.id != offer.donor_id:
        abort(403)  # 403 Forbidden

    return render_template('offer_details.html', offer=offer)


@main_bp.route('/offer/<int:offer_id>/apply', methods=['POST'])
@login_required
def apply_for_offer(offer_id):
    # 1. Role check: Only beneficiaries can apply for help
    if current_user.user_type != 'beneficient':
        flash("Only beneficiaries can apply for help!", category='error')
        return redirect(url_for('main.dashboard'))

    offer = Offer.query.get_or_404(offer_id)

    # 2. Duplication check: Prevent sending multiple applications for the same offer
    existing_application = Application.query.filter_by(offer_id=offer_id, applicant_id=current_user.id).first()
    if existing_application:
        flash("You have already applied for this offer! Please wait for a response.")
        return redirect(url_for('main.dashboard'))

    # 3. Retrieve the message from the form
    msg = request.form.get('message')

    # 4. Create the Application object (Link between User and Offer)
    new_application = Application(
        message=msg,
        offer_id=offer.id,
        applicant_id=current_user.id
        # dodac status oferty
    )

    # 5. Commit changes to the database
    db.session.add(new_application)
    db.session.commit()

    flash('Your application has been sent to the Donor!', category='success')

    return redirect(url_for('main.dashboard'))


@main_bp.route('/offer/<int:offer_id>/manage')
@login_required
def manage_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    # Security check: Ensure that only the owner of the offer can manage it
    if offer.donor_id != current_user.id:
        flash("Only the donor can manage their own offer.", category='error')
        return redirect(url_for('main.dashboard'))

    # Fetch all applications related to this offer using the relationship
    applications = offer.applications

    # Pass the applications list to the template
    return render_template('manage_offer.html', applications=applications, offer=offer)



# Subpage
@main_bp.route('/application/<int:app_id>/accept', methods=['POST'])
@login_required
def accept_application(app_id):
    application = Application.query.get_or_404(app_id)

    # Security check: Verify if the current user is the owner of the offer associated with this application
    if application.offer.donor_id != current_user.id:
        flash('You cannot manage applications for offers that are not yours!', category='error')
        return redirect(url_for('main.dashboard'))

    # Update statuses
    application.status = 'accepted'
    application.offer.status = 'closed'  # Close the offer so it disappears from the

    for other_application in application.offer.applications:
        if other_application.id != application.id and other_application.status == 'pending':
            other_application.status = 'rejected'

    # Save changes to the database
    db.session.commit()

    flash(f'You have accepted help for user {application.applicant.first_name}!', category='success')

    # Redirect back to the management page
    #return redirect(url_for('main.manage_offer', offer_id=application.offer.id))
    return redirect(url_for('main.dashboard'))


# --- WORKER PANEL (MODERATION) ---
@main_bp.route('/worker/pending_users')
@login_required
def pending_users():
    if current_user.user_type != 'worker':
        abort(403)
    # Get all unauthorized users
    waiting_users = User.query.filter_by(is_approved=False).all()
    return render_template('worker_users.html', users=waiting_users)

# subpage
@main_bp.route('/worker/user/<int:user_id>/approve', methods=['POST'])
@login_required
def approve_user(user_id):
    if current_user.user_type != 'worker':
        abort(403)
    user = User.query.get_or_404(user_id)
    user.is_approved=True
    db.session.commit()
    flash(f"Account {user.email} has been approved", category='success')
    return redirect(url_for('main.pending_users'))


@main_bp.route('/worker/pending')
@login_required
def pending_offers():
    # Only Workers (and Administrators) should access this panel
    if current_user.user_type != 'worker' and current_user.user_type != 'administrator':
        flash('Access denied. Panel restricted to employees.', category='error')
        return redirect(url_for('main.dashboard'))

    # Fetch offers with 'pending' status
    pending_offers = Offer.query.filter_by(status='pending').order_by(Offer.date_created.asc()).all()

    return redirect(url_for('main.dashboard'))


@main_bp.route('/worker/offer/<int:offer_id>/approve', methods=['POST'])
@login_required
def approve_offer(offer_id):
    # 1. Permission Check: Only Workers can approve offers (Strict IO requirement)
    if current_user.user_type != 'worker':
        abort(403)  # Return "Forbidden" error if the user is unauthorized

    offer = Offer.query.get_or_404(offer_id)

    # 2. Change status to 'approved'
    # This makes the offer visible on the main Dashboard for all users
    offer.status = 'approved'
    db.session.commit()

    flash(f'Offer "{offer.title}" has been approved.', category='success')

    # Redirect back to the list of pending offers
    return redirect(url_for('main.pending_offers'))


@main_bp.route('/offer/<int:offer_id>/delete', methods=['POST'])
@login_required
def delete_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    # 1. Sprawdzenie uprawnień: Tylko właściciel lub administrator może usunąć ofertę
    if current_user.id != offer.donor_id and current_user.user_type != 'administrator':
        flash('Nie masz uprawnień do usunięcia tej oferty.', category='error')
        return redirect(url_for('main.dashboard'))

    try:
        # 2. Ręczne usuwanie powiązanych rekordów (jeśli nie masz ustawionego cascade w modelach)
        # Usuwamy wszystkie aplikacje przypisane do tej oferty
        for application in offer.applications:
            db.session.delete(application)

        # Usuwamy załączniki przypisane do oferty
        for attachment in offer.attachments:
            db.session.delete(attachment)

        # 3. Usunięcie samej oferty
        db.session.delete(offer)
        db.session.commit()

        flash('Oferta oraz wszystkie powiązane z nią zgłoszenia zostały usunięte.', category='success')
    except Exception as e:
        db.session.rollback()
        flash('Wystąpił błąd podczas usuwania oferty.', category='error')

    return redirect(url_for('main.dashboard'))

@main_bp.route('/worker/src/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    if current_user.user_type != 'worker':
        abort(403)

    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')

        db.session.commit()
        flash(f'Project: {project.title} has been updated.', category='success')
        return redirect(url_for('main.dashboard'))
    # if GET
    return render_template('edit_project.html', project=project)

@main_bp.route('/worker/src/<int:project_id>/finish', methods=['POST'])
@login_required
def finish_project(project_id):
    # Only workers can finish projects
    if current_user.user_type != 'worker':
        abort(403)

    project = Project.query.get_or_404(project_id)

    # Prevent double finish
    if project.status == 'finished':
        flash('Project is already finished.', category='info')
        return redirect(url_for('main.dashboard'))

    project.finish()
    db.session.commit()

    flash(f'Project "{project.title}" has been finished. All related offers were closed.',
          category='success')

    return redirect(url_for('main.dashboard'))



@main_bp.route('/worker/offer/<int:offer_id>/reject', methods=['POST'])
@login_required
def reject_offer(offer_id):
    # Permission Check: Only Workers can reject
    if current_user.user_type != 'worker':
        abort(403)

    offer = Offer.query.get_or_404(offer_id)

    # Delete the offer from the database permanently, this or changing the status
    db.session.delete(offer)
    db.session.commit()

    flash('Offer has been rejected and deleted.', category='info')
    return redirect(url_for('main.pending_offers'))


@main_bp.route('/profile')
@login_required
def profile():
    # Initialize empty lists to avoid errors if user type is unknown
    my_offers = []
    my_applications = []

    # Logic for Donors: Show offers created by them
    if current_user.user_type == 'donor':
        my_offers = Offer.query.filter_by(donor_id=current_user.id).order_by(Offer.date_created.desc()).all()

    # Logic for Beneficiaries: Show applications they have sent
    elif current_user.user_type == 'beneficient':
        my_applications = Application.query.filter_by(applicant_id=current_user.id).order_by(
            Application.date_created.desc()).all()

    # Pass both lists to the template. The frontend will decide which one to display based on user_type.
    return render_template('profile.html', my_offers=my_offers, my_applications=my_applications)


# --- ADMIN PANEL ---

@main_bp.route('/admin/create-worker', methods=['GET', 'POST'])
@login_required
def create_worker():
    # Only Administrator can create new worker accounts
    if current_user.user_type != 'administrator':
        abort(403)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        # Creating a new OrganizationWorker
        new_worker = OrganizationWorker(
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type='worker'
        )
        new_worker.set_password(password)

        db.session.add(new_worker)
        db.session.commit()

        flash('Worker account created successfully.', category='success')
        return redirect(url_for('main.index'))

    return render_template('create_worker.html')


# --- PROJECT MANAGEMENT ---
# Add view projectds
@main_bp.route('/worker/create-src', methods=['GET', 'POST'])
@login_required
def create_project():
    # Only Workers can create charity projects
    if current_user.user_type != 'worker':
        abort(403)

    if request.method == 'POST':
        title = request.form.get('title')
        desc = request.form.get('description')

        new_project = Project(
            title=title,
            description=desc,
            worker_id=current_user.id
        )
        db.session.add(new_project)
        db.session.commit()
        flash('Charity src created successfully.', category='success')
        return redirect(url_for('main.dashboard'))

    return redirect(url_for('main.dashboard'))


@main_bp.route('/rate/<int:app_id>', methods=['POST'])
@login_required
def rate_interaction(app_id):
    application = Application.query.get_or_404(app_id)
    score = request.form.get('score')  # 1-5
    comment = request.form.get('comment')

    # SCENARIO 1: Worker rates Donor (after process analysis)
    if current_user.user_type == 'worker':
        rating_type = 'donor_rating'

    # SCENARIO 2: Beneficiary fills survey (rates help received)
    elif current_user.user_type == 'beneficient' and application.applicant_id == current_user.id:
        rating_type = 'help_survey'
    else:
        flash('You do not have permission to rate.', category='error')
        return redirect(url_for('main.dashboard'))

    new_rating = Rating(
        score=score,
        comment=comment,
        rating_type=rating_type,
        rater_id=current_user.id,
        application_id=application.id
    )

    db.session.add(new_rating)
    db.session.commit()

    flash('Thank you for your feedback!', category='success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/send-inquiry', methods=['POST'])
def send_inquiry():
    title = request.form.get('name')  # używamy name jako tytuł zapytania
    message = request.form.get('question')

    # Jeśli user jest zalogowany, bierzemy jego ID, inaczej przypisujemy None lub specjalnego guest usera
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = 1

    # Tworzymy nowe zapytanie
    new_inquiry = Inquiry(
        title=title,
        message=message,
        user_id=user_id,
        created_at=datetime.utcnow()
    )

    db.session.add(new_inquiry)
    db.session.commit()

    flash(f'Thank you {title}, your inquiry has been sent to the organization!', category='success')
    return redirect(url_for('main.guest_dashboard'))

@main_bp.route('/guest')
def guest_dashboard():
    offers = Offer.query.filter_by(status='approved') \
        .order_by(Offer.date_created.desc()).all()

    projects = Project.query.filter(Project.status != 'active') \
        .order_by(Project.date_created.desc()).all()

    ratings = Rating.query.filter_by(rating_type='donor_rating') \
        .order_by(Rating.id.desc()).limit(10).all()

    return render_template(
        'guest_dashboard.html',
        offers=offers,
        projects=projects,
        ratings=ratings
    )
