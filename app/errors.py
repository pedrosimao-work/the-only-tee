from flask import current_app, render_template, request # Import Flask helpers for logging request errors and rendering error pages

from app.extensions import db # Import the database object so failed transactions can be rolled back on server errors


def register_error_handlers(app): # Define a function that registers app-level error handlers
    @app.errorhandler(403) # Register the 403 Forbidden error handler
    def forbidden(error): # Define the handler for forbidden requests
        current_app.logger.warning("403 Forbidden at %s: %s", request.path, error) # Log the forbidden request path and error
        return render_template("errors/403.html"), 403 # Render a user-safe forbidden page

    @app.errorhandler(404) # Register the 404 Not Found error handler
    def not_found(error): # Define the handler for missing pages
        current_app.logger.info("404 Not Found at %s: %s", request.path, error) # Log the missing path without treating it as a server failure
        return render_template("errors/404.html"), 404 # Render a user-safe not found page

    @app.errorhandler(500) # Register the 500 Internal Server Error handler
    def internal_server_error(error): # Define the handler for unexpected server errors
        db.session.rollback() # Roll back any failed database transaction before rendering the error page
        current_app.logger.exception("500 Internal Server Error at %s: %s", request.path, error) # Log the full stack trace for debugging
        return render_template("errors/500.html"), 500 # Render a user-safe server error page