import json  # Import json so drop mockup image URL's can be stored and read as JSON text
from datetime import datetime  # Import datetime so we can store creation and lifecycle dates

from flask_login import UserMixin  # Import UserMixin to provide default Flask-Login user methods
from werkzeug.security import check_password_hash, generate_password_hash  # Import secure password hashing helpers

from app.constants import DROP_SIZE_ORDER, DEFAULT_SHIRT_COLOR, DROP_PRODUCT_TYPE_TSHIRT, DROP_STATUS_DRAFT  # Import default drop constants
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
    printify_size_variant_map = db.Column(db.Text, nullable=True)  # Store a JSON map connecting customer sizes to Printify variant IDs
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


    def get_size_variant_map(self):  # Define a helper method that returns the stored size-to-variant map
        if not self.printify_size_variant_map:  # Check if no size map has been stored yet
            return {}  # Return an empty dictionary when there is no size map

        try:  # Start a protected block in case the stored JSON is invalid
            size_variant_map = json.loads(self.printify_size_variant_map)  # Convert the stored JSON text into a Python dictionary
        except json.JSONDecodeError:  # Catch invalid JSON safely
            return {}  # Return an empty dictionary if the JSON cannot be decoded

        if not isinstance(size_variant_map, dict):  # Check if the decoded value is not a dictionary
            return {}  # Return an empty dictionary because the size map format is invalid

        return size_variant_map  # Return the valid size-to-variant map

    def get_available_sizes(self):  # Define a helper method that returns available sizes in storefront order
        size_variant_map = self.get_size_variant_map()  # Read the stored size-to-variant map

        ordered_sizes = [size for size in DROP_SIZE_ORDER if size in size_variant_map]  # Keep known sizes in the preferred order
        extra_sizes = sorted(size for size in size_variant_map if size not in DROP_SIZE_ORDER)  # Sort any unexpected extra sizes alphabetically

        return ordered_sizes + extra_sizes  # Return known sizes first, then any extra sizes

    def get_printify_variant_id_for_size(self, selected_size):  # Define a helper method that returns the Printify variant ID for one size
        size_variant_map = self.get_size_variant_map()  # Read the stored size-to-variant map
        return size_variant_map.get(selected_size)  # Return the matching Printify variant ID or None


    def __repr__(self):  # Define the developer-friendly representation of a Drop object
        return f"<Drop #{self.drop_number} - {self.name}>"  # Return a readable lable when debugging Drop records


class Order(db.Model):  # Create a database model class representing one Stripe checkout order
    id = db.Column(db.Integer, primary_key=True)  # Create the primary key column for each order record
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # Store the user ID if the customer is logged in
    drop_id = db.Column(db.Integer, db.ForeignKey("drop.id"), nullable=False)  # Store the purchased drop ID
    stripe_checkout_session_id = db.Column(db.String(255), nullable=False, unique=True, index=True)  # Store the Stripe Checkout Session ID
    stripe_payment_intent_id = db.Column(db.String(255), nullable=True, index=True)  # Store the Stripe PaymentIntent ID after payment completion
    payment_status = db.Column(db.String(50), nullable=False, default="created")  # Store the payment status returned by Stripe
    customer_email = db.Column(db.String(255), nullable=True)  # Store the customer email returned by Stripe Checkout
    selected_size = db.Column(db.String(20), nullable=True)  # Store the customer-selected shirt size for fulfillment
    printify_variant_id = db.Column(db.String(120), nullable=True)  # Store the Printify variant ID connected to the selected size
    quantity = db.Column(db.Integer, nullable=False, default=1)  # Store the purchased quantity
    amount_total = db.Column(db.Integer, nullable=True)  # Store the total paid amount in the smallest currency unit
    currency = db.Column(db.String(10), nullable=True)  # Store the Stripe currency code
    printify_order_id = db.Column(db.String(120), nullable=True)  # Store the future Printify order ID after fulfillment
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Store when the local order was created
    paid_at = db.Column(db.DateTime, nullable=True)  # Store when Stripe confirmed payment completion

    user = db.relationship("User", backref="orders")  # Connect the order to the option user record
    drop = db.relationship("Drop", backref="orders")  # Connect the order to the purchased drop record

    def get_amount_display(self):  # Define a helper method that formats the Stripe amount for admin display
        if self.amount_total is None:  # Check if Stripe did not return an amount yet
            return "Not available"  # Return a safe fallback when the amount is missing

        if not self.currency:  # Check if Stripe did not return a currency yet
            return "Not available"  # Return safe fallback when the currency is missing

        amount = self.amount_total / 100  # Convert Stripe's smallest currency unit into normal currency units
        return f"{self.currency.upper()} {amount:.2f}"  # Return the formatted amount with the currency code

    def get_fulfillment_status_label(self):  # Define a helper method that explains fulfillment readiness
        if self.printify_order_id:  # Check if the order has already been sent to Printify
            return "Sent to Printify"  # Return the completed fulfillment label

        if self.payment_status == "paid" and self.printify_variant_id:  # Check if the order is paid and has a fulfillment variant
            return "Ready for fulfillment"  # Return the ready-for-Printify label

        if self.payment_status == "paid":  # Check if the order is paid but missing fulfillment data
            return "Paid, missing variant"  # Return a warning label for incomplete fulfillment data

        return "Waiting for payment"  # Return the default label for unpaid or incomplete orders

    def is_ready_for_fulfillment(self):  # Define a helper method that returns whether this order can be fulfilled
        return self.payment_status == "paid" and bool(self.printify_variant_id) and not self.printify_order_id  # Return True only when the paid order has a variant and has not been sent to Printify

    def __repr__(self):  # Define the developer-friendly representation of an Order object
        return f"<Order {self.id} - {self.payment_status}>"  # Return a readable label when debugging Order records