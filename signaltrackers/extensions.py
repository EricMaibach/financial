"""
Flask Extension Instances

Centralized extension instances for the application.
These are initialized without an app and bound later via init_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

# Database
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# CSRF protection
csrf = CSRFProtect()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['100 per minute']
)

# Email
mail = Mail()


def init_extensions(app):
    """Initialize all extensions with the Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # User loader for Flask-Login
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
