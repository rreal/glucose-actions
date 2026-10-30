"""Glucose data capture module using pylibrelinkup."""

import logging
import os
from datetime import datetime

from pylibrelinkup import PyLibreLinkUp
from pylibrelinkup.models.data import Patient, Trend

logger = logging.getLogger(__name__)


def connect(config: dict) -> tuple[PyLibreLinkUp, Patient] | None:
    """Authenticate and return (client, patient), or None if the account has no patients."""
    email = os.environ.get("LIBRELINKUP_EMAIL") or config["librelinkup"]["email"]
    password = os.environ.get("LIBRELINKUP_PASSWORD") or config["librelinkup"]["password"]

    client = PyLibreLinkUp(email=email, password=password)
    client.authenticate()

    patients = client.get_patients()
    if not patients:
        logger.error("No patients found in LibreLinkUp account")
        return None

    patient = patients[0]
    if len(patients) > 1:
        logger.info("Multiple patients found, using first: %s %s", patient.first_name, patient.last_name)
    return client, patient


def read_glucose(config: dict) -> dict | None:
    """Connect to LibreLinkUp and return latest glucose reading plus recent history, or None on failure."""
    try:
        connection = connect(config)
        if connection is None:
            return None
        client, patient = connection

        graph = client.read(patient)
        latest = graph.current
        if latest is None:
            logger.error("No glucose data returned for patient %s", patient.first_name)
            return None

        return {
            "value": int(latest.value),
            "timestamp": latest.factory_timestamp,
            "trend": latest.trend.name,
            "trend_arrow": "" if latest.trend == Trend.UNKNOWN else latest.trend.indicator,
            "is_high": latest.is_high,
            "is_low": latest.is_low,
            "history": local_readings([*graph.history, latest]),
        }
    except Exception as e:
        logger.error("Failed to read glucose data: %s: %s", type(e).__name__, e)
        return None


def read_logbook(config: dict) -> list[tuple[datetime, int]] | None:
    """Return ~14 days of logbook events (high/low alarms, scans) as local-time readings, or None on failure."""
    try:
        connection = connect(config)
        if connection is None:
            return None
        client, patient = connection
        return local_readings(client.logbook(patient))
    except Exception as e:
        logger.error("Failed to read logbook: %s: %s", type(e).__name__, e)
        return None


def local_readings(measurements: list) -> list[tuple[datetime, int]]:
    # `timestamp` is the patient's local wall-clock time, which is what hour-of-day patterns need
    return [(m.timestamp, int(m.value)) for m in measurements]
