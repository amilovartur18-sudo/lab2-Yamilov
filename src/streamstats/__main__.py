"""Запуск анализатора из терминала."""

import argparse
import logging
import sys
from pathlib import Path

from .analysis import analyze
from .errors import ConfigurationError, StreamStatsError
from .parsers import ParseStats, parse_files
from .report import write_report


def build_parser() -> argparse.ArgumentParser:
    """Создать разбор аргументов."""
    parser = argparse.ArgumentParser(description="Потоковый анализатор событий")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze_parser = commands.add_parser("analyze", help="проанализировать файлы")
    analyze_parser.add_argument("inputs", nargs="+", type=Path)
    analyze_parser.add_argument("--format", required=True, choices=("csv", "jsonl"))
    analyze_parser.add_argument("--output", type=Path, default=Path("report.json"))
    analyze_parser.add_argument("--skip-invalid", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Запустить анализ и вернуть код завершения."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    try:
        output = args.output.resolve()
        for path in args.inputs:
            if path.resolve() == output or (output.exists() and path.exists() and path.samefile(output)):
                raise ConfigurationError("выходной файл совпадает с входным")
        stats = ParseStats()
        result = analyze(parse_files(args.inputs, args.format, args.skip_invalid, stats))
        result["skipped"] = stats.skipped
        write_report(result, args.output)
    except (StreamStatsError, OSError, UnicodeError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
