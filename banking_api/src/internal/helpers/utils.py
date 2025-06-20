import uuid
from datetime import UTC, datetime
from uuid import UUID


def get_timestamp() -> datetime:
    """Get the current timestamp in UTC."""
    return datetime.now(tz=UTC)


def get_uuid() -> UUID:
    """Generate a UUID4."""
    return uuid.uuid4()


def generate_unique_account_number() -> str:
    """Generate a unique account number based on UUID."""
    # Generate a UUID and extract parts
    unique_id = get_uuid()
    # Use first 16 characters of the UUID
    id_part = str(unique_id).replace("-", "")[:16]

    # Format as ACCT-YYYY-XXXX-XXXX where XXXX-XXXX are from UUID
    year = datetime.now().strftime("%Y")
    first_part = id_part[:4]
    second_part = id_part[4:8]

    return f"DE-{year}-{first_part}-{second_part}"
