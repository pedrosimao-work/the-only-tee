from flask_wtf import FlaskForm  # Import FlaskForm as the base class for secure Flask forms
from wtforms import DateTimeLocalField, DecimalField, IntegerField, SelectField, StringField, SubmitField, TextAreaField  # Import form field types for drop management
from wtforms.validators import DataRequired, Length, NumberRange, Optional  # Import reusable form validation rules

from app.constants import VALID_DROP_STATUSES, VALID_PRODUCT_TYPES  # Import the allowed statuses and product types


class DropForm(FlaskForm):  # Create a form class for creating and editing drop records
    drop_number = StringField(  # Create the drop number input field
        "Drop Number",  # Set the human-readable label for the drop number field
        validators=[DataRequired(), Length(min=4, max=10)],  # Require the field and enforce sensible length limits
    )  # Close the drop number field definition

    season = IntegerField(  # Create the season number input field
        "Season",  # Set the human-readable label for the season field
        validators=[DataRequired(), NumberRange(min=1)],  # Require the field and only allow positive season numbers
    )  # Close the season field definition

    name = StringField(  # Create the drop name input field
        "Name",  # Set the human-readable label for the name field
        validators=[DataRequired(), Length(min=3, max=120)],  # Require the field and enforce length limits
    )  # Close the name field definition

    description = TextAreaField(  # Create the drop description textarea field
        "Description",  # Set the human-readable label for the description field
        validators=[DataRequired(), Length(min=10, max=1000)],  # Require the field and enforce useful length limits
    )  # Close the description field definition

    price = DecimalField(  # Create the USD price input field
        "Price in USD",  # Set the human-readable label for the price field
        validators=[DataRequired(), NumberRange(min=1)],  # Require the field and only allow positive prices
        places=2,  # Keep prices to two decimal places
    )  # Close the price field definition

    status = SelectField(  # Create the status dropdown field
        "Status",  # Set the human-readable label for the status field
        choices=[(status, status.capitalize()) for status in VALID_DROP_STATUSES],  # Build dropdown choices from valid statuses
        validators=[DataRequired()],  # Require one valid status selection
    )  # Close the status field definition

    product_type = SelectField(  # Create the product type dropdown field
        "Product Type",  # Set the human-readable label for the product type field
        choices=[(product_type, product_type.title()) for product_type in VALID_PRODUCT_TYPES],  # Build dropdown choices from valid product types
        validators=[DataRequired()],  # Require one valid product type selection
    )  # Close the product type field definition

    shirt_color = StringField(  # Create the selected shirt color input field
        "Shirt Color",  # Set the human-readable label for the shirt color field
        validators=[DataRequired(), Length(min=2, max=80)],  # Require shirt color and enforce length limits
    )  # Close the shirt color field definition

    starts_at = DateTimeLocalField(  # Create the optional drop start datetime field
        "Starts At",  # Set the human-readable label for the start datetime field
        format="%Y-%m-%dT%H:%M",  # Match the HTML datetime-local input format
        validators=[Optional()],  # Allow admins to leave the start date empty for unscheduled drafts
    )  # Close the start datetime field definition

    ends_at = DateTimeLocalField(  # Create the optional drop end datetime field
        "Ends At",  # Set the human-readable label for the end datetime field
        format="%Y-%m-%dT%H:%M",  # Match the HTML datetime-local input format
        validators=[Optional()],  # Allow admins to leave the end date empty if it should be calculated later
    )  # Close the end datetime field definition

    printify_product_id = StringField(  # Create the optional Printify product ID input field
        "Printify Product ID",  # Set the human-readable label for the Printify Product ID field
        validators=[Optional(), Length(max=120)],  # Allow the field to be empty but limit length when filled
    )  # Close the Printify product ID field definition

    printify_variant_ids = TextAreaField(  # Create the optional Printify variant IDs textarea field
        "Printify Variant IDs",  # Set the human-readable label for the Printify variant IDs field
        validators=[Optional(), Length(max=1000)],  # Allow the field to be empty but limit stored text length
    )  # Close the Printify variant IDs field definition

    submit = SubmitField("Save Drop")  # Create the submit button for the drop form


class EmptyForm(FlaskForm):  # Create a minimal CSRF-protected form for button-only POST actions
    submit = SubmitField("Submit")  # Create a generic submit button field