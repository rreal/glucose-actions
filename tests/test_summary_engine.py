"""Unit tests for daily summary engine."""

from datetime import date, datetime, timedelta

from src.summary_engine import build_summary, day_stats, format_hours, recurring_hours

TODAY = date(2026, 10, 29)


def make_config(**summary) -> dict:
    return {"alerts": {"low_threshold": 70, "high_threshold": 180}, "daily_summary": summary}


def day_readings(day: date, values: list[int]) -> list[tuple[datetime, int]]:
    start = datetime.combine(day, datetime.min.time())
    return [(start + timedelta(minutes=15 * i), v) for i, v in enumerate(values)]


def at(day_offset: int, hour: int, value: int) -> tuple[datetime, int]:
    return datetime.combine(TODAY - timedelta(days=day_offset), datetime.min.time()) + timedelta(hours=hour), value


class TestDayStats:
    def test_counts_only_the_given_day(self):
        readings = day_readings(TODAY, [100, 200, 60]) + day_readings(TODAY - timedelta(days=1), [300])
        assert day_stats(readings, TODAY, 70, 180) == {"count": 3, "in_range": 1, "above": 1, "below": 1}

    def test_boundaries_are_in_range(self):
        assert day_stats(day_readings(TODAY, [70, 180]), TODAY, 70, 180)["in_range"] == 2


class TestRecurringHours:
    def test_hour_repeated_on_enough_days_is_reported(self):
        readings = [at(d, 15, 220) for d in range(3)] + [at(0, 9, 220)]
        assert recurring_hours(readings, TODAY, 7, 3, 70, 180) == {"high": [15], "low": []}

    def test_multiple_readings_same_day_count_once(self):
        readings = [at(0, 15, 220), at(0, 15, 230), at(1, 15, 220)]
        assert recurring_hours(readings, TODAY, 7, 3, 70, 180)["high"] == []

    def test_days_outside_window_are_ignored(self):
        readings = [at(d, 3, 60) for d in (0, 1, 7)]
        assert recurring_hours(readings, TODAY, 7, 3, 70, 180)["low"] == []

    def test_lows_detected_separately(self):
        readings = [at(d, 3, 60) for d in (0, 2, 5)]
        assert recurring_hours(readings, TODAY, 7, 3, 70, 180) == {"high": [], "low": [3]}


class TestFormatHours:
    def test_single_hour(self):
        assert format_hours([15]) == "por volta das 15h"

    def test_consecutive_hours_become_range(self):
        assert format_hours([14, 15, 16]) == "entre 14h e 17h"

    def test_multiple_groups(self):
        assert format_hours([8, 14, 15, 22]) == "por volta das 8h, entre 14h e 16h e por volta das 22h"

    def test_midnight_and_one_oclock(self):
        assert format_hours([0]) == "por volta da meia-noite"
        assert format_hours([1]) == "por volta da 1h"
        assert format_hours([23]) == "por volta das 23h"
        assert format_hours([22, 23]) == "entre 22h e meia-noite"


class TestBuildSummary:
    def test_good_day_congratulates(self):
        readings = day_readings(TODAY, [120] * 17 + [200] * 3)
        message = build_summary(readings, readings, TODAY, make_config())
        assert message.startswith("Parabéns! Hoje a glicose ficou 85%")

    def test_goal_is_inclusive(self):
        readings = day_readings(TODAY, [120] * 16 + [200] * 4)
        assert build_summary(readings, readings, TODAY, make_config()).startswith("Parabéns")

    def test_below_goal_mostly_high_suggests_meals(self):
        readings = day_readings(TODAY, [120] * 10 + [200] * 8 + [60] * 2)
        message = build_summary(readings, readings, TODAY, make_config())
        assert "50%" in message and "refeições" in message and "acima de 180" in message

    def test_below_goal_mostly_low_suggests_snack(self):
        readings = day_readings(TODAY, [120] * 10 + [60] * 8 + [200] * 2)
        message = build_summary(readings, readings, TODAY, make_config())
        assert "lanchinho" in message and "abaixo de 70" in message

    def test_few_readings_reports_no_data(self):
        readings = day_readings(TODAY, [120] * 5)
        message = build_summary(readings, readings, TODAY, make_config())
        assert message == "Hoje o sensor não enviou leituras suficientes para o resumo do dia."

    def test_patterns_appended_after_day_result(self):
        today = day_readings(TODAY, [120] * 20)
        events = [at(d, 15, 220) for d in range(1, 4)] + [at(d, 3, 60) for d in range(1, 4)]
        message = build_summary(today, today + events, TODAY, make_config())
        assert message == (
            "Parabéns! Hoje a glicose ficou 100% do tempo na faixa ideal. Foi um ótimo dia, continue assim! "
            "Nos últimos 7 dias, a glicose costumou subir por volta das 15h. Vale uma atenção especial nesses horários. "
            "Nos últimos 7 dias, a glicose costumou baixar por volta das 3h. "
            "Vale uma atenção especial nesses horários, com um lanchinho por perto."
        )

    def test_custom_messages_and_goal(self):
        readings = day_readings(TODAY, [120] * 18 + [200] * 2)
        config = make_config(goal_percent=95, messages={"improve_high": "{tir} de {goal}"})
        assert build_summary(readings, readings, TODAY, config) == "90 de 95"
