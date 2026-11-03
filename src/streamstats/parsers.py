"""Потоковое чтение CSV и JSONL."""

import csv
import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from .errors import InputError, InvalidEventError, UnsupportedFormatError
from .models import Event

logger = logging.getLogger(__name__)


@dataclass
class ParseStats:
    """Число пропущенных записей."""

    skipped: int = 0


def _invalid(path: Path, line: int, error: Exception, skip: bool, stats: ParseStats) -> None:
    """Остановить обработку или зарегистрировать пропуск."""
    message = f"{path}, строка {line}: {error}"
    if not skip:
        raise InputError(message) from error
    logger.warning("%s", message)
    stats.skipped += 1


def parse_jsonl(path: Path, skip: bool, stats: ParseStats) -> Iterator[Event]:
    """Читать JSONL по строкам."""
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise InvalidEventError("ожидался JSON-объект")
                event = Event.from_mapping(record)
            except (json.JSONDecodeError, InvalidEventError) as error:
                _invalid(path, line_number, error, skip, stats)
                continue
            yield event


def parse_csv(path: Path, skip: bool, stats: ParseStats) -> Iterator[Event]:
    """Читать CSV по записям."""
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        try:
            fields = reader.fieldnames
        except csv.Error as error:
            raise InputError(f"{path}, строка {reader.line_num}: {error}") from error
        if fields is None:
            return
        required = {"timestamp", "level", "source", "message"}
        if len(fields) != len(set(fields)) or not required.issubset(fields):
            raise InputError(f"{path}, строка 1: неверный заголовок CSV")
        while True:
            line_number = reader.line_num + 1
            try:
                record = next(reader)
            except StopIteration:
                break
            except csv.Error as error:
                _invalid(path, line_number, error, skip, stats)
                continue
            try:
                if None in record:
                    raise InvalidEventError("лишние поля CSV")
                event = Event.from_mapping(record)
            except InvalidEventError as error:
                _invalid(path, line_number, error, skip, stats)
                continue
            yield event


def parse_files(paths: list[Path], format_name: str, skip: bool, stats: ParseStats) -> Iterator[Event]:
    """Последовательно читать все входные файлы."""
    parsers = {"csv": parse_csv, "jsonl": parse_jsonl}
    if format_name not in parsers:
        raise UnsupportedFormatError(f"неподдерживаемый формат: {format_name}")
    for path in paths:
        yield from parsers[format_name](path, skip, stats)
