"""Local glucose history. LibreLinkUp's graph only covers ~12 hours, so readings are accumulated across cron runs."""

from datetime import datetime, timedelta

KEY_FORMAT = "%Y-%m-%dT%H:%M"
RETENTION_DAYS = 14


def merge_readings(history: dict, readings: list[tuple[datetime, int]], now: datetime) -> dict:
    """Return history with readings added (keyed by local minute) and entries past retention dropped."""
    merged = dict(history.get("readings", {}))
    for ts, value in readings:
        merged[ts.strftime(KEY_FORMAT)] = value
    cutoff = (now - timedelta(days=RETENTION_DAYS)).strftime(KEY_FORMAT)
    return {**history, "readings": {k: v for k, v in sorted(merged.items()) if k >= cutoff}}


def stored_readings(history: dict) -> list[tuple[datetime, int]]:
    return [(datetime.strptime(k, KEY_FORMAT), v) for k, v in history.get("readings", {}).items()]
