import logging # Import Python's standard logging module
from logging.handlers import RotatingFileHandler # Import rotating file handler so logs do not grow forever
from pathlib import Path # Import Path so log directories can be created safely


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s" # Define the standard log message format
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S" # Define the standard log date format


def get_log_level(app): # Define a helper that reads the configured log level
    log_level_name = app.config.get("LOG_LEVEL", "INFO") # Read LOG_LEVEL from app config with INFO as fallback
    return getattr(logging, str(log_level_name).upper(), logging.INFO) # Convert the configured level name into a logging level value


def build_formatter(): # Define a helper that creates the shared log formatter
    return logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT) # Return a formatter using the project log format and date format


def configure_logger_handlers(logger, formatter, log_level): # Define a helper that updates handlers on one logger
    for handler in logger.handlers: # Loop through handlers already attached to this logger
        handler.setLevel(log_level) # Apply the configured log level to this handler
        handler.setFormatter(formatter) # Apply the shared formatter to this handler


def has_file_handler(logger, log_file_path): # Define a helper that prevents duplicate file handlers in debug reloads
    for handler in logger.handlers: # Loop through handlers already attached to the logger
        if isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == log_file_path: # Check if this exact log file handler already exists
            return True # Signal that the file handler is already configured

    return False # Signal that the file handler is not configured yet


def has_console_handler(logger): # Define a helper that prevents duplicate console handlers
    for handler in logger.handlers: # Loop through handlers already attached to the logger
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler): # Check for a console stream handler but not a file handler
            return True # Signal that a console handler already exists

    return False # Signal that no console handler exists yet


def add_file_handler(logger, log_file_path, formatter, log_level): # Define a helper that adds a rotating file handler to one logger
    if has_file_handler(logger, log_file_path): # Check if this file handler was already added
        return # Stop to avoid duplicate log lines

    file_handler = RotatingFileHandler(log_file_path, maxBytes=1_000_000, backupCount=5) # Create a rotating file handler with five backups
    file_handler.setLevel(log_level) # Apply the configured log level to the file handler
    file_handler.setFormatter(formatter) # Apply the shared formatter to the file handler
    logger.addHandler(file_handler) # Attach the file handler to the selected logger


def add_console_handler(logger, formatter, log_level): # Define a helper that adds a console log handler
    if has_console_handler(logger): # Check if a console handler already exists
        return # Stop to avoid duplicate terminal log lines

    console_handler = logging.StreamHandler() # Create a console handler so logs are printed in the terminal
    console_handler.setLevel(log_level) # Apply the configured log level to the console handler
    console_handler.setFormatter(formatter) # Apply the shared formatter to the console handler
    logger.addHandler(console_handler) # Attach the console handler to the selected logger


def configure_root_logger(formatter, log_level, log_file_path, log_to_file): # Define a helper that configures module-level service loggers
    root_logger = logging.getLogger() # Get the root logger used by module loggers
    root_logger.setLevel(log_level) # Apply the configured log level to the root logger
    configure_logger_handlers(root_logger, formatter, log_level) # Update existing root handlers
    add_console_handler(root_logger, formatter, log_level) # Add terminal logging so Werkzeug startup/request lines stay visible

    if log_to_file: # Check if file logging is enabled
        add_file_handler(root_logger, log_file_path, formatter, log_level) # Add file logging for module-level service loggers


def configure_werkzeug_logger(formatter, log_level): # Define a helper that keeps Flask development server logs visible only in the terminal
    werkzeug_logger = logging.getLogger("werkzeug") # Get Werkzeug's development server logger
    werkzeug_logger.setLevel(log_level) # Keep Flask development server startup and request logs visible
    werkzeug_logger.propagate = False # Prevent Werkzeug development server logs from being written through the root file handler
    configure_logger_handlers(werkzeug_logger, formatter, log_level) # Update existing Werkzeug handlers
    add_console_handler(werkzeug_logger, formatter, log_level) # Add terminal logging for Werkzeug if it has no console handler


def configure_app_logger(app, formatter, log_level, log_file_path, log_to_file): # Define a helper that configures Flask's app logger
    app.logger.setLevel(log_level) # Apply the configured level to the Flask app logger
    app.logger.propagate = False # Prevent app logger records from being duplicated through the root logger
    configure_logger_handlers(app.logger, formatter, log_level) # Update Flask's existing handlers

    if log_to_file: # Check if file logging is enabled
        add_file_handler(app.logger, log_file_path, formatter, log_level) # Add file logging for Flask app logger records


def configure_logging(app): # Define the main logging setup function called from the app factory
    log_level = get_log_level(app) # Resolve the configured log level
    formatter = build_formatter() # Build the shared log formatter
    logs_directory = Path(app.instance_path) / "logs" # Build the instance logs directory path
    logs_directory.mkdir(parents=True, exist_ok=True) # Create the logs directory if it does not exist
    log_file_path = logs_directory / "the_only_drop.log" # Build the main application log file path
    log_to_file = app.config.get("LOG_TO_FILE", True) # Read whether file logging is enabled

    configure_root_logger(formatter, log_level, log_file_path, log_to_file) # Configure service/module loggers
    configure_werkzeug_logger(formatter, log_level) # Keep Flask development server logs visible in the terminal only
    configure_app_logger(app, formatter, log_level, log_file_path, log_to_file) # Configure Flask app logger

    app.logger.info("Logging configured with level %s.", logging.getLevelName(log_level)) # Log that application logging was configured