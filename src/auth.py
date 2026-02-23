from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from . import db
from .models import User, Donor, Beneficient, Administrator, OrganizationWorker

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return redirect(url_for('main.index'))

    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        """if not user.is_approved:
            flash("Your account is waiting for authentication from our worker.", category='error')
            return redirect(url_for('main.index'))"""
        login_user(user)

        if user.user_type == "administrator":
            return redirect(url_for('main.dashboard')) #  'main.admin_panel'
        elif user.user_type == "worker":
            return redirect(url_for('main.dashboard')) #  'main.worker_panel'
        else:
            # Beneficient and Donor
            return redirect(url_for('main.dashboard'))

    flash('Niepoprawny email lub hasło.', category='error')

    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') #donor, beneficient
        fname = request.form.get('first_name')
        lname = request.form.get('last_name')

        if User.query.filter_by(email=email).first():
            flash('E-mail jest już zajęty.', category='error')
            return redirect(url_for('main.index'))

        new_user = None
        if role == 'donor':
            new_user = Donor(email=email, first_name=fname, last_name=lname)
        elif role == 'beneficient':
            new_user = Beneficient(email=email, first_name=fname, last_name=lname)

        if new_user:
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Konto zostało utworzone.", category='success')
            return redirect(url_for('main.index'))

    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Zostałeś wylogowany.", category='success')
    return redirect(url_for('main.index'))