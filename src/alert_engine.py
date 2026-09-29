"""Alert logic: threshold evaluation, cooldown, stale detection, message building."""

import re
from datetime import datetime, timezone


def evaluate(glucose_value: int, config: dict) -> str:
    """Return 'low', 'high', or 'normal' based on configured thresholds."""
    low = config["alerts"]["low_threshold"]
    high = config["alerts"]["high_threshold"]
    if glucose_value < low:
        return "low"
    if glucose_value > high:
        return "high"
    return "normal"


def is_stale(reading_timestamp: datetime, max_age_minutes: int) -> bool:
    """Return True if the reading is older than max_age_minutes."""
    now = datetime.now(timezone.utc)
    age = now - reading_timestamp
    return age.total_seconds() > max_age_minutes * 60


def should_alert(level: str, state: dict, cooldown_minutes: int) -> bool:
    """Return True if an alert should be sent based on level, state, and cooldown."""
    if level == "normal":
        return False

    last_time = state.get("last_alert_time")
    last_level = state.get("last_alert_level")

    if not last_time:
        return True

    if level != last_level:
        return True

    last_dt = datetime.fromisoformat(last_time)
    now = datetime.now(timezone.utc)
    elapsed = (now - last_dt).total_seconds()
    return elapsed > cooldown_minutes * 60


DEFAULT_TREND_TEXTS = {
    "DOWN_FAST": "caindo rapido",
    "DOWN_SLOW": "caindo",
    "STABLE": "estavel",
    "UP_SLOW": "subindo",
    "UP_FAST": "subindo rapido",
}


def build_message(glucose_value: int, level: str, trend_arrow: str, config: dict | None = None,
                  trend: str = "") -> str:
    """Build alert message using configurable templates from config."""
    alerts_cfg = config.get("alerts", {}) if config else {}
    messages = alerts_cfg.get("messages", {})
    trend_texts = {**DEFAULT_TREND_TEXTS, **alerts_cfg.get("trend_texts", {})}

    template = messages.get(level, "")
    if not template:
        defaults = {
            "low": "Atencao: glicose em {value} mg/dL {trend} {trend_text}, nivel baixo",
            "high": "Atencao: glicose em {value} mg/dL {trend} {trend_text}, nivel alto",
        }
        template = defaults.get(level, "Alert: glucose {value} mg/dL {trend} {trend_text}, level {level}")

    message = template.format(value=glucose_value, trend=trend_arrow, trend_text=trend_texts.get(trend, ""),
                              level=level)
    # An empty trend (sensor reports UNKNOWN) would leave stray spaces before punctuation
    return re.sub(r" +([,.!?])", r"\1", re.sub(r" {2,}", " ", message)).strip()
