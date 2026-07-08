from app.constants import VALID_DROP_STATUSES, VALID_PRODUCT_TYPES  # Import allowed lifecycle statuses and product types


def validate_drop_status(status):  # Define a reusable function that validates a drop lifecycle status
    if status not in VALID_DROP_STATUSES:  # Check if the provided status is not one of the allowed statuses
        raise ValueError(f"Invalid drop status: {status}")  # Stop the program with a clear error message for invalid statuses

    return status  # Return the validated status when it is allowed


def validate_product_type(product_type):  # Define a reusable function that validates a drop product type
    if product_type not in VALID_PRODUCT_TYPES:  # Check if the provided product type is not supported
        raise ValueError(f"Invalid product type: {product_type}")  # Stop the program with a clear error message for invalid product types

    return product_type  # Return the validated product type when it is allowed