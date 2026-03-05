"""Glucose data capture module using pylibrelinkup."""

import logging
import os

from pylibrelinkup import PyLibreLinkUp

logger = logging.getLogger(__name__)


def read_glucose(config: dict) -> dict | None:
    """Connect to LibreLinkUp and return latest glucose reading, or None on failure."""
    try:
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
        latest = client.latest(patient)
        if latest is None:
            logger.error("No glucose data returned for patient %s", patients[0].first_name)
            return None

        return {
            "value": int(latest.value),
            "timestamp": latest.factory_timestamp,
            "trend": latest.trend.name,
            "trend_arrow": latest.trend.indicator,
            "is_high": latest.is_high,
            "is_low": latest.is_low,
        }
    except Exception as e:
        logger.error("Failed to read glucose data: %s: %s", type(e).__name__, e)
        return None
