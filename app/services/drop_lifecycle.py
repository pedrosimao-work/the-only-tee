from datetime import datetime  # Import datetime so we can calculate month boundaries
from zoneinfo import ZoneInfo  # Import ZoneInfo so monthly rotation uses the business timezone

from app.constants import APP_TIMEZONE, DROP_STATUS_ACTIVE, DROP_STATUS_ARCHIVED, DROP_STATUS_DRAFT  # Import timezone and drop status constants
from app.extensions import db  # Import the database object so lifecycle changes can be saved
from app.models import Drop  # Import the Drop model so lifecycle logic can query and update drops


def get_current_time():  # Define a helper function that returns the current business time
    return datetime.now(ZoneInfo(APP_TIMEZONE)).replace(tzinfo=None)  # Return timezone-based time as a naive datetime for the current database setup


def get_month_start(reference_time):  # Define a helper function that returns the start of the reference month
    return reference_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # Return the first second of the month


def get_next_month_start(reference_time):  # Define a helper function that returns the start of the next month
    month_start = get_month_start(reference_time)  # Normalize the reference time to the first second of its month

    if month_start.month == 12:  # Check if the current month is December
        return month_start.replace(year=month_start.year + 1, month=1)  # Return January of the next year

    return month_start.replace(month=month_start.month + 1)  # Return the first second of the next month


def get_previous_month_start(reference_time):  # Define a helper function that returns the start of the previous month
    month_start = get_month_start(reference_time)  # Normalize the reference time to the first second of its month

    if month_start.month == 1:  # Check if the current month is January
        return month_start.replace(year=month_start.year - 1, month=12)  # Return December of the previous year

    return month_start.replace(month=month_start.month - 1)  # Return the first second of the previous month


def archive_expired_active_drops(reference_time):  # Define a function that archives active drops whose end date has passed
    expired_active_drops = Drop.query.filter(  # Query active drops that have an end date in the past
        Drop.status == DROP_STATUS_ACTIVE,  # Only look at currently active drops
        Drop.ends_at.isnot(None),  # Only archive drops that have a defined end date
        Drop.ends_at <= reference_time,  # Only archive drops that ended before or at the reference time
    ).all()  # Return all matching expired active drops

    for drop in expired_active_drops:  # Loop through each expired active drop
        drop.status = DROP_STATUS_ARCHIVED  # Mark the expired drop as archived
        drop.archived_at = reference_time  # Store when the drop was archived

    return expired_active_drops  # Return the archived drops for reporting


def archive_extra_active_drops(reference_time):  # Define a function that guarantees only one active drop remains
    active_drops = Drop.query.filter_by(status=DROP_STATUS_ACTIVE).all()  # Query all currently active drops

    if len(active_drops) <= 1:  # Check if there are zero or one active drops
        return []  # Return an empty list because no cleanup is needed

    active_drops.sort(  # Sort active drops so the most recent scheduled drop stays active
        key=lambda drop: (drop.starts_at or datetime.min, drop.id or 0),  # Sort by start date first and database ID second
        reverse=True,  # Put the newest active drop first
    )  # Close the sort call

    extra_active_drops = active_drops[1:]  # Keep every active drop except the first one as extras

    for drop in extra_active_drops:  # Loop through active drops that should not remain active
        drop.status = DROP_STATUS_ARCHIVED  # Archive the extra active drop
        drop.archived_at = reference_time  # Store when the extra active drop was archived

    return extra_active_drops  # Return the extra archived drops for reporting


def activate_scheduled_drop(reference_time):  # Define a function that activates the next scheduled draft drop
    existing_active_drop = Drop.query.filter_by(status=DROP_STATUS_ACTIVE).first()  # Check if an active drop already exists

    if existing_active_drop:  # Check if there is already an active drop
        return None  # Do not activate another drop because only one active drop is allowed

    scheduled_drop = Drop.query.filter(  # Query the next draft drop scheduled to start
        Drop.status == DROP_STATUS_DRAFT,  # Only look at draft drops
        Drop.starts_at.isnot(None),  # Only consider drops with a defined start date
        Drop.starts_at <= reference_time,  # Only consider drops whose start date has arrived
    ).order_by(  # Start ordering scheduled candidates
        Drop.starts_at.asc(),  # Activate the earliest scheduled eligible drop first
        Drop.drop_number.asc(),  # Use drop number as a stable secondary order
    ).first()  # Return only the next scheduled drop

    if not scheduled_drop:  # Check if no scheduled draft drop is ready
        return None  # Return nothing because there is no drop to activate

    scheduled_drop.status = DROP_STATUS_ACTIVE  # Mark the scheduled draft drop as active

    if scheduled_drop.ends_at is None:  # Check if the scheduled drop does not already have an end date
        scheduled_drop.ends_at = get_next_month_start(scheduled_drop.starts_at)  # Default the end date to the first second of the next month

    return scheduled_drop  # Return the activated drop for reporting


def rotate_monthly_drops(reference_time=None):  # Define the main monthly lifecycle function
    if reference_time is None:  # Check if no reference time was provided
        reference_time = get_current_time()  # Use the current business time by default

    expired_archived_drops = archive_expired_active_drops(reference_time)  # Archive active drops whose monthly window has ended
    extra_archived_drops = archive_extra_active_drops(reference_time)  # Archive extra active drops if the database has more than one
    activated_drop = activate_scheduled_drop(reference_time)  # Activate the next scheduled draft drop if no active drop remains

    db.session.commit()  # Save all lifecycle changes permanently to the database

    return {  # Return a report dictionary for CLI output and future logging
        "reference_time": reference_time,  # Include the time used for this rotation
        "expired_archived_drops": expired_archived_drops,  # Include drops archived because they expired
        "extra_archived_drops": extra_archived_drops,  # Include drops archived because they were extra active drops
        "activated_drop": activated_drop,  # Include the drop activated during this rotation
    }  # Close the report dictionary