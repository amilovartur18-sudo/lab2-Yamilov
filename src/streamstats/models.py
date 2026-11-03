"""Модель одного события и проверка его полей."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from .errors import InvalidEventError, InvalidTimestampError

LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


@dataclass(frozen=True)
class Event:
    """Проверенное событие из входного файла."""

    timestamp: datetime
    level: str
    source: str
    message: str

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> "Event":
        """Проверить поля записи и создать событие."""
        timestamp = values.get("timestamp")
        level = values.get("level")
        source = values.get("source")
        message = values.get("message")

        if not isinstance(timestamp, str):
            raise InvalidTimestampError("поле timestamp должно быть строкой ISO 8601")
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise InvalidTimestampError("неверный формат поля timestamp") from exc

        if parsed_timestamp.tzinfo is None:
            parsed_timestamp = parsed_timestamp.replace(tzinfo=UTC)

        if not isinstance(level, str) or level not in LEVELS:
            raise InvalidEventError("неверное поле level")
        if not isinstance(source, str) or not source.strip():
            raise InvalidEventError("поле source должно быть непустой строкой")
        if not isinstance(message, str):
            raise InvalidEventError("поле message должно быть строкой")

        return cls(parsed_timestamp, level, source, message)
