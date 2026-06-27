from flask import Flask  # Import the Flask class used to create the web application
from flask_migrate import Migrate  # Import Flask-Migrate to manage database migrations

from app.config import Config  # Import the main configuration class
from app.extensions import db, login_manager  # Import the shared SQLAlchemy database object


migrate = Migrate()  # Create the migration extension object without binding it to the app yet


def create_app():  # Define the application factory function used to build and configure the Flask app
    app = Flask(__name__)  # Create a new Flask application instance using the current package name

    app.config.from_object(Config)  # Load configuration values from the Config class

    db.init_app(app)  # Connect the SQLAlchemy database extension to this Flask app
    migrate.init_app(app, db)  # Connect Flask-Migrate to this Flask app and database object
    login_manager.init_app(app)  # Connect Flask-Login to this Flask app

    login_manager.login_view = "auth.login"  # Redirect unauthenticated users to the login page when needed
    login_manager.login_message = "Please log in to access this page."  # Set the message shown when login is required
    login_manager.login_message_category = "warning"  # Set the Boostrap-style category for the Login-required message

    from app import models  # Import models so Flask-Migrate can detect database tables

    from app.commands import register_commands  # Import the function that registers custom Flask CLI commands

    register_commands(app)  # Register custom terminal commands on the Flask app

    from app.auth.routes import auth  # Import the authentication bluepring after the app is configured
    from app.routes import main  # Import the main routes blueprint after creating the app to avoid circular imports

    app.register_blueprint(main)  # Register the main blueprint so its routes become available in the app
    app.register_blueprint(auth)  # Register the authentication blueprint

    return app  # Return the fully configured Flask application instance