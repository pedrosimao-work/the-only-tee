from flask_wtf import FlaskForm # Import FlaskForm as the base class for protected forms
from wtforms import DateTimeLocalField, DecimalField, HiddenField, IntegerField, SelectField, StringField, SubmitField, TextAreaField # Import WTForms fields used by admin forms
from wtforms.validators import DataRequired, Length, NumberRange, Optional # Import validators used by admin forms


class DropForm(FlaskForm): # Define the admin form used to create and edit drops
    drop_number = StringField("Drop Number", validators=[DataRequired(), Length(min=4, max=4)]) # Store the public drop number
    season = IntegerField("Season", validators=[DataRequired(), NumberRange(min=1)]) # Store the season number
    name = StringField("Name", validators=[DataRequired(), Length(max=120)]) # Store the manual drop name
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=1000)]) # Store the manual public drop description
    price = DecimalField("Price in USD", validators=[DataRequired(), NumberRange(min=1)], places=2) # Store the USD drop price
    status = SelectField("Status", choices=[("draft", "Draft"), ("active", "Active"), ("archived", "Archived")], validators=[DataRequired()]) # Store the drop lifecycle status
    product_type = SelectField("Product Type", choices=[("t-shirt", "T-Shirt")], validators=[DataRequired()]) # Store the product type
    shirt_color = StringField("Shirt Color", validators=[DataRequired(), Length(max=40)]) # Store the fixed shirt color
    starts_at = DateTimeLocalField("Starts At", format="%Y-%m-%dT%H:%M", validators=[Optional()]) # Store the optional drop start date and time
    ends_at = DateTimeLocalField("Ends At", format="%Y-%m-%dT%H:%M", validators=[Optional()]) # Store the optional drop end date and time
    printify_product_id = HiddenField("Printify Product", validators=[Optional(), Length(max=120)]) # Store the selected Printify product ID from the visual picker
    submit = SubmitField("Save Drop") # Submit the admin drop form


class EmptyForm(FlaskForm): # Define an empty CSRF-protected form for button-only POST actions
    submit = SubmitField("Submit") # Provide a generic submit field for protected POST buttons