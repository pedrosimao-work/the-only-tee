import json  # Import json so drop mockup image URL's can be stored and read as JSON text
from datetime import datetime  # Import datetime so we can store creation and lifecycle dates

from flask_login import UserMixin  # Import UserMixin to provide default Flask-Login user methods
from werkzeug.security import check_password_hash, generate_password_hash  # Import secure password hashing helpers

from app.constants import DEFAULT_SHIRT_COLOR, DROP_PRODUCT_TYPE_TSHIRT, DROP_STATUS_DRAFT  # Import default drop constants
from app.extensions import db, login_manager  # Import the shared SQLAlchemy database object
from app.validators import validate_drop_status, validate_product_type  # Import the reusable drop validation functions


class User(UserMixin, db.Model):  # Create a database model class representing one registered user
    id = db.Column(db.Integer, primary_key=True)  # Create the primary key column for each user record
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)  # Store the user's unique email address
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)  # Store the user's unique public username
    password_hash = db.Column(db.String(255), nullable=False)  # Store the hashed password, never the plain password
    is_admin = db.Column(db.Boolean, nullable=False, default=False)  # Store whether the user has admin permissions
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Storewhen the user account was created

    def set_password(self, password):  # Define a method for securely storing a new password
        self.password_hash = generate_password_hash(password)  # Hash the plain password and store only the hash

    def check_password(self, password):  # Define a method for checking a login password
        return check_password_hash(self.password_hash, password)  # Compare the submitted password against the stored hash

    def __repr__(self):  # Define the developer-friendly representation of a User object
        return f"<User {self.username}>"  # Return a readable label when debugging User records


@login_manager.user_loader  # Register the function Flask-Login uses to reload a user from the session
def load_user(user_id):  # Define the user loading function that receives the stored user ID
    return User.query.get(int(user_id))  # Return the User record matching the session user


class Drop(db.Model):  # Create a database model class representing one limited T-shirt drop
    id = db.Column(db.Integer, primary_key=True)  # Create the primary key column for each drop record
    drop_number = db.Column(db.String(10), nullable=False, unique=True)  # Store the public drop number, such as 0001
    season = db.Column(db.Integer, nullable=False, default=1)  # Store the season number for collection organization
    name = db.Column(db.String(120), nullable=False)  # Store the public name of the drop
    description = db.Column(db.Text, nullable=False)  # Store the longer description of the drop
    price = db.Column(db.Integer, nullable=False, default=59)  # Store the price in euros as a simple integer for now
    status = db.Column(db.String(20), nullable=False, default=DROP_STATUS_DRAFT)  # Store the lifecycle status using the default constant
    product_type = db.Column(db.String(50), nullable=False, default=DROP_PRODUCT_TYPE_TSHIRT, server_default=DROP_PRODUCT_TYPE_TSHIRT)  # Store the product type for this monthly drop
    shirt_color = db.Column(db.String(80), nullable=False, default=DEFAULT_SHIRT_COLOR, server_default=DEFAULT_SHIRT_COLOR)  # Store the selected shirt color for this design
    image_url = db.Column(db.String(255), nullable=True)  # Store an optional product image URL for future Printify or uploaded images
    mockup_image_urls = db.Column(db.Text, nullable=True)  # Store multiple Printify mockup image URLs as JSON text
    printify_product_id = db.Column(db.String(120), nullable=True)  # Store the Printify product ID connected to this drop
    printify_variant_ids = db.Column(db.Text, nullable=True)  # Store selected Printify variant IDs for available sizes as text for future parsing
    stripe_product_id = db.Column(db.String(120), nullable=True)  # Store the Stripe product ID connected to this drop
    stripe_price_id = db.Column(db.String(120), nullable=True)  # Store the Stripe price ID used for hosted Checkout
    instagram_media_id = db.Column(db.String(120), nullable=True)  # Store the Instagram media ID after publishing a launch reel
    instagram_permalink = db.Column(db.String(255), nullable=True)  # Store the Instagram post permalink after publishing
    starts_at = db.Column(db.DateTime, nullable= True)  # Store when the drop becomes active
    ends_at = db.Column(db.DateTime, nullable=True)  # Store when the drop expires
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Store when the database record was created
    archived_at = db.Column(db.DateTime, nullable=True)  # Store when the drop entered the archive collection

    def __init__(self, **kwargs):  # Define custom initialization logic for new Drop objects
        super().__init__(**kwargs)  # Let SQLAlchemy assign the provided fields normally first
        validate_drop_status(self.status)  # Validate the drop status immediately after object creation
        validate_product_type(self.product_type)  # Validate the product type immediately after object creation


    def get_mockup_images(self):  # Define a helper method that returns all usable mockup image URLs
        if self.mockup_image_urls:  # Check if the drop has a stored JSON list of mockup images
            try:  # Start a protected block in case the stored JSON text is invalid
                images = json.loads(self.mockup_image_urls)  # Convert the stored JSON text into a Python list
            except json.JSONDecodeError:  # Catch invalid JSON data safely
                images = []  # Use an empty list if the stored JSON cannot be decoded

            if images:  # Check if the decoded image list contains URLs
                return images  # Return the stored mockup image URLs

        if self.image_url:  # Check if the drop has one fallback image URL
            return [self.image_url]  # Return a single image URL inside a list

        return []  # Return an empty list when the drop has no mockup images


    def __repr__(self):  # Define the developer-friendly representation of a Drop object
        return f"<Drop #{self.drop_number} - {self.name}>"  # Return a readable lable when debugging Drop records