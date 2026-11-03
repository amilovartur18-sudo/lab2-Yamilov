"""Проверки форматов и запуска CLI."""

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from streamstats.analysis import analyze
from streamstats.parsers import ParseStats, parse_csv, parse_jsonl

SRC = Path(__file__).resolve().parents[1] / "src"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Запустить пакет в отдельном процессе."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    return subprocess.run(
        [sys.executable, "-m", "streamstats", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


class IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.records = [
            {"timestamp": "2026-01-01T10:00:00Z", "level": "ERROR", "source": "сайт", "message": "Ошибка, сеть"},
            {"timestamp": "2026-01-01T12:00:00+02:00", "level": "CRITICAL", "source": "база", "message": "Нет связи"},
        ]

    def jsonl(self, name: str, records: list[dict[str, str]]) -> Path:
        path = self.root / name
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
        return path

    def test_csv_and_jsonl_match(self) -> None:
        csv_path = self.root / "events.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["timestamp", "level", "source", "message"])
            writer.writeheader()
            writer.writerows(self.records)
        json_path = self.jsonl("events.jsonl", self.records)
        csv_result = analyze(parse_csv(csv_path, False, ParseStats()))
        json_result = analyze(parse_jsonl(json_path, False, ParseStats()))
        self.assertEqual(csv_result, json_result)
        self.assertEqual(csv_result["total"], 2)
        self.assertEqual(csv_result["top_error_sources"][0]["source"], "база")

    def test_empty_files(self) -> None:
        for fmt in ("csv", "jsonl"):
            with self.subTest(fmt=fmt):
                path = self.root / f"empty.{fmt}"
                path.write_text("", encoding="utf-8")
                output = self.root / "report.json"
                result = run_cli("analyze", str(path), "--format", fmt, "--output", str(output))
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(report["total"], 0)
                self.assertIsNone(report["first_time"])

    def test_jsonl_bad_line_strict_and_skip(self) -> None:
        path = self.jsonl("bad.jsonl", [self.records[0]] * 6)
        with path.open("a", encoding="utf-8") as file:
            file.write("{bad json}\n")
            file.write(json.dumps(self.records[1], ensure_ascii=False) + "\n")
        output = self.root / "report.json"
        args = ("analyze", str(path), "--format", "jsonl", "--output", str(output))
        result = run_cli(*args)
        self.assertEqual(result.returncode, 2)
        self.assertIn("строка 7", result.stderr)
        self.assertFalse(output.exists())
        result = run_cli(*args, "--skip-invalid")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARNING", result.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual((report["total"], report["skipped"]), (7, 1))
        self.assertIn("сайт", output.read_text(encoding="utf-8"))

    def test_csv_invalid_date_and_skip(self) -> None:
        path = self.root / "bad.csv"
        path.write_text("timestamp,level,source,message\nwrong,INFO,a,x\n2026-01-01,INFO,b,y\n", encoding="utf-8")
        output = self.root / "out.json"
        args = ("analyze", str(path), "--format", "csv", "--output", str(output))
        strict = run_cli(*args)
        self.assertEqual(strict.returncode, 2)
        self.assertIn("строка 2", strict.stderr)
        self.assertIn("timestamp", strict.stderr)
        skipped = run_cli(*args, "--skip-invalid")
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual((report["total"], report["skipped"]), (1, 1))

    def test_multiple_files_and_input_preserved(self) -> None:
        first = self.jsonl("first.jsonl", [self.records[0]])
        second = self.jsonl("second.jsonl", [self.records[1]])
        before = first.read_bytes()
        output = self.root / "out.json"
        result = run_cli("analyze", str(first), str(second), "--format", "jsonl", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["total"], 2)
        blocked = run_cli("analyze", str(first), "--format", "jsonl", "--output", str(first))
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(first.read_bytes(), before)

    def test_csv_multiline_record_reports_physical_line(self) -> None:
        path = self.root / "multiline.csv"
        path.write_text('timestamp,level,source,message\n2026-01-01,INFO,a,"line 1\nline 2"\nbad,INFO,b,x\n', encoding="utf-8")
        result = run_cli("analyze", str(path), "--format", "csv")
        self.assertEqual(result.returncode, 2)
        self.assertIn("строка 4", result.stderr)

    def test_help(self) -> None:
        self.assertEqual(run_cli("--help").returncode, 0)
