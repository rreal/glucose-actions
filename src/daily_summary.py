"""Daily summary entry point, run once a day by cron (e.g. 21:00). Use --dry-run to print without sending."""

import logging
import sys
from datetime import datetime

from src.glucose_reader import read_glucose, read_logbook
from src.history import merge_readings, stored_readings
from src.main import build_outputs, configure_logging, load_config, resolve_path, validate_config
from src.state import load_state, save_state
from src.summary_engine import build_summary

logger = logging.getLogger("glucose-actions")


def main() -> None:
    dry_run = "--dry-run" in sys.argv[1:]
    config = load_config()
    configure_logging(config)

    error = validate_config(config)
    if error:
        logger.error("Config validation failed: %s", error)
        sys.exit(1)

    summary_cfg = config.get("daily_summary", {})
    if not summary_cfg.get("enabled", False) and not dry_run:
        logger.info("Daily summary disabled")
        sys.exit(0)

    now = datetime.now()
    today = now.date()
    history_path = resolve_path(config.get("history_file", "history.json"))
    history = load_state(history_path)
    if history.get("last_summary_date") == today.isoformat() and not dry_run:
        logger.info("Daily summary already sent today")
        sys.exit(0)

    reading = read_glucose(config)
    if reading is not None:
        history = merge_readings(history, reading["history"], now)
    logbook = read_logbook(config) or []

    readings = stored_readings(history)
    message = build_summary(readings, readings + logbook, today, config)

    if dry_run:
        save_state(history_path, history)
        print(message)
        sys.exit(0)

    outputs = build_outputs(config, types=summary_cfg.get("outputs"))
    if not outputs:
        logger.warning("No outputs enabled for daily summary")
        sys.exit(1)

    glucose_value = reading["value"] if reading else 0
    results = [output.send_alert(message, glucose_value, "summary") for output in outputs]
    if any(results):
        history["last_summary_date"] = today.isoformat()
        logger.info("Daily summary sent: %s", message)
    else:
        logger.error("All outputs failed for daily summary")
    save_state(history_path, history)
    sys.exit(0 if any(results) else 1)


if __name__ == "__main__":
    main()
