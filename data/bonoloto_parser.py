"""
SELBEE SPAIN - Bonoloto Data Parser

Parses and validates raw Bonoloto JSON results from SELAE.
"""

import re
from datetime import datetime


def parse_spanish_number(value: str) -> float:
    """Convert a Spanish-formatted numeric string into a float."""

    if not isinstance(value, str):
        raise TypeError("Numeric values must be strings")

    normalized = value.strip().replace(".", "").replace(",", ".")

    try:
        return float(normalized)
    except ValueError as error:
        raise ValueError(f"Invalid Spanish numeric value: {value}") from error


def parse_combination(value: str) -> dict:
    """Extract the six winning numbers, complementary number and reintegro."""

    if not isinstance(value, str):
        raise TypeError("Combination must be a string")

    match = re.fullmatch(
        r"\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*"
        r"(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})"
        r"\s+C\((\d{1,2})\)\s+R\((\d)\)\s*",
        value,
    )

    if not match:
        raise ValueError(f"Invalid Bonoloto combination: {value}")

    numbers = [int(number) for number in match.groups()[:6]]
    complementary = int(match.group(7))
    reintegro = int(match.group(8))

    if len(set(numbers)) != 6:
        raise ValueError("Winning numbers must be unique")

    if any(number < 1 or number > 49 for number in numbers):
        raise ValueError("Winning numbers must be between 1 and 49")

    if complementary < 1 or complementary > 49:
        raise ValueError("Complementary number must be between 1 and 49")

    if complementary in numbers:
        raise ValueError("Complementary number cannot be a winning number")

    return {
        "numbers": numbers,
        "complementary": complementary,
        "reintegro": reintegro,
    }


def parse_bonoloto_draw(raw: dict) -> dict:
    """Normalize one raw SELAE Bonoloto draw."""

    required_fields = {
        "fecha_sorteo",
        "id_sorteo",
        "game_id",
        "combinacion",
        "apuestas",
        "recaudacion",
        "premios",
        "fondo_bote",
        "escrutinio",
    }

    missing_fields = required_fields - raw.keys()

    if missing_fields:
        raise ValueError(f"Missing required fields: {sorted(missing_fields)}")

    if raw["game_id"] != "BONO":
        raise ValueError("Invalid game ID: expected BONO")

    try:
        draw_date = datetime.strptime(
            raw["fecha_sorteo"],
            "%Y-%m-%d %H:%M:%S",
        )
    except ValueError as error:
        raise ValueError("Invalid draw date format") from error

    if not isinstance(raw["escrutinio"], list):
        raise TypeError("Prize scrutiny must be a list")

    category_results = {}

    for item in raw["escrutinio"]:
        category = item["categoria"]

        if category in category_results:
            raise ValueError(f"Duplicate prize category: {category}")

        category_results[category] = {
            "description": item["tipo"].strip(),
            "prize_per_winner": parse_spanish_number(item["premio"]),
            "winners": int(item["ganadores"]),
        }

    if set(category_results) != {1, 2, 3, 4, 5, 6}:
        raise ValueError("Expected six Bonoloto prize categories")

    return {
        "draw_id": str(raw["id_sorteo"]),
        "date": draw_date.date(),
        "game_id": raw["game_id"],
        "combination": parse_combination(raw["combinacion"]),
        "entries": int(raw["apuestas"]),
        "revenue_eur": parse_spanish_number(raw["recaudacion"]),
        "prize_fund_eur": parse_spanish_number(raw["premios"]),
        "jackpot_rollover_eur": parse_spanish_number(raw["fondo_bote"]),
        "categories": category_results,
    }
