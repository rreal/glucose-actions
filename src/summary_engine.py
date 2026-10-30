"""Daily summary logic: time in range for the day and recurring out-of-range hours."""

from collections import defaultdict
from datetime import date, datetime, timedelta

DEFAULT_SUMMARY_MESSAGES = {
    "good": "Parabéns! Hoje a glicose ficou {tir}% do tempo na faixa ideal. Foi um ótimo dia, continue assim!",
    "improve_high": "Hoje a glicose ficou {tir}% do tempo na faixa ideal, e cada dia é um aprendizado. "
                    "Para chegar aos {goal}% amanhã, um cuidado extra com as refeições pode ajudar, "
                    "já que a glicose passou mais tempo acima de {high}.",
    "improve_low": "Hoje a glicose ficou {tir}% do tempo na faixa ideal, e cada dia é um aprendizado. "
                   "Para chegar aos {goal}% amanhã, ter um lanchinho por perto pode ajudar, "
                   "já que a glicose passou mais tempo abaixo de {low}.",
    "pattern_high": "Nos últimos {days} dias, a glicose costumou subir {hours}. Vale uma atenção especial nesses horários.",
    "pattern_low": "Nos últimos {days} dias, a glicose costumou baixar {hours}. "
                   "Vale uma atenção especial nesses horários, com um lanchinho por perto.",
    "no_data": "Hoje o sensor não enviou leituras suficientes para o resumo do dia.",
}


def day_stats(readings: list[tuple[datetime, int]], day: date, low: int, high: int) -> dict:
    values = [v for ts, v in readings if ts.date() == day]
    return {
        "count": len(values),
        "in_range": sum(low <= v <= high for v in values),
        "above": sum(v > high for v in values),
        "below": sum(v < low for v in values),
    }


def recurring_hours(readings: list[tuple[datetime, int]], today: date, days: int, min_days: int,
                    low: int, high: int) -> dict[str, list[int]]:
    """Hours of the day that were out of range on at least min_days distinct days in the window."""
    start = today - timedelta(days=days - 1)
    hits: dict[str, dict[int, set[date]]] = {"high": defaultdict(set), "low": defaultdict(set)}
    for ts, value in readings:
        if not start <= ts.date() <= today:
            continue
        if value > high:
            hits["high"][ts.hour].add(ts.date())
        elif value < low:
            hits["low"][ts.hour].add(ts.date())
    return {kind: sorted(h for h, dates in hours.items() if len(dates) >= min_days) for kind, hours in hits.items()}


def _clock(hour: int) -> str:
    return "meia-noite" if hour % 24 == 0 else f"{hour}h"


def _around(hour: int) -> str:
    if hour == 0:
        return "por volta da meia-noite"
    if hour == 1:
        return "por volta da 1h"
    return f"por volta das {hour}h"


def format_hours(hours: list[int]) -> str:
    """Spoken pt-BR description, e.g. [8, 14, 15, 16] -> 'por volta das 8h e entre 14h e 17h'."""
    groups: list[list[int]] = []
    for hour in sorted(hours):
        if groups and hour == groups[-1][-1] + 1:
            groups[-1].append(hour)
        else:
            groups.append([hour])
    parts = [_around(g[0]) if len(g) == 1 else f"entre {_clock(g[0])} e {_clock(g[-1] + 1)}" for g in groups]
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " e " + parts[-1]


def build_summary(today_readings: list[tuple[datetime, int]], pattern_readings: list[tuple[datetime, int]],
                  today: date, config: dict) -> str:
    """today_readings must be continuous (CGM history); pattern_readings may also include sparse logbook events."""
    cfg = config.get("daily_summary", {})
    messages = {**DEFAULT_SUMMARY_MESSAGES, **cfg.get("messages", {})}
    low = config["alerts"]["low_threshold"]
    high = config["alerts"]["high_threshold"]
    goal = cfg.get("goal_percent", 80)
    days = cfg.get("pattern_days", 7)
    fields = {"goal": goal, "low": low, "high": high, "days": days}

    parts = []
    stats = day_stats(today_readings, today, low, high)
    if stats["count"] < cfg.get("min_readings", 16):
        parts.append(messages["no_data"].format(**fields))
    else:
        tir = round(100 * stats["in_range"] / stats["count"])
        if tir >= goal:
            key = "good"
        else:
            key = "improve_high" if stats["above"] >= stats["below"] else "improve_low"
        parts.append(messages[key].format(tir=tir, **fields))

    patterns = recurring_hours(pattern_readings, today, days, cfg.get("pattern_min_days", 3), low, high)
    for kind in ("high", "low"):
        if patterns[kind]:
            parts.append(messages[f"pattern_{kind}"].format(hours=format_hours(patterns[kind]), **fields))
    return " ".join(parts)
