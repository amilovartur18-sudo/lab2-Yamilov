"""Расчёт статистики событий."""

from collections import Counter
from collections.abc import Iterable
from datetime import datetime

from .models import LEVELS, Event


def analyze(events: Iterable[Event]) -> dict[str, object]:
    """Обработать события без накопления списка."""
    total = 0
    by_level = {level: 0 for level in sorted(LEVELS)}
    by_source: Counter[str] = Counter()
    error_sources: Counter[str] = Counter()
    first: datetime | None = None
    last: datetime | None = None
    for event in events:
        total += 1
        by_level[event.level] += 1
        by_source[event.source] += 1
        if event.level in {"ERROR", "CRITICAL"}:
            error_sources[event.source] += 1
        if first is None or event.timestamp < first:
            first = event.timestamp
        if last is None or event.timestamp > last:
            last = event.timestamp
    top = sorted(error_sources.items(), key=lambda item: (-item[1], item[0]))[:5]
    return {
        "total": total,
        "by_level": by_level,
        "by_source": dict(sorted(by_source.items())),
        "top_error_sources": [{"source": source, "count": count} for source, count in top],
        "first_time": first.isoformat() if first else None,
        "last_time": last.isoformat() if last else None,
    }
