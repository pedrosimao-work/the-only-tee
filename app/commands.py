import click  # Import Click so we can display styled messages in the terminal
from sqlalchemy.engine.url import make_url  # Import make_url so we can safely inspect the database URI

from app.constants import DEFAULT_SHIRT_COLOR, DROP_PRODUCT_TYPE_TSHIRT, DROP_STATUS_ACTIVE, DROP_STATUS_ARCHIVED, DROP_STATUS_DRAFT  # Import reusable status constants for seed data
from app.extensions import db  # Import the database object so we can save and delete records
from app.models import Drop  # Import the Drop model so we can create drop records
from app.services.drop_lifecycle import get_current_time, get_month_start, get_next_month_start, get_previous_month_start, rotate_monthly_drops  # Import monthly lifecycle helpers

def register_commands(app):  # Define a function that registers custom made commands on the Flask app
    @app.cli.command("seed-drops")  # Create a custom terminal command named flask seed-drops
    def seed_drops():  # Define the function that runs when seed-drops command is executed
        Drop.query.delete()  # Delete all existing Drop records so the seed data starts clean
        now = get_current_time()  # Get the current business time
        current_month_start = get_month_start(now)  # Calculate the first second of the current month
        next_month_start = get_next_month_start(now)  # Calculate the first second of the next month
        month_after_next_start = get_next_month_start(next_month_start)  # Calculate the first second of the month after next
        previous_month_start = get_previous_month_start(current_month_start)  # Calculate the first second of the previous month
        two_months_ago_start = get_previous_month_start(previous_month_start)  # Calculate the first second of two months ago

        active_drop = Drop(  # Create one active drop record
            drop_number="0001",  # Set the active drop
            season=1,  # Set the active drop season
            name="Silent Horizon",  # Set the active drop name
            description="The first monthly T-shirt design from The Only Drop. Available while stock lasts, then archived permanently.",  # Set the active drop description
            price=59,  # Set the fixed active drop price
            status=DROP_STATUS_ACTIVE,  # Mark this drop as active using the reusable status constant
            product_type=DROP_PRODUCT_TYPE_TSHIRT,  # Set the active drop product type
            shirt_color=DEFAULT_SHIRT_COLOR,  # Set the active drop selected shirt color
            starts_at=current_month_start,  # Schedule the active drop to start at the beginning of the current month
            ends_at=next_month_start,  # Schedule the active drop to end at the beginning of the next month
        )  # Close the active drop object creation

        archived_drop_one = Drop(  # Create the first archived drop record
            drop_number="0002",  # Set the first archived drop number
            season=1,  # Set the first archived drop season
            name="Frozen Signal",  # Set the first archived drop name
            description="An archived monthly T-shirt design from The Only Drop collection.",  # Set the first archived drop description
            price=59,  # Set the first archived drop price
            status=DROP_STATUS_ARCHIVED,  # Mark this drop as archived using the reusable status constant
            product_type=DROP_PRODUCT_TYPE_TSHIRT,  # Set the archived drop product type
            shirt_color="White",  # Set the archived drop selected shirt color
            starts_at=previous_month_start,  # Store when the archived drop started
            ends_at=current_month_start,  # Store when the archived drop ended
            archived_at=current_month_start,  # Store when the archived drop entered the archive
        )  # Close the first archived drop object creation

        archived_drop_two = Drop(  # Create the second archived drop record
            drop_number="0003",  # Set the second archived drop number
            season=1,  # Set the second archived drop season
            name="Cold Archive",  # Set the second archived drop name
            description="An archived monthly T-shirt design from The Only Drop collection.",  # Set the second archived drop description
            price=59,  # Set the second archived drop price
            status=DROP_STATUS_ARCHIVED,  # Mark this drop as archived using the reusable status constant
            product_type=DROP_PRODUCT_TYPE_TSHIRT,  # Set the archived drop product type
            shirt_color="Navy",  # Set the archived drop selected shirt color
            starts_at=two_months_ago_start,  # Store when the archived drop started
            ends_at=previous_month_start,  # Store when the archived drop ended
            archived_at=previous_month_start,  # Store when the archived drop entered the archive
        )  # Close the second archived drop object creation

        scheduled_drop = Drop(  # Create one future scheduled draft drop
            drop_number="0004",  # Set the scheduled drop number
            season=1,  # Set the scheduled drop season
            name="Static Garden",  # Set the scheduled drop name
            description="A scheduled monthly T-shirt design prepared for the next drop window.",  # Set the scheduled drop description
            price=59,  # Set the scheduled drop price
            status=DROP_STATUS_DRAFT,  # Keep the scheduled drop as draft until the lifecycle command activates it
            product_type=DROP_PRODUCT_TYPE_TSHIRT,  # Set the scheduled drop product type
            shirt_color="black",  # Set the scheduled drop selected shirt color
            starts_at=next_month_start,  # Schedule this drop to start at the beginning of the next month
            ends_at=month_after_next_start,  # Schedule this drop to end at the beginning of the following month
        )  # Close the scheduled drop object creation

        db.session.add(active_drop)  # Add the active drop object to the database session
        db.session.add(archived_drop_one)  # Add the first archived drop object to the database session
        db.session.add(archived_drop_two)  # Add the second archived drop object to the database session
        db.session.add(scheduled_drop)  # Add the scheduled draft drop object to the database session
        db.session.commit()  # Save all seeded drop records permanently to the database

        click.echo("Seeded 4 drop records successfully.")  # Display a success message in the terminal


    @app.cli.command("rotate-drops")  # Create a custom terminal command named flask rotate-drops
    def rotate_drops():  # Define the function that runs when the rotate-drops command is executed
        result = rotate_monthly_drops()  # Run the monthly lifecycle rotation service

        click.echo(f"Rotation reference time: {result['reference_time']}")  # Display the time used for this rotation
        click.echo(f"Expired drops archived: {len(result['expired_archived_drops'])}")  # Display how many expired active drops were archived
        click.echo(f"Extra active drops archived: {len(result['extra_archived_drops'])}")  # Display how many extra active drops were archived

        if result['activated_drop']:  # Check if a scheduled drop was activated
            click.echo(f"Activated drop: #{result['activated_drop'].drop_number} - {result['activated_drop'].name}")  # Display the activated drop information
        else:  # Run this block if no scheduled drop was activated
            click.echo("Activated drop: none")  # Display that no drop was activated


    @app.cli.command("db-info")  # Create a custom terminal command named flask db-info
    def db_info():  # Define the function that displays safe database connection information
        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]  # Read the configured SQLAlchemy database URI
        parsed_uri = make_url(database_uri)  # Parse the URI into safe structured parts

        click.echo(f"Database driver: {parsed_uri.drivername}")  # Display the database driver without exposing secrets
        click.echo(f"Database host: {parsed_uri.host or 'local file'}")  # Display the database host or local file fallback
        click.echo(f"Database name: {parsed_uri.database}")  # Display the database name or SQLite file path
        click.echo("Database password: hidden")  # Confirm that password output is intentionally hidden