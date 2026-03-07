"""Main entry point for glucose monitoring cron job."""

import fcntl
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from src.alert_engine import build_message, evaluate, is_stale, should_alert
from src.glucose_reader import read_glucose
from src.outputs.webhook import WebhookOutput
from src.outputs.whatsapp import WhatsAppOutput
from src.state import load_state, save_state

logger = logging.getLogger("glucose-actions")


def validate_config(config: dict) -> str | None:
    """Validate config. Returns error message or None if valid."""
    try:
        alerts = config["alerts"]
        low = alerts["low_threshold"]
        high = alerts["high_threshold"]
    except KeyError as e:
        return f"Missing required config field: {e}"

    if not isinstance(low, (int, float)) or not isinstance(high, (int, float)):
        return "Thresholds must be numbers"
    if low <= 0 or high <= 0:
        return "Thresholds must be positive"
    if low >= high:
        return f"low_threshold ({low}) must be less than high_threshold ({high})"

    cooldown = alerts.get("cooldown_minutes")
    if cooldown is None or cooldown <= 0:
        return "cooldown_minutes must be a positive number"

    max_age = alerts.get("max_reading_age_minutes")
    if max_age is None or max_age <= 0:
        return "max_reading_age_minutes must be a positive number"

    if "librelinkup" not in config:
        return "Missing librelinkup config section"

    ll = config["librelinkup"]
    if not ll.get("email") and not os.environ.get("LIBRELINKUP_EMAIL"):
        return "Missing librelinkup email (set in config or LIBRELINKUP_EMAIL env var)"
    if not ll.get("password") and not os.environ.get("LIBRELINKUP_PASSWORD"):
        return "Missing librelinkup password (set in config or LIBRELINKUP_PASSWORD env var)"

    return None


def configure_logging(config: dict) -> None:
    """Configure logging from config."""
    log_config = config.get("logging", {})
    level = getattr(logging, log_config.get("level", "INFO").upper(), logging.INFO)
    log_file = log_config.get("file", "")

    handler: logging.Handler
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


def build_outputs(config: dict) -> list:
    """Instantiate enabled output objects from config."""
    outputs = []
    for out_cfg in config.get("outputs", []):
        if not out_cfg.get("enabled", False):
            continue
        out_type = out_cfg.get("type")
        if out_type == "webhook":
            outputs.append(WebhookOutput(
                url=out_cfg["url"],
                token=out_cfg.get("token", ""),
                device=out_cfg.get("device", ""),
            ))
        elif out_type == "whatsapp":
            access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN") or out_cfg.get("access_token", "")
            outputs.append(WhatsAppOutput(
                phone_number_id=out_cfg["phone_number_id"],
                access_token=access_token,
                recipient=out_cfg["recipient"],
                template_name=out_cfg.get("template_name", "glucose_alert"),
                language_code=out_cfg.get("language_code", "pt_BR"),
            ))
        else:
            logger.warning("Unknown output type '%s', skipping", out_type)
    return outputs


def main() -> None:
    # Load config
    config_path = PROJECT_ROOT / "config.yaml"
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        sys.exit(1)

    if config is None:
        print("ERROR: config.yaml is empty", file=sys.stderr)
        sys.exit(1)

    # Configure logging
    configure_logging(config)

    # Validate config
    error = validate_config(config)
    if error:
        logger.error("Config validation failed: %s", error)
        sys.exit(1)

    # Acquire file lock
    lock_path = config.get("lock_file", "/tmp/glucose-actions.lock")
    if not os.path.isabs(lock_path):
        lock_path = str(PROJECT_ROOT / lock_path)
    try:
        lock_fd = open(lock_path, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        logger.info("Another instance is running, exiting")
        sys.exit(0)

    try:
        # Load state
        state_path = config.get("state_file", "state.json")
        if not os.path.isabs(state_path):
            state_path = str(PROJECT_ROOT / state_path)
        state = load_state(state_path)

        # Read glucose
        reading = read_glucose(config)
        if reading is None:
            logger.error("Failed to read glucose data")
            sys.exit(1)

        glucose_value = reading["value"]
        timestamp = reading["timestamp"]
        trend_arrow = reading["trend_arrow"]

        logger.info("Glucose: %d mg/dL %s (%s)", glucose_value, trend_arrow, timestamp)

        # Check stale
        max_age = config["alerts"]["max_reading_age_minutes"]
        if is_stale(timestamp, max_age):
            logger.warning("Stale reading from %s, skipping", timestamp)
            sys.exit(0)

        # Evaluate
        level = evaluate(glucose_value, config)

        # Normal — clear state if needed
        if level == "normal":
            if state:
                save_state(state_path, {})
                logger.info("Glucose back to normal, state cleared")
            else:
                logger.info("Glucose normal")
            sys.exit(0)

        # Check cooldown
        cooldown = config["alerts"]["cooldown_minutes"]
        if not should_alert(level, state, cooldown):
            logger.info("Alert suppressed by cooldown")
            sys.exit(0)

        # Build message and send
        message = build_message(glucose_value, level, trend_arrow, config)
        outputs = build_outputs(config)

        if not outputs:
            logger.warning("No outputs enabled, cannot send alert")
            sys.exit(1)

        any_success = False
        for output in outputs:
            if output.send_alert(message, glucose_value, level):
                any_success = True

        if any_success:
            new_state = {
                "last_alert_time": datetime.now(timezone.utc).isoformat(),
                "last_alert_level": level,
            }
            save_state(state_path, new_state)
            logger.info("Alert sent: %s", message)
            sys.exit(0)
        else:
            logger.error("All outputs failed, state not updated")
            sys.exit(1)

    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


if __name__ == "__main__":
    main()
