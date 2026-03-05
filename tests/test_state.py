"""Unit tests for state persistence module."""

import json

from src.state import load_state, save_state


class TestLoadState:
    def test_file_not_found(self, tmp_path):
        assert load_state(str(tmp_path / "nonexistent.json")) == {}

    def test_valid_json(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text('{"last_alert_time": "2026-01-01T00:00:00+00:00", "last_alert_level": "low"}')
        result = load_state(str(path))
        assert result["last_alert_level"] == "low"

    def test_invalid_json(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text("not json {{{")
        assert load_state(str(path)) == {}


class TestSaveState:
    def test_writes_valid_json(self, tmp_path):
        path = str(tmp_path / "state.json")
        state = {"last_alert_time": "2026-01-01T00:00:00+00:00", "last_alert_level": "high"}
        save_state(path, state)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == state

    def test_atomic_write(self, tmp_path):
        path = str(tmp_path / "state.json")
        save_state(path, {"key": "value1"})
        save_state(path, {"key": "value2"})
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["key"] == "value2"

    def test_overwrites_existing(self, tmp_path):
        path = str(tmp_path / "state.json")
        save_state(path, {"old": True})
        save_state(path, {"new": True})
        with open(path) as f:
            loaded = json.load(f)
        assert "old" not in loaded
        assert loaded["new"] is True
