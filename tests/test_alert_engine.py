"""Unit tests for alert engine."""

from datetime import datetime, timedelta, timezone

from src.alert_engine import build_message, evaluate, is_stale, should_alert


def make_config(low: int = 70, high: int = 180) -> dict:
    return {"alerts": {"low_threshold": low, "high_threshold": high}}


class TestEvaluate:
    def test_below_low_returns_low(self):
        assert evaluate(65, make_config()) == "low"

    def test_above_high_returns_high(self):
        assert evaluate(210, make_config()) == "high"

    def test_in_range_returns_normal(self):
        assert evaluate(100, make_config()) == "normal"

    def test_at_low_boundary_returns_normal(self):
        assert evaluate(70, make_config()) == "normal"

    def test_at_high_boundary_returns_normal(self):
        assert evaluate(180, make_config()) == "normal"

    def test_just_below_low(self):
        assert evaluate(69, make_config()) == "low"

    def test_just_above_high(self):
        assert evaluate(181, make_config()) == "high"


class TestIsStale:
    def test_recent_reading_not_stale(self):
        ts = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert is_stale(ts, 15) is False

    def test_old_reading_is_stale(self):
        ts = datetime.now(timezone.utc) - timedelta(minutes=20)
        assert is_stale(ts, 15) is True

    def test_exactly_at_boundary_is_stale(self):
        ts = datetime.now(timezone.utc) - timedelta(minutes=15)
        # At boundary (>= max_age), reading is considered stale
        assert is_stale(ts, 15) is True


class TestShouldAlert:
    def test_no_prior_state(self):
        assert should_alert("low", {}, 20) is True

    def test_same_level_within_cooldown(self):
        last_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        state = {"last_alert_time": last_time, "last_alert_level": "low"}
        assert should_alert("low", state, 20) is False

    def test_same_level_past_cooldown(self):
        last_time = (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat()
        state = {"last_alert_time": last_time, "last_alert_level": "low"}
        assert should_alert("low", state, 20) is True

    def test_level_changed(self):
        last_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        state = {"last_alert_time": last_time, "last_alert_level": "low"}
        assert should_alert("high", state, 20) is True

    def test_normal_level(self):
        assert should_alert("normal", {}, 20) is False


class TestBuildMessage:
    def test_low_default_message(self):
        msg = build_message(65, "low", "↘")
        assert msg == "Atencao: glicose em 65 mg/dL ↘, nivel baixo"

    def test_high_default_message(self):
        msg = build_message(210, "high", "↑")
        assert msg == "Atencao: glicose em 210 mg/dL ↑, nivel alto"

    def test_integer_formatting(self):
        msg = build_message(100, "low", "→")
        assert "100" in msg
        assert "100.0" not in msg

    def test_custom_message_from_config(self):
        config = {"alerts": {"messages": {
            "low": "Warning: glucose at {value} mg/dL {trend}, level {level}",
        }}}
        msg = build_message(65, "low", "↘", config)
        assert msg == "Warning: glucose at 65 mg/dL ↘, level low"

    def test_missing_config_uses_default(self):
        msg = build_message(65, "low", "↘", None)
        assert msg == "Atencao: glicose em 65 mg/dL ↘, nivel baixo"

    def test_partial_config_uses_default_for_missing(self):
        config = {"alerts": {"messages": {"low": "Custom low {value}"}}}
        msg = build_message(210, "high", "↑", config)
        assert msg == "Atencao: glicose em 210 mg/dL ↑, nivel alto"

    def test_empty_trend_leaves_no_stray_spaces(self):
        msg = build_message(65, "low", "", None)
        assert msg == "Atencao: glicose em 65 mg/dL, nivel baixo"

    def test_empty_trend_at_end_of_custom_template(self):
        config = {"alerts": {"messages": {"high": "Glucose {value} {trend}"}}}
        assert build_message(210, "high", "", config) == "Glucose 210"

    def test_default_message_includes_trend_text(self):
        msg = build_message(65, "low", "↘", None, trend="DOWN_SLOW")
        assert msg == "Atencao: glicose em 65 mg/dL ↘ caindo, nivel baixo"

    def test_high_default_message_with_fast_rise(self):
        msg = build_message(210, "high", "↑", None, trend="UP_FAST")
        assert msg == "Atencao: glicose em 210 mg/dL ↑ subindo rapido, nivel alto"

    def test_unknown_trend_leaves_trend_text_empty(self):
        msg = build_message(65, "low", "", None, trend="UNKNOWN")
        assert msg == "Atencao: glicose em 65 mg/dL, nivel baixo"

    def test_trend_texts_overridable_from_config(self):
        config = {"alerts": {
            "messages": {"low": "Warning: glucose at {value} mg/dL {trend} {trend_text}, level low"},
            "trend_texts": {"DOWN_FAST": "falling fast"},
        }}
        msg = build_message(55, "low", "↓", config, trend="DOWN_FAST")
        assert msg == "Warning: glucose at 55 mg/dL ↓ falling fast, level low"

    def test_partial_trend_texts_fall_back_to_defaults(self):
        config = {"alerts": {"trend_texts": {"DOWN_FAST": "falling fast"}}}
        msg = build_message(210, "high", "→", config, trend="STABLE")
        assert msg == "Atencao: glicose em 210 mg/dL → estavel, nivel alto"
