"""
SELBEE SPAIN - Historical Combination CSV Importer

Imports historical Bonoloto combinations from CSV files.
"""

import csv
from datetime import datetime
from pathlib import Path


def parse_historical_row(row: list[str]) -> dict:
    """Parse and validate one historical CSV row."""

    if len(row) != 9:
        raise ValueError(f"Expected 9 columns, received {len(row)}")

    draw_date = datetime.strptime(row[0].strip(), "%d/%m/%Y").date()

    numbers = [int(value.strip()) for value in row[1:7]]

    if len(set(numbers)) != 6:
        raise ValueError("Main numbers must be unique")

    if any(number < 1 or number > 49 for number in numbers):
        raise ValueError("Main numbers must be between 1 and 49")

    complementary = int(row[7].strip())

    if not 1 <= complementary <= 49:
        raise ValueError("Complementary number must be between 1 and 49")

    if complementary in numbers:
        raise ValueError("Complementary number cannot be a main number")

    reintegro_value = row[8].strip()
    reintegro = int(reintegro_value) if reintegro_value else None

    if reintegro is not None and not 0 <= reintegro <= 9:
        raise ValueError("Reintegro must be between 0 and 9")

    return {
        "date": draw_date.isoformat(),
        "numbers": numbers,
        "complementary": complementary,
        "reintegro": reintegro,
    }


def inspect_historical_csv(file_path: Path) -> dict:
    """Inspect a CSV file without importing its records."""

    file_path = Path(file_path)
    records = []
    errors = []

    with file_path.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.reader(file)

        next(reader, None)  # Skip header

        for line_number, row in enumerate(reader, start=2):
            try:
                records.append(parse_historical_row(row))
            except (ValueError, IndexError) as error:
                errors.append({
                    "line": line_number,
                    "error": str(error),
                })

    dates = [record["date"] for record in records]

    return {
        "file": file_path.name,
        "records": len(records),
        "missing_reintegro": sum(
            record["reintegro"] is None for record in records
        ),
        "duplicate_dates": len(dates) - len(set(dates)),
        "first_date": min(dates) if dates else None,
        "last_date": max(dates) if dates else None,
        "errors": errors,
        "data": records,
    }

from selbee.data.database import (
    DEFAULT_DATABASE_PATH,
    save_historical_combination,
)


def import_historical_csv(
    file_path: Path,
    db_path: Path = DEFAULT_DATABASE_PATH,
) -> dict:
    """Import historical combinations from a CSV file."""

    inspection = inspect_historical_csv(file_path)

    if inspection["errors"]:
        raise ValueError(
            f"CSV contains {len(inspection['errors'])} invalid rows"
        )

    imported = 0

    for record in inspection["data"]:
        save_historical_combination(
            {
                **record,
                "source": f"lotoideas:{Path(file_path).name}",
            },
            db_path=db_path,
        )
        imported += 1

    return {
        "file": Path(file_path).name,
        "imported": imported,
    }
