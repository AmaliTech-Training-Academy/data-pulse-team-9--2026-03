import os

import pytest
from datapulse.exceptions import InvalidFileException
from datasets.services.file_parser import parse_csv, parse_json


@pytest.fixture
def temp_files(tmp_path):
    files = {}

    # 1. Empty CSV
    empty_csv = tmp_path / "empty.csv"
    empty_csv.touch()
    files["empty_csv"] = str(empty_csv)

    # 2. CSV with weird delimiter and bad lines
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("col1,col2\nval1,val2\nval3,val4,bad\nval5,val6", encoding="utf-8")
    files["bad_csv"] = str(bad_csv)

    # 3. CSV with latin1
    # We'll just write it as binary
    latin_csv = tmp_path / "latin.csv"
    latin_csv.write_bytes(b"name,age\nJ\xf6rg,30\n")
    files["latin_csv"] = str(latin_csv)

    # 4. JSON wrapper
    wrapper_json = tmp_path / "wrapper.json"
    wrapper_json.write_text('{"status": "ok", "data": [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]}')
    files["wrapper_json"] = str(wrapper_json)

    # 5. Bad JSON
    bad_json = tmp_path / "bad.json"
    bad_json.write_text('{"status": "ok", "data": ')
    files["bad_json"] = str(bad_json)

    return files


def test_parse_csv_empty(temp_files):
    with pytest.raises(InvalidFileException, match="completely empty"):
        parse_csv(temp_files["empty_csv"])


def test_parse_csv_delimiter_and_skip(temp_files):
    result = parse_csv(temp_files["bad_csv"])
    # 1 header, 2 good rows, 1 bad row skipped
    assert result["row_count"] == 2
    assert result["column_count"] == 2
    assert "col1" in result["column_names"]


def test_parse_csv_encoding_fallback(temp_files):
    result = parse_csv(temp_files["latin_csv"])
    assert result["row_count"] == 1
    assert result["column_names"] == ["name", "age"]


def test_parse_json_unwrapper(temp_files):
    result = parse_json(temp_files["wrapper_json"])
    assert result["row_count"] == 2
    assert result["column_names"] == ["id", "val"]


def test_parse_json_invalid(temp_files):
    with pytest.raises(InvalidFileException, match="Invalid JSON format"):
        parse_json(temp_files["bad_json"])
