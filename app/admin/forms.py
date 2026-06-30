from flask_wtf import FlaskForm  # Import FlaskForm as the base class for secure Flask forms
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField  # Import form field types for drop management
from wtforms.validators import DataRequired, Length, NumberRange, Optional  # Import reusable form validation rules

from app.constants import VALID_DROP_STATUSES  # Import the allowed drop statuses for the status select field


class DropForm(FlaskForm):  # Create a form class for creating new drop records
    drop_number = StringField(  # Create the drop number input field
        "Drop Number",  # Set the human-readable label for the drop number field
        validators=[DataRequired(), Length(min=4, max=10)],  # Require the field and enforce a sensible lenght
    )  # Close the season field definition

    season = IntegerField(  # Create the season number input field
        "Season",  # Set the human-readable label for the season field
        validators=[DataRequired(), NumberRange(min=1)],  # Require the field and only allow positive season numbers
    )  # Close the season field definition

    name = StringField(  # Create the drop name input field
        "Name",  # Set the human-readable label for the name field
        validators=[DataRequired(), Length(min=3, max=120)],  # Require the field and enforce length limits
    )  # Close the name field definitio

    description = TextAreaField(  # Create the drop description textarea field
        "Description",  # Set the human-readable label for the description field
        validators=[DataRequired(), Length(min=10)]  # Require the field and enforce a useful minimum length
    )  # Close the description field definition

    price = IntegerField(  # Create the price input field
        "Price",  # Set the human-readable label for the price field
        validators=[DataRequired(), NumberRange(min=1)]  # Require the field and only allow positive prices
    )  # Close the price field definition

    status = SelectField(  # Create the status dropdown field
        "Status",  # Set the human-readable label for the status field
        choices=[(status, status.capitalize()) for status in VALID_DROP_STATUSES],  # Build dropdown choices from valid statuses
        validators=[DataRequired()],  # Require one valid status selection
    )  # Close the status field definition

    image_url = StringField(  # Create the optional image URL input field
        "Image URL",  # Set the human-readable label for the image URL field
        validators=[Optional(), Length(max=255)],  # Allow the field to be empty but limit length when filled
    )  # Close the image URL field definition

    submit = SubmitField("Create Drop")  # Create the submit button for the create-dropform