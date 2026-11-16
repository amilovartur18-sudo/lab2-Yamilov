# Лабораторная работа 2 — streamstats

Программа читает события CSV и JSONL и создаёт статистический JSON-отчёт.

## Установка

Требуется Python 3.12 или новее и Git. Склонируйте репозиторий и перейдите в его папку:

```bash
git clone https://github.com/amilovartur18-sudo/lab2-Yamilov.git
cd lab2-Yamilov
```

Создайте виртуальное окружение, активируйте его и установите пакет проекта:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Для запуска тестов и проверки кода установите дополнительные инструменты:

```bash
python -m pip install -r requirements.txt -r requirements-tests.txt
```

## Запуск

Выполняйте команды из папки проекта. Справка:

```bash
python -m streamstats --help
```

Анализ примера CSV и просмотр отчёта:

```bash
python -m streamstats analyze events.csv --format csv --output report.json
cat report.json
```

Анализ двух примеров JSONL и просмотр отчёта:

```bash
python -m streamstats analyze examples/first.jsonl examples/second.jsonl --format jsonl --skip-invalid
cat report.json
```

После успешного анализа программа записывает отчёт в файл и ничего не печатает в терминале. В обоих примерах отчёт сохраняется в `report.json`; следующий запуск перезапишет этот файл. Используйте `--output другое_имя.json`, чтобы сохранить отчёты отдельно.

Для своих данных замените пути к примерам на пути к своим файлам.

Без `--output` отчёт записывается в `report.json`. Все входные файлы одного запуска должны соответствовать выбранному формату. Исходный файл нельзя использовать в качестве файла отчёта.

CSV содержит заголовок `timestamp,level,source,message`; в JSONL каждая строка — JSON-объект с теми же полями. `timestamp` задаётся в ISO 8601, `level` — DEBUG, INFO, WARNING, ERROR или CRITICAL, `source` — непустая строка, `message` — строка. Время без указанного часового пояса считается UTC.

По умолчанию программа останавливается на ошибочной записи, показывает файл и строку, возвращает код 2. С `--skip-invalid` запись пропускается, в stderr выводится предупреждение, а в отчёте увеличивается `skipped`. Неверный заголовок CSV считается ошибкой файла.

Отчёт содержит `total`, `by_level`, `by_source`, `top_error_sources`, `first_time`, `last_time`, `skipped`. При равном числе ошибок источники сортируются по имени. Пустой файл даёт нулевые счётчики и `null` для дат.

Файлы читаются по одной записи. Память расходуется на текущую запись и счётчики для разных источников и уровней, а не на все события.

## Проверка

```bash
python -m pytest
python -m pytest --cov=streamstats --cov-report=term-missing
ruff check .
```

Команда с `--cov` показывает покрытие кода тестами, включая запуск CLI в отдельных процессах. Строки без покрытия перечислены в колонке `Missing`.

## Подготовка к защите

Все команды ниже выполняются в папке проекта с активированным окружением `.venv`.

### Показать работу с CSV

```bash
python -m streamstats analyze events.csv --format csv --output report_csv.json
cat report_csv.json
```

В файле три события, поэтому в отчёте `total: 3`. У источника `database` два события, которые учитываются в топе ошибок: одно `ERROR` и одно `CRITICAL`.

### Показать работу с JSONL и несколькими файлами

```bash
python -m streamstats analyze examples/first.jsonl --format jsonl --output report_one.json
cat report_one.json
```

В первом файле два события. Теперь передадим оба файла за один запуск:

```bash
python -m streamstats analyze examples/first.jsonl examples/second.jsonl --format jsonl --output report_combined.json
cat report_combined.json
```

В общем отчёте `total: 3`: два события из первого файла и одно из второго. За один запуск все входные файлы должны иметь выбранный формат.

### Добавить и удалить источник в данных

Источник — значение поля `source`; отдельного списка допустимых источников нет. Создадим временную копию входного файла, чтобы не менять пример из репозитория:

```bash
demo_dir=$(mktemp -d)
cp examples/first.jsonl "$demo_dir/events.jsonl"
nano "$demo_dir/events.jsonl"
```

В редакторе замените `website` на новый источник, например `mobile_app`. Сохраните файл: Ctrl+O, Enter; выйдите: Ctrl+X. Затем запустите анализ:

```bash
python -m streamstats analyze "$demo_dir/events.jsonl" --format jsonl --output "$demo_dir/report.json"
cat "$demo_dir/report.json"
```

В `by_source` появится `mobile_app`, а `website` исчезнет: в этой копии его больше нет. Программа принимает любое непустое название источника. Если преподаватель попросит изменить **уровень**, а не источник, допустимые уровни находятся в `LEVELS` файла `src/streamstats/models.py`.

### Где показать чтение и анализ

- `src/streamstats/parsers.py`: `parse_jsonl` читает файл в цикле `for line_number, line in enumerate(file, 1)`, а `yield event` передаёт по одному событию.
- В том же файле `parse_csv` использует `csv.DictReader` и `next(reader)` для последовательного чтения CSV-записей. Одна CSV-запись при необходимости может занимать несколько строк.
- `src/streamstats/analysis.py`: функция `analyze` проходит по событиям и обновляет счётчики, не сохраняя все события в списке.

Такое чтение позволяет не загружать весь файл в память. Дополнительная память зависит от текущей записи и числа разных источников, для которых хранятся счётчики и строится топ.

### Показать тесты, Ruff и покрытие

```bash
python -m pytest
ruff check .
python -m pytest --cov=streamstats --cov-report=term-missing
```

`pytest` запускает тесты, Ruff проверяет код, а отчёт покрытия показывает, какие строки выполнялись во время тестов. Если инструменты не установлены, сначала выполните команды установки из раздела «Установка».
