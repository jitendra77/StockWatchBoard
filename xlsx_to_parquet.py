#!/usr/bin/env python3
"""
xlsx_to_parquet.py

Convert an Excel .xlsx file to a Parquet file with explicit column coercions:
- Selected columns to datetime
- Selected columns to durations (hours/minutes/seconds)

Examples:
  Basic conversion with datetime parsing and hour/minute durations:
    python xlsx_to_parquet.py \
      --input data.xlsx --output data.parquet \
      --sheet-name Sheet1 \
      --datetime-cols created_at updated_at \
      --duration-col task_hours:h --duration-col break_minutes:m

  Using a specific datetime format for all datetime columns:
    python xlsx_to_parquet.py \
      --input data.xlsx --output data.parquet \
      --datetime-cols start_time end_time \
      --datetime-format "%Y-%m-%d %H:%M:%S"

  Handling timezone localization for datetime columns:
    python xlsx_to_parquet.py \
      --input data.xlsx --output data.parquet \
      --datetime-cols timestamp \
      --timezone UTC

Notes:
- Duration units supported: h, hr, hrs, hour, hours; m, min, mins, minute, minutes; s, sec, secs, second, seconds
- If duration column values are strings like "01:30:00", they will be parsed directly.
- Writing uses pyarrow to preserve dtypes (including timedelta64[ns]).
"""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert an .xlsx file to .parquet with explicit datetime and duration column handling.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--input", required=True, help="Path to input .xlsx file")
    parser.add_argument("--output", required=True, help="Path to output .parquet file")
    parser.add_argument(
        "--sheet-name",
        default=0,
        help=(
            "Sheet name or index to read from the Excel file. "
            "Use integer index for position (0-based) or string for sheet name."
        ),
    )
    parser.add_argument(
        "--header",
        type=int,
        default=0,
        help="Row (0-indexed) to use as the column names. Pass None-like (e.g., -1) for no header.",
    )
    parser.add_argument(
        "--datetime-cols",
        nargs="*",
        default=[],
        help="Column names to convert to datetime",
    )
    parser.add_argument(
        "--datetime-format",
        default=None,
        help=(
            "Optional strptime-compatible format string to apply to all datetime columns. "
            "If omitted, pandas will infer formats."
        ),
    )
    parser.add_argument(
        "--timezone",
        default=None,
        help=(
            "Optional timezone to localize naive datetimes (e.g., 'UTC', 'Europe/Berlin'). "
            "If provided, each datetime column will be localized to this timezone if naive."
        ),
    )
    parser.add_argument(
        "--duration-col",
        action="append",
        default=[],
        metavar="NAME:UNIT",
        help=(
            "Add a duration column specification as 'column_name:unit'. "
            "Units: h/hr/hrs/hour/hours, m/min/mins/minute/minutes, s/sec/secs/second/seconds. "
            "Pass multiple times for multiple columns."
        ),
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Whether to preserve the DataFrame index in the parquet output.",
    )
    parser.add_argument(
        "--engine",
        default="fastparquet",
        choices=["pyarrow", "fastparquet"],
        help="Parquet engine to use when writing.",
    )
    parser.add_argument(
        "--na-values",
        nargs="*",
        default=["", "NA", "NaN", "nan", "NULL", "null"],
        help="Additional strings to recognize as NA/NaN when reading Excel.",
    )
    parser.add_argument(
        "--encoding",
        default=None,
        help="Optional encoding override when reading the Excel file.",
    )
    parser.add_argument(
        "--sheet-rows",
        type=int,
        default=None,
        help="Optionally limit number of rows read from the sheet.",
    )

    return parser.parse_args(argv)


def parse_duration_specs(specs: Iterable[str]) -> Dict[str, str]:
    unit_aliases = {
        "h": "h",
        "hr": "h",
        "hrs": "h",
        "hour": "h",
        "hours": "h",
        "m": "m",
        "min": "m",
        "mins": "m",
        "minute": "m",
        "minutes": "m",
        "s": "s",
        "sec": "s",
        "secs": "s",
        "second": "s",
        "seconds": "s",
    }

    result: Dict[str, str] = {}
    for spec in specs:
        if ":" not in spec:
            raise ValueError(
                f"Invalid --duration-col '{spec}'. Expected format 'name:unit', e.g., 'task_hours:h'"
            )
        name, unit = spec.split(":", 1)
        unit_key = unit.strip().lower()
        if unit_key not in unit_aliases:
            raise ValueError(
                f"Unsupported duration unit '{unit}'. Use one of h/hr/hrs/hour/hours, m/min/mins/minute/minutes, s/sec/secs/second/seconds"
            )
        result[name.strip()] = unit_aliases[unit_key]
    return result


def coerce_datetime_columns(
    frame: pd.DataFrame,
    column_names: Iterable[str],
    dt_format: Optional[str],
    timezone: Optional[str],
) -> pd.DataFrame:
    for column_name in column_names:
        if column_name not in frame.columns:
            print(f"[warn] datetime column '{column_name}' not found; skipping", file=sys.stderr)
            continue

        coerced = pd.to_datetime(frame[column_name], format=dt_format, errors="coerce")

        if timezone:
            # Localize naive datetimes only; if already tz-aware, convert to target tz
            try:
                if coerced.dt.tz is None:
                    coerced = coerced.dt.tz_localize(timezone)
                else:
                    coerced = coerced.dt.tz_convert(timezone)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"[warn] failed to localize/convert timezone for column '{column_name}': {exc}",
                    file=sys.stderr,
                )

        frame[column_name] = coerced
    return frame


def coerce_duration_columns(
    frame: pd.DataFrame,
    name_to_unit: Dict[str, str],
) -> pd.DataFrame:
    for column_name, unit in name_to_unit.items():
        if column_name not in frame.columns:
            print(f"[warn] duration column '{column_name}' not found; skipping", file=sys.stderr)
            continue

        series = frame[column_name]

        # If values look like HH:MM:SS or similar strings, parse directly without unit
        # Otherwise, assume numeric values represent the provided unit
        try:
            # Detect string-like durations
            if series.dtype == object:
                parsed = pd.to_timedelta(series, errors="coerce")
            else:
                parsed = pd.to_timedelta(series, unit=unit, errors="coerce")
        except Exception:
            # Fallback: attempt generic parsing
            parsed = pd.to_timedelta(series, errors="coerce")

        frame[column_name] = parsed
    return frame


def read_excel_safely(
    input_path: str,
    sheet_name: object,
    header: Optional[int],
    na_values: List[str],
    nrows: Optional[int],
    encoding: Optional[str],
) -> pd.DataFrame:
    header_arg: Optional[int]
    if header is None or header < 0:
        header_arg = None
    else:
        header_arg = header

    # engine left to pandas (openpyxl for .xlsx)
    frame = pd.read_excel(
        input_path,
        sheet_name=sheet_name,
        header=header_arg,
        na_values=na_values,
        nrows=nrows,
        engine=None,
    )
    if isinstance(frame, dict):
        # If a dict was returned, user likely passed sheet_name=None; pick the first sheet deterministically
        first_key = sorted(frame.keys())[0]
        frame = frame[first_key]
    return frame


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    try:
        duration_specs = parse_duration_specs(args.duration_col)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    try:
        df = read_excel_safely(
            input_path=args.input,
            sheet_name=args.sheet_name,
            header=args.header,
            na_values=args.na_values,
            nrows=args.sheet_rows,
            encoding=args.encoding,
        )
    except FileNotFoundError:
        print(f"[error] input file not found: {args.input}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"[error] failed to read Excel: {exc}", file=sys.stderr)
        return 2

    if args.datetime_cols:
        df = coerce_datetime_columns(df, args.datetime_cols, args.datetime_format, args.timezone)

    if duration_specs:
        df = coerce_duration_columns(df, duration_specs)

    # Write parquet
    try:
        df.to_parquet(args.output, index=args.index, engine=args.engine)
    except Exception as exc:  # noqa: BLE001
        print(
            f"[error] failed to write parquet with engine '{args.engine}': {exc}",
            file=sys.stderr,
        )
        return 2

    print(f"[ok] wrote parquet -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

