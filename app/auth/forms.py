from flask_wtf import FlaskForm  # Import FlaskForm as the base class for secure Flask forms
from wtforms import EmailField, PasswordField, StringField, SubmitField  # Import form field types used by auth forms
from wtforms.validators import DataRequired, Email, EqualTo, Length  # Import reusable form validation rules


class RegisterForm(FlaskForm):  # Create the registration form class
    email = EmailField(  # Create the email input field
        "Email",  # Set the human-readable label for the email field
        validators=[DataRequired(), Email(), Length(max=120)],  # Require email, validate format, and limit length
    )  # Close the email field definition
    username = StringField(  # Create the username input field
        "Username",  # Set the human-readable label for the username field
        validators=[DataRequired(), Length(min=3, max=80)],  # Require username and enforce length limits
    )  # Close the username field definition
    password = PasswordField(  # Create the password input field
        "Password",  # Set the human-readable label for the password field
        validators=[DataRequired(), Length(min=6)],  # Require password and enforce a minimum length
    )  # Close the password field definition
    confirm_password = PasswordField(  # Create the confirm password input field
        "Confirm Password",  # Set the human-readable label for the confirm password field
        validators=[DataRequired(), EqualTo("password")],  # Require confirmation and make it match the password field
    )  # Close the confirm password field definition
    submit = SubmitField("Create Account")  # Create the submit button for the registration form


class LoginForm(FlaskForm):  # Create the Login form class
    email = EmailField(  # Create the email input field
        "Email",  # Set the human-readable label for the email field
        validators=[DataRequired(), Email(), Length(max=120)],  # Require email, validate format, and limit length
    )  # Close the email field definition
    password = PasswordField(  # Create the password input field
        "Password",  # Set the human-readable label for the password field
        validators=[DataRequired()],  # Require a password before submitting the form
    )  # Close the password field definition
    submit = SubmitField("Log In")  # Create the submit button for the login form