import os  # Import the os module to read environment variables from the operating system


class Config:  # Create a base configuration class for the Flask application
    SECRET_KEY = os.getenv("SECRET_KEY", "temporary-development-key")  # Read the secret key from the environment or use a local fallback
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///the_only_tee.db")  # Read the database URL or use local SQlite
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable unnecessary SQLAlchemy modification tracking to improve performance
    