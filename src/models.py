
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password_hash = db.Column(db.String, nullable = False)
    first_name = db.Column(db.String(60), nullable = False)
    last_name = db.Column(db.String(60), nullable=False)
    user_type = db.Column(db.String)
    is_approved = db.Column(db.Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity' : 'user',
        'polymorphic_on' : user_type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Administrator(User):
    __mapper_args__ = {'polymorphic_identity' : 'administrator'}

class OrganizationWorker(User):
    __mapper_args__ = {'polymorphic_identity' : 'worker'}
    # extra atributes - to be done
class Donor(User):
    __mapper_args__ = {'polymorphic_identity' : 'donor'}
    # extra atributes - to be done
class Beneficient(User):
    __mapper_args__ = {'polymorphic_identity' : 'beneficient'}
    # extra atributes - to be done

# to be implemented - Offer, Project, Application, Inquiry.......
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(db.String(20), default='active')  # active / finished
    date_finished = db.Column(db.DateTime, nullable=True)

    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    worker = db.relationship('User', backref='managed_projects')

    def finish(self):
        self.status = 'finished'
        self.date_finished = datetime.utcnow()

        # Close all related offers
        for offer in self.offers:
            offer.status = 'closed'


class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    rating_type = db.Column(db.String(20))  # 'donor_rating' lub 'help_survey'

    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))

    application = db.relationship('Application', backref='ratings')

class Offer(db.Model):
    __tablename__ = 'offers'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    offer_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String, default='pending')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    # Foreign key
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Making a relationship between donor and an offer, so we can easily get informations,
    # Enables for example:
    # my_offers = current_user.offers instead of Offer.query.filter_by(donor_id=current_user.id).all()
    donor = db.relationship('User', backref='offers')

    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    project = db.relationship('Project', backref='offers')

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Who is sending an application
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # What is the application for
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False)
    # So we can use offer.applications
    # add donor id
    offer = db.relationship('Offer', backref='applications')
    # So we can show all user's applications
    applicant = db.relationship('User', backref='my_applications')


class Attachment(db.Model):
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

    # Powiązanie z ofertą (zgodnie z IO)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False)
    offer = db.relationship('Offer', backref='attachments')


class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Kto pyta? (User)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='inquiries')
