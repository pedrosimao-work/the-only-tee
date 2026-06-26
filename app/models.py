from datetime import datetime  # Import datetime so we can store creation and lifecycle dates

from app.constants import DROP_STATUS_DRAFT  # Import the default draft status constant
from app.extensions import db  # Import the shared SQLAlchemy database object
from app.validators import validate_drop_status  # Import the reusable drop status validation function


class Drop(db.Model):  # Create a database model class representing one limited T-shirt drop
    id = db.Column(db.Integer, primary_key=True)  # Create the primary key column for each drop record
    drop_number = db.Column(db.String(10), nullable=False, unique=True)  # Store the public drop number, such as 0001
    season = db.Column(db.Integer, nullable=False, default=1)  # Store the season number for collection organization
    name = db.Column(db.String(120), nullable=False)  # Store the public name of the drop
    description = db.Column(db.Text, nullable=False)  # Store the longer description of the drop
    price = db.Column(db.Integer, nullable=False, default=59)  # Store the price in euros as a simple integer for now
    status = db.Column(db.String(20), nullable=False, default="draft")  # Store the lifecycle status, such as draft, active, or archived
    image_url = db.Column(db.String(255), nullable=True)  # Store an optional product image URL for future Printify or uploaded images
    starts_at = db.Column(db.DateTime, nullable= True)  # Store when the drop becomes active
    ends_at = db.Column(db.DateTime, nullable=True)  # Store when the drop expires
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Store when the database record was created
    archived_at = db.Column(db.DateTime, nullable=True)  # Store when the drop entered the archive collection

    def __init__(self, **kwargs):  # Define custom initialization logic for new Drop objects
        super().__init__(**kwargs)  # Let SQLAlchemy assign the provided fields normally first
        validate_drop_status(self.status)  # Validate the drop status immediately after object creation

    def __repr__(self):  # Define the developer-friendly representation of a Drop object
        return f"<Drop #{self.drop_number} - {self.name}>"  # Return a readable lable when debugging Drop records