"""Проверки модели события."""

import unittest
from datetime import UTC, datetime

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import Event


class EventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.values: dict[str, object] = {
            "timestamp": "2026-11-03T09:30:00",
            "level": "ERROR",
            "source": "сервер",
            "message": "Ошибка подключения",
        }

    def test_valid_event(self) -> None:
        event = Event.from_mapping(self.values)
        self.assertEqual(event.timestamp, datetime(2026, 11, 3, 9, 30, tzinfo=UTC))
        self.assertEqual(event.source, "сервер")

    def test_invalid_timestamp(self) -> None:
        self.values["timestamp"] = "не дата"
        with self.assertRaises(InvalidTimestampError):
            Event.from_mapping(self.values)

    def test_invalid_level(self) -> None:
        self.values["level"] = "NOTICE"
        with self.assertRaises(InvalidEventError):
            Event.from_mapping(self.values)

    def test_missing_message(self) -> None:
        del self.values["message"]
        with self.assertRaises(InvalidEventError):
            Event.from_mapping(self.values)

    def test_blank_source(self) -> None:
        self.values["source"] = "  "
        with self.assertRaises(InvalidEventError):
            Event.from_mapping(self.values)
