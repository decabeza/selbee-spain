"""
SELBEE SPAIN - Historical Data Importer

Imports raw SELAE JSON files into the local SQLite database.
"""

import json
from pathlib import Path

from selbee.data.bonoloto_parser import parse_bonoloto_draw
from selbee.data.database import DEFAULT_DATABASE_PATH, save_draw


def import_raw_draws(
    raw_dir: Path = Path("data/raw"),
    db_path: Path = DEFAULT_DATABASE_PATH,
) -> dict:
    """
    Import all JSON draw files from a directory.

    Each file may contain one draw or a list of draws.
    Existing draw IDs are updated rather than duplicated.
    """

    raw_dir = Path(raw_dir)

    if not raw_dir.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {raw_dir}"
        )

    files = sorted(raw_dir.glob("*.json"))

    summary = {
        "files_found": len(files),
        "draws_imported": 0,
        "errors": [],
    }

    for file_path in files:
        try:
            with file_path.open(encoding="utf-8") as file:
                raw_data = json.load(file)

            if isinstance(raw_data, dict):
                raw_draws = [raw_data]
            elif isinstance(raw_data, list):
                raw_draws = raw_data
            else:
                raise ValueError(
                    "JSON must contain an object or a list of objects"
                )

            for raw_draw in raw_draws:
                normalized_draw = parse_bonoloto_draw(raw_draw)

                save_draw(
                    normalized_draw,
                    db_path=db_path,
                )

                summary["draws_imported"] += 1

        except (
            OSError,
            json.JSONDecodeError,
            ValueError,
            TypeError,
            KeyError,
        ) as error:
            summary["errors"].append({
                "file": file_path.name,
                "error": str(error),
            })

    return summary
