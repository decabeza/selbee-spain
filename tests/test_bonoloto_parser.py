
import json
from pathlib import Path

import pytest

from selbee.data.bonoloto_parser import (
    parse_bonoloto_draw,
    parse_combination,
    parse_spanish_number,
)


DATA_PATH = Path("data/raw/bonoloto_20261111.json")


@pytest.fixture
def raw_draw():
    with DATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)[0]


def test_parse_spanish_number():
    assert parse_spanish_number("45.903,59") == 45903.59
    assert parse_spanish_number("2181853") == 2181853.0
    assert parse_spanish_number("0,5") == 0.5


def test_parse_combination():
    result = parse_combination(
        "14 - 21 - 34 - 36 - 37 - 42 C(19) R(0)"
    )

    assert result["numbers"] == [14, 21, 34, 36, 37, 42]
    assert result["complementary"] == 19
    assert result["reintegro"] == 0


def test_parse_combination_rejects_duplicate_numbers():
    with pytest.raises(ValueError):
        parse_combination("14 - 14 - 34 - 36 - 37 - 42 C(19) R(0)")


def test_parse_combination_rejects_invalid_number():
    with pytest.raises(ValueError):
        parse_combination("14 - 21 - 34 - 36 - 37 - 50 C(19) R(0)")


def test_parse_combination_rejects_complementary_in_main_numbers():
    with pytest.raises(ValueError):
        parse_combination("14 - 21 - 34 - 36 - 37 - 42 C(14) R(0)")


def test_parse_bonoloto_draw(raw_draw):
    result = parse_bonoloto_draw(raw_draw)

    assert result["draw_id"] == "1328301315"
    assert str(result["date"]) == "2026-11-11"
    assert result["entries"] == 4363706
    assert result["revenue_eur"] == 2181853.0
    assert result["prize_fund_eur"] == 1200019.0
    assert result["categories"][2]["winners"] == 3
    assert result["categories"][2]["prize_per_winner"] == 45903.59


def test_parse_bonoloto_draw_rejects_wrong_game(raw_draw):
    raw_draw["game_id"] = "EURO"
    with pytest.raises(ValueError):
        parse_bonoloto_draw(raw_draw)


def test_parse_bonoloto_draw_rejects_missing_fields(raw_draw):
    del raw_draw["recaudacion"]
    with pytest.raises(ValueError):
        parse_bonoloto_draw(raw_draw)
