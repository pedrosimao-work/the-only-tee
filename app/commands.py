import click  # Import Click so we can display styled messages in the terminal
from sqlalchemy.engine.url import make_url  # Import make_url so we can safely inspect the database URI

from app.constants import DEFAULT_SHIRT_COLOR, DROP_PRODUCT_TYPE_TSHIRT, DROP_STATUS_ACTIVE, DROP_STATUS_ARCHIVED, DROP_STATUS_DRAFT  # Import reusable status constants for seed data
from app.extensions import db  # Import the database object so we can save and delete records
from app.models import Drop  # Import the Drop model so we can create drop records
from app.services.drop_lifecycle import get_current_time, get_month_start, get_next_month_start, get_previous_month_start, rotate_monthly_drops  # Import monthly lifecycle helpers
from app.services.printify import PrintifyAPIError, PrintifyConfigError, get_printify_product, get_printify_products, get_printify_shops, sync_drop_with_printify  # Import Printify helpers for CLI commands


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


    @app.cli.command("printify-shops")  # Create a custom terminal command named flask printify-shops
    def printify_shops():  # Define the function that lists connected Printify shops
        try:  # Start a protected block for Printify API access
            shops = get_printify_shops()  # Retrieve the Printify shops connected to this account
        except (PrintifyConfigError, PrintifyAPIError) as error:  # Catch Printify configuration and API errors
            click.echo(f"Printify error: {error}")  # Display the Printify error in the terminal
            return  # Stop the command after printing the error

        if not shops:  # Check if the API returned no shops
            click.echo("No Printify shops found.")  # Display an empty result message
            return  # Stop the command because there are no shops to display

        for shop in shops:  # Loop through each Printify shop
            click.echo(f"{shop.get('id')} - {shop.get('title')} - {shop.get('sales_channel')}")  # Display the shop ID, title, and sales channel


    @app.cli.command("printify-products")  # Create a custom terminal command named flask printify-products
    def printify_products():  # Define the function that lists Printify products from the configured shop
        try:  # Start a protected block for Printify API access
            products_response = get_printify_products()  # Retrieve products from the configured Printify shop
        except (PrintifyConfigError, PrintifyAPIError) as error:  # Catch Printify configuration and API errors
            click.echo(f"Printify error: {error}")  # Display the Printify error in the terminal
            return  # Stop the command after printing the error

        products = products_response.get("data", products_response)  # Support paginated and direct-list response shapes

        if not products:  # Check if no products were returned
            click.echo("No Printify products found.")  # Display an empty result message
            return  # Stop the command because there are no products

        for product in products:  # Loop through each Printify product
            click.echo(f"{product.get('id')} - {product.get('title')}")  # Display the product ID and product title


    @app.cli.command("printify-product")  # Create a custom terminal command named flask printify-product
    @click.argument("product_id")  # Require a Printify product ID argument
    def printify_product(product_id):  # Define the function that inspects one Printify product
        try:  # Start a protected block for Printify API access
            product = get_printify_product(product_id)  # Retrieve the Printify product by ID
        except (PrintifyConfigError, PrintifyAPIError) as error:  # Catch Printify configuration and API errors
            click.echo(f"Printify error: {error}")  # Display the Printify error in the terminal
            return  # Stop the command after printing the error

        click.echo(f"Product ID: {product.get('id')}")  # Display the Printify product ID
        click.echo(f"Title: {product.get('title')}")  # Display the Printify product title
        click.echo(f"Visible: {product.get('visible')}")  # Display whether the Printify product is visible
        click.echo(f"Locked: {product.get('is_locked')}")  # Display whether the Printify product is locked
        click.echo(f"Variant count: {len(product.get('variants', []))}")  # Display how many variants the product has
        click.echo("Available enabled variants:")  # Display a heading for available variants

        for variant in product.get("variants", []):  # Loop through every Printify variant
            if variant.get("is_enabled") and variant.get("is_available"):  # Check if the variant can currently be sold
                click.echo(f"- {variant.get('id')} | {variant.get('title')} | {variant.get('sku')}")  # Display variant ID, title, and SKU

    @app.cli.command("printify-sync-drop")  # Create a custom terminal command named flask printify-sync-drop
    @click.argument("drop_number")  # Require a local drop number argument
    def printify_sync_drop(drop_number):  # Define the function that syncs a local drop with Printify
        drop = Drop.query.filter_by(drop_number=drop_number).first()  # Find the local drop by drop number

        if not drop:  # Check if no local drop matched the provided number
            click.echo(f"Drop #{drop_number} was not found.")  # Display a clear not-found message
            return  # Stop the command because there is no drop to sync

        try:  # Start a protected block for Printify sync
            result = sync_drop_with_printify(drop)  # Sync the local drop with Printify
        except (PrintifyConfigError, PrintifyAPIError) as error:  # Catch Printify configuration and API errors
            click.echo(f"Printify error: {error}")  # Display the Printify error in the terminal
            return  # Stop the command after printing the error

        variant_summary = result["variant_summary"]  # Store the returned variant summary locally
        selected_count = len(variant_summary["selected_variants"])  # Count selected variants found on the product
        selected_available_count = len(variant_summary["selected_available_variants"])  # Count selected variants currently available

        click.echo(f"Synced Drop #{drop.drop_number} with Printify product {drop.printify_product_id}.")  # Display the synced drop and product
        click.echo(f"Image URL synced: {bool(result['default_image_url'])}")  # Display whether a mockup image was synced
        click.echo(f"Selected variants available: {selected_available_count}/{selected_count}")  # Display selected variant availability