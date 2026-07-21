import os  # Import the os module to read environment variables from the operating system


def build_database_uri():  # Define a helper function that builds the database connection URI
    database_url = os.environ.get("DATABASE_URL")  # Read the DATABASE_URL value from the environment

    if not database_url:  # Check if no production database URL was provided
        return "sqlite:///the_only_drop.db"  # Use a local SQLite database for development

    if database_url.startswith("mysql://"):  # Check of if the database URL uses the generic MySQL scheme
        return database_url.replace("mysql://", "mysql+pymysql://", 1)  # Convert it to the PyMySQL SQLAlchemy driver format

    return database_url  # Return the provided database URL unchanged when it already uses a supported format


class Config:  # Create a base configuration class for the Flask application
    SECRET_KEY = os.getenv("SECRET_KEY", "temporary-development-key")  # Read the secret key from the environment or use a local fallback
    SQLALCHEMY_DATABASE_URI = build_database_uri()  # Configure SQLAlchemy from DATABASE_URL or SQLite fallback
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable unnecessary SQLAlchemy modification tracking to improve performance
    SQLALCHEMY_ENGINE_OPTIONS = {  # Configure database engine behavior for more reliable production connections
        "pool_pre_ping": True,  # Check database connections before using them to avoid stale connection errors
        "pool_recycle": 280,  # Recycle database connections before shared-hosting timeouts commonly close them
    }  # Close the SQLAlchemy engine options dictionary
    