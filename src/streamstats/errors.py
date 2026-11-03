"""Ошибки анализатора событий."""


class StreamStatsError(Exception):
    """Общая ошибка анализатора."""


class InvalidEventError(StreamStatsError):
    """Событие содержит отсутствующие или неверные поля."""


class InvalidTimestampError(InvalidEventError):
    """Временная метка события имеет неверный формат."""


class UnsupportedFormatError(StreamStatsError):
    """Формат файла не поддерживается."""


class ConfigurationError(StreamStatsError):
    """Неверные параметры запуска."""


class InputError(StreamStatsError):
    """Ошибка чтения входной записи."""
