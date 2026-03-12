"""Tests for the extract module."""

import pandas as pd
from unittest.mock import patch, MagicMock
from pipeline.etl.extract import extract


def test_extract_returns_dataframe():
    """extract() should return a DataFrame."""
    mock_engine = MagicMock()
    mock_df = pd.DataFrame({"id": [1, 2], "dataset_id": [10, 20]})

    with patch("pipeline.etl.extract.pd.read_sql", return_value=mock_df):
        result = extract(mock_engine)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2


def test_extract_empty_table():
    """extract() should handle empty results gracefully."""
    mock_engine = MagicMock()
    empty_df = pd.DataFrame()

    with patch("pipeline.etl.extract.pd.read_sql", return_value=empty_df):
        result = extract(mock_engine)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
