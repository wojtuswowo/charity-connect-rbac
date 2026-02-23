from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

load_dotenv()


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Password to our database
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    # Needs to be done
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    # Not to have errors and for memory save
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # User class needs to be implemented
    from .models import User

    # Loading user
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # auth needs to be implemented
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main import main_bp
    app.register_blueprint(main_bp)

    return app




