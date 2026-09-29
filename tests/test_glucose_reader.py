"""Unit tests for glucose reader."""

from unittest.mock import patch

from pylibrelinkup.models.data import GlucoseMeasurementWithTrend

from src.glucose_reader import read_glucose

CONFIG = {"librelinkup": {"email": "user@example.com", "password": "secret"}}


def make_measurement(trend_arrow: int) -> GlucoseMeasurementWithTrend:
    return GlucoseMeasurementWithTrend.model_validate({
        "FactoryTimestamp": "9/29/2026 10:00:00 AM",
        "Timestamp": "9/29/2026 7:00:00 AM",
        "type": 1,
        "ValueInMgPerDl": 65,
        "MeasurementColor": 1,
        "GlucoseUnits": 1,
        "Value": 65,
        "isHigh": False,
        "isLow": True,
        "TrendArrow": trend_arrow,
    })


def read_with(measurement: GlucoseMeasurementWithTrend) -> dict | None:
    with patch("src.glucose_reader.PyLibreLinkUp") as client_cls:
        client = client_cls.return_value
        client.get_patients.return_value = [object()]
        client.latest.return_value = measurement
        return read_glucose(CONFIG)


class TestReadGlucose:
    def test_known_trend_uses_arrow(self):
        reading = read_with(make_measurement(2))
        assert reading["trend"] == "DOWN_SLOW"
        assert reading["trend_arrow"] == "↘"

    def test_unknown_trend_has_empty_arrow(self):
        reading = read_with(make_measurement(0))
        assert reading["value"] == 65
        assert reading["trend"] == "UNKNOWN"
        assert reading["trend_arrow"] == ""
