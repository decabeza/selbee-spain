import json

from selbee.data.importer import import_raw_draws
from selbee.data.database import count_draws


def test_import_raw_draws(tmp_path):
    raw_dir = tmp_path / "raw"
    db_path = tmp_path / "test.db"

    raw_dir.mkdir()

    source_path = "data/raw/bonoloto_20261111.json"

    with open(source_path, encoding="utf-8") as file:
        raw_data = json.load(file)

    test_file = raw_dir / "bonoloto_test.json"

    test_file.write_text(
        json.dumps(raw_data, ensure_ascii=False),
        encoding="utf-8",
    )

    result = import_raw_draws(
        raw_dir=raw_dir,
        db_path=db_path,
    )

    assert result["files_found"] == 1
    assert result["draws_imported"] == 1
    assert result["errors"] == []
    assert count_draws(db_path) == 1


def test_import_raw_draws_does_not_duplicate_records(tmp_path):
    raw_dir = tmp_path / "raw"
    db_path = tmp_path / "test.db"

    raw_dir.mkdir()

    source_path = "data/raw/bonoloto_20261111.json"

    with open(source_path, encoding="utf-8") as file:
        raw_data = json.load(file)

    test_file = raw_dir / "bonoloto_test.json"

    test_file.write_text(
        json.dumps(raw_data),
        encoding="utf-8",
    )

    import_raw_draws(raw_dir=raw_dir, db_path=db_path)
    import_raw_draws(raw_dir=raw_dir, db_path=db_path)

    assert count_draws(db_path) == 1
