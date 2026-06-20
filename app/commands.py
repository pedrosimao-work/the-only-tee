import click  # Import Click so we can display styled messages in the terminal

from app.extensions import db  # Import the database object so we can save and delete records
from app.models import Drop  # Import the Drop model so we can create drop records


def register_commands(app):  # Define a function that registers custom made commands on the Flask app
    @app.cli.command("seed-drops")  # Create a custom terminal command named flask seed-drops
    def seed_drops():  # Define the function that runs when seed-drops command is executed
        Drop.query.delete()  # Delete all existing Drop records so the seed data starts clean

        active_drop = Drop(  # Create one active drop record
            drop_number="0001",  # Set the active drop
            season=1,  # Set the active drop season
            name="Silent Horizon",  # Set the active drop name
            description="A one-time T-shirt drop available for a limited window before entering the Archive Collection permanently.",  # Set the active drop description
            price=59,  # Set the fixed active drop price
            status="active",  # Mark this drop as the current active drop
        )  # Close the active drop object creation

        archived_drop_one = Drop(  # Create the first archived drop record
            drop_number="0002",  # Set the first archived drop number
            season=1,  # Set the first archived drop season
            name="Frozen Signal",  # Set the first archived drop name
            description="A finished limited drop from the first collection.",  # Set the first archived drop description
            price=59,  # Set the first archived drop price
            status="archived",  # Mark this drop as archived
        )  # Close the first archived drop object creation

        archived_drop_two = Drop(  # Create the second archived drop record
            drop_number="0003",  # Set the second archived drop number
            season=1,  # Set the second archived drop season
            name="Cold Archive",  # Set the second archived drop name
            description="A finished limited drop from the first collection.",  # Set the second archived drop description
            price=59,  # Set the second archived drop price
            status="archived",  # Mark this drop object creation
        )  # Close the second archived drop object creation

        db.session.add(active_drop)  # Add the active drop object to the database session
        db.session.add(archived_drop_one)  # Add the first archived drop object to the database session
        db.session.add(archived_drop_two)  # Add the second archived drop object to the database session
        db.session.commit()  # Save all seeded drop records permanently to the database

        click.echo("Seeded 3 drop records successfully.")  # Display a success message in the terminal