"""Сохранение JSON-отчёта."""

import json
from pathlib import Path


def write_report(report: dict[str, object], output: Path) -> None:
    """Записать отчёт в UTF-8."""
    with output.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")
