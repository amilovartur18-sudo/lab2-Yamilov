# Лабораторная работа 2 — streamstats

Программа читает события CSV и JSONL и создаёт статистический JSON-отчёт.

## Установка

Требуется Python 3.12 или новее и uv:

```bash
uv sync
```

## Запуск

```bash
uv run python -m streamstats --help
uv run python -m streamstats analyze events.csv --format csv --output report.json
uv run python -m streamstats analyze first.jsonl second.jsonl --format jsonl --skip-invalid
```

Без `--output` отчёт записывается в `report.json`. Все входные файлы одного запуска должны соответствовать выбранному формату. Исходный файл нельзя использовать в качестве файла отчёта.

CSV содержит заголовок `timestamp,level,source,message`; в JSONL каждая строка — JSON-объект с теми же полями. `timestamp` задаётся в ISO 8601, `level` — DEBUG, INFO, WARNING, ERROR или CRITICAL, `source` — непустая строка, `message` — строка. Время без указанного часового пояса считается UTC.

По умолчанию программа останавливается на ошибочной записи, показывает файл и строку, возвращает код 2. С `--skip-invalid` запись пропускается, в stderr выводится предупреждение, а в отчёте увеличивается `skipped`. Неверный заголовок CSV считается ошибкой файла.

Отчёт содержит `total`, `by_level`, `by_source`, `top_error_sources`, `first_time`, `last_time`, `skipped`. При равном числе ошибок источники сортируются по имени. Пустой файл даёт нулевые счётчики и `null` для дат.

Файлы читаются по одной записи. Память расходуется на текущую запись и счётчики для разных источников и уровней, а не на все события.

## Проверка

```bash
uv run python -m pytest
uv run python -m pytest --cov=streamstats --cov-report=term-missing
uv run ruff check .
```

Команда с `--cov` показывает покрытие кода тестами, включая запуск CLI в отдельных процессах. Строки без покрытия перечислены в колонке `Missing`.
