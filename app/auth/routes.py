from flask import Blueprint, flash, redirect, render_template, url_for  # Import Flask helpers for auth routes
from flask_login import current_user, login_required, login_user, logout_user  # Import Flask-Login helpers

from app.auth.forms import LoginForm, RegisterForm  # Import the authentication form classes
from app.extensions import db  # Import the database object so authroutes can save users
from app.models import User  # Import the User model so auth rotes can query and create users


auth = Blueprint("auth", __name__, url_prefix="/auth")  # Create the auth blueprint with /auth URL prefix


@auth.route("/register", methods=["GET", "POST"])  # Register the account creation route for GET and POST requests
def register():  # Define the function that handles user registration
    if current_user.is_authenticated:  # Check if the visitor is already logged in
        return redirect(url_for("main.home"))  # Redirect logged-in users away from the register page

    form = RegisterForm()  # Create a registration form instance

    if form.validate_on_submit():  # Check if the form was submitted and passed validation
        existing_email_user = User.query.filter_by(email=form.email.data.lower()).first()  # Look for an existing user with the submitted email
        existing_username_user = User.query.filter_by(username=form.username.data.strip()).first()  # Look for an existing user with the submitted username

        if existing_email_user:  # Check if the email is already registered
            flash("An account with that email already exists.", "danger")  # Show an error message to the user
            return render_template("auth/register.html", form=form)  # Re-render the registration page with the error

        if existing_username_user:  # Check if the username is already registered
            flash("That username is already taken.", "danger")  # Show an error message to the user
            return render_template("auth/register.html", form=form)  # Re-render the registration page with the error

        user = User(  # Create a new User object
            email=form.email.data.lower(),  # Store the email in lowercase for consistent login matching
            username=form.username.data.strip(),  # Store the cleaned username without surrounding spaces
        )  # Close the User object creation
        user.set_password(form.password.data)  # Hash and store the submitted password securely

        db.session.add(user)  # Add the new user to the database session
        db.session.commit()  # Save the new user permanently to the database

        flash("Account created successfully. You can now log in.", "success")  # Show a success message
        return redirect(url_for("auth.login"))  # Redirect the new user to the login page

    return render_template("auth/register.html", form=form)  # Render the registration page for GET requests or invalid form submissions


@auth.route("/login", methods=["GET", "POST"])  # Register the login route for GET and POST requests
def login():  # Define the function that handles user login
    if current_user.is_authenticated:  # Check if the visitor is already logged in
        return redirect(url_for("main.home"))  # Redirect logged-in users away from the login page

    form = LoginForm()  # Create a login form instance

    if form.validate_on_submit():  # Check if the form was submitted and passed validation
        user = User.query.filter_by(email=form.email.data.lower()).first()  # Look up a user by submitted email address

        if user and user.check_password(form.password.data):  # Check if the user exists and the password is correct
            login_user(user)  # Log the user in by storing their ID in the session
            flash("Logged in successfully.", "success")  # Show a success message
            return redirect(url_for("auth.profile"))  # Redirect the user to their profile page

        flash("Invalid email or password.", "danger")  # Show a generic login error message

    return render_template("auth/login.html", form=form)  # Render the login page for GET requests or invalid login attempts


@auth.route("/logout")  # Register the logout route
@login_required  # Require the user to be logged in before logging out
def logout():  # Define the function that handles user logout
    logout_user()  # Clear the current user's login session
    flash("Logged out successfully.", "success")  # Show a logout success message
    return redirect(url_for("main.home"))  # Redirect the user to the homepage


@auth.route("/profile")  # Register the protected profile route
@login_required  # Require login before accessing the profile page
def profile():  # Define the function that renders the user profile page
    return render_template("auth/profile.html")  # Render the profile template


