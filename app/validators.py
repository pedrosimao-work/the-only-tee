from app.constants import VALID_DROP_STATUSES  # Import the tuple containing every valid drop status


def validate_drop_status(status):  # Define a reusable function that validates a drop lifecycle status
    if status not in VALID_DROP_STATUSES:  # Check if the provided status is not one of the allowed statuses
        raise ValueError(f"Invalid drop status: {status}")  # Stop the program with a clear error message for invalid statuses

    return status  # Return the validated status when it is allowed