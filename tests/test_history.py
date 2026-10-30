"""Unit tests for local glucose history."""

from datetime import datetime

from src.history import merge_readings, stored_readings

NOW = datetime(2026, 10, 29, 21, 0)


class TestMergeReadings:
    def test_adds_and_deduplicates_by_minute(self):
        history = merge_readings({}, [(datetime(2026, 10, 29, 10, 0, 30), 100)], NOW)
        history = merge_readings(history, [(datetime(2026, 10, 29, 10, 0, 45), 105),
                                           (datetime(2026, 10, 29, 10, 15), 110)], NOW)
        assert history["readings"] == {"2026-10-29T10:00": 105, "2026-10-29T10:15": 110}

    def test_drops_readings_past_retention(self):
        history = merge_readings({"readings": {"2026-10-01T10:00": 90}}, [], NOW)
        assert history["readings"] == {}

    def test_keeps_other_keys(self):
        history = merge_readings({"last_summary_date": "2026-10-28"}, [], NOW)
        assert history["last_summary_date"] == "2026-10-28"

    def test_round_trip(self):
        ts = datetime(2026, 10, 29, 10, 15)
        assert stored_readings(merge_readings({}, [(ts, 110)], NOW)) == [(ts, 110)]
