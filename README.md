## xlsx_to_parquet CLI

Convert an Excel `.xlsx` file to a Parquet file, with options to coerce specific columns to datetimes and durations (hours/minutes/seconds).

### Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Usage

```bash
python xlsx_to_parquet.py \
  --input input.xlsx \
  --output output.parquet \
  --sheet-name Sheet1 \
  --datetime-cols created_at updated_at \
  --datetime-format "%Y-%m-%d %H:%M:%S" \
  --timezone UTC \
  --duration-col task_hours:h \
  --duration-col break_minutes:m
```

- **Datetime columns**: pass names via `--datetime-cols`. Optionally set `--datetime-format` and `--timezone`.
- **Duration columns**: pass one or more `--duration-col name:unit` entries. Units supported: `h/hr/hrs/hour/hours`, `m/min/mins/minute/minutes`, `s/sec/secs/second/seconds`.
- If a duration cell is a string like `"01:30:00"`, it's parsed directly via `pandas.to_timedelta`.

View all options:

```bash
python xlsx_to_parquet.py --help
```

