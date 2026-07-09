from datetime import datetime, timezone

def get_utc_now() -> datetime:
    """Returns the current datetime in UTC."""
    return datetime.now(timezone.utc)
