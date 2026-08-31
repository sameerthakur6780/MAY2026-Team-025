from datetime import date, datetime


def isoformat_utc(dt):
    """Serialize a datetime as an ISO 8601 string with an explicit UTC marker.

    Every DateTime column in this app stores naive datetimes that were
    always UTC to begin with (SQLite drops tzinfo on write). Calling plain
    `.isoformat()` on the naive value read back gives a string with no
    offset, which browsers then parse as *local* time instead of UTC --
    shifting the displayed time by whatever the user's UTC offset is. This
    helper appends the missing marker so the frontend converts to local
    time correctly.

    Also accepts plain ``date`` values (e.g. rows created before the
    due_date column was migrated from Date to DateTime).
    """
    if dt is None:
        return None
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt.isoformat() + "T00:00:00Z"
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.isoformat()
