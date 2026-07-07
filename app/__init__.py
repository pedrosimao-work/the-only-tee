from flask import Flask  # Import the Flask class used to create the web application
from flask_migrate import Migrate  # Import Flask-Migrate to manage database migrations

from app.config import Config  # Import the main configuration class
from app.constants import BRAND_NAME, BRAND_NAME_UPPER, BRAND_TAGLINE, DROP_CADENCE_LABEL, PRIMARY_DOMAIN, PRODUCT_CATEGORY_PLURAL, PRODUCT_CATEGORY_SINGULAR  # Import brand constants used globally in templates
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

    @app.context_processor  # Register a function that injects shared variables into all templates
    def inject_brand_context():  # Define the template context function for brand values
        return {  # Return a dictionary of values available in every Jinja template
            "BRAND_NAME": BRAND_NAME,  # Make the public brand name available to templates
            "BRAND_NAME_UPPER": BRAND_NAME_UPPER,  # Make the uppercase brand name available to templates
            "BRAND_TAGLINE": BRAND_TAGLINE,  # Make the brand tagline available to templates
            "DROP_CADENCE_LABEL": DROP_CADENCE_LABEL,  # Make the monthly cadence label available to templates
            "PRIMARY_DOMAIN": PRIMARY_DOMAIN,  # Make the planned domain available to templates
            "PRODUCT_CATEGORY_SINGULAR": PRODUCT_CATEGORY_SINGULAR,  # Make the singular product category available to templates
            "PRODUCT_CATEGORY_PLURAL": PRODUCT_CATEGORY_PLURAL,  # Make the plural product category available to templates
        }  # Close the template context dictionary

    from app import models  # Import models so Flask-Migrate can detect database tables

    from app.commands import register_commands  # Import the function that registers custom Flask CLI commands

    register_commands(app)  # Register custom terminal commands on the Flask app

    from app.admin.routes import admin  # Import the admin blueprint after the app is configured
    from app.auth.routes import auth  # Import the authentication blueprint after the app is configured
    from app.routes import main  # Import the main routes blueprint after creating the app to avoid circular imports

    app.register_blueprint(main)  # Register the main blueprint so its routes become available in the app
    app.register_blueprint(auth)  # Register the authentication blueprint
    app.register_blueprint(admin)  # Register the admin blueprint

    return app  # Return the fully configured Flask application instance