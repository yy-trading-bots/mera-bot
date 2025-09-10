import csv
from pathlib import Path
import pytest

from utils.file_utils import FileUtils
import utils.file_utils as file_utils_module
from data.market_snapshot import MarketSnapshot


def read_csv(path: Path):
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_ensure_parent_creates_directory(tmp_path: Path):
    target = tmp_path / "nested" / "deeper" / "out.csv"
    assert not target.parent.exists()
    FileUtils._ensure_parent(target)
    assert target.parent.exists()
    assert target.parent.is_dir()


def test_is_empty_file_missing_and_empty_and_nonempty(tmp_path: Path):
    missing = tmp_path / "missing.csv"
    assert FileUtils._is_empty_file(missing) is True

    empty = tmp_path / "empty.csv"
    empty.touch()
    assert FileUtils._is_empty_file(empty) is True

    nonempty = tmp_path / "nonempty.csv"
    nonempty.write_text("x", encoding="utf-8")
    assert FileUtils._is_empty_file(nonempty) is False


def test_append_csv_writes_header_then_rows(tmp_path: Path):
    out = tmp_path / "data" / "results.csv"

    row1 = ["2025-08-29 00:00", "WIN", "LONG", 100.0, 1.0, -2.0, 200.0, 55.0]
    row2 = ["2025-08-29 01:00", "LOSS", "SHORT", 90.0, -0.5, 0.8, 198.0, 48.0]

    FileUtils._append_csv(out, row1)
    FileUtils._append_csv(out, row2)

    rows = read_csv(out)
    assert rows[0] == FileUtils._HEADER
    assert rows[1] == [
        "2025-08-29 00:00",
        "WIN",
        "LONG",
        "100.0",
        "1.0",
        "-2.0",
        "200.0",
        "55.0",
    ]
    assert rows[2] == [
        "2025-08-29 01:00",
        "LOSS",
        "SHORT",
        "90.0",
        "-0.5",
        "0.8",
        "198.0",
        "48.0",
    ]
    assert len(rows) == 3


def test_save_result_appends_snapshot_rows_and_header_once(tmp_path: Path):
    out = tmp_path / "r" / "results.csv"

    s1 = MarketSnapshot(
        date="2025-08-29 00:00",
        price=100.0,
        macd_12=1.0,
        macd_26=-2.0,
        ema_100=200.0,
        rsi_6=55.0,
    )
    s2 = MarketSnapshot(
        date="2025-08-29 01:00",
        price=90.0,
        macd_12=-0.5,
        macd_26=0.8,
        ema_100=198.0,
        rsi_6=48.0,
    )

    FileUtils.save_result(out, result="WIN", position="LONG", snapshot=s1)
    FileUtils.save_result(out, result="LOSS", position="SHORT", snapshot=s2)

    rows = read_csv(out)
    assert rows[0] == FileUtils._HEADER
    assert rows[1] == [
        "2025-08-29 00:00",
        "WIN",
        "LONG",
        "100.0",
        "1.0",
        "-2.0",
        "200.0",
        "55.0",
    ]
    assert rows[2] == [
        "2025-08-29 01:00",
        "LOSS",
        "SHORT",
        "90.0",
        "-0.5",
        "0.8",
        "198.0",
        "48.0",
    ]
    assert len(rows) == 3


def test_read_toml_file_success(tmp_path: Path):
    toml_file = tmp_path / "config.toml"
    toml_file.write_text(
        """
        [api]
        public_key = "PUB"
        secret_key = "SEC"
        [runtime]
        sleep_duration = 5
        """,
        encoding="utf-8",
    )
    data = FileUtils.read_toml_file(toml_file)
    assert isinstance(data, dict)
    assert data["api"]["public_key"] == "PUB"
    assert data["runtime"]["sleep_duration"] == 5


def test_read_toml_file_not_found(tmp_path: Path):
    missing = tmp_path / "nope.toml"
    with pytest.raises(FileNotFoundError) as ei:
        FileUtils.read_toml_file(missing)
    assert "TOML file not found" in str(ei.value)


def test_read_toml_file_parse_error_raises_valueerror(tmp_path: Path):
    invalid = tmp_path / "bad.toml"
    invalid.write_text('key = "unterminated', encoding="utf-8")
    with pytest.raises(ValueError) as ei:
        FileUtils.read_toml_file(invalid)
    assert "Failed to parse TOML file" in str(ei.value)


def test_read_toml_file_non_dict_top_level_raises_valueerror(
    tmp_path: Path, monkeypatch
):
    toml_file = tmp_path / "weird.toml"
    toml_file.write_text("anything = 1", encoding="utf-8")

    def fake_load(_fp):
        return ["not-a-dict"]

    monkeypatch.setattr(file_utils_module.tomllib, "load", lambda fp: fake_load(fp))

    with pytest.raises(ValueError) as ei:
        FileUtils.read_toml_file(toml_file)
    assert "Top-level TOML content must be a table/object." in str(ei.value)
