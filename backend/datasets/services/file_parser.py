"""File parsing service - IMPLEMENTED."""

import pandas as pd


def parse_csv(file_path: str) -> dict:
    """Parse a CSV file and return metadata."""
    df = pd.read_csv(file_path)
    return {
        "dataframe": df,
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }


def parse_json(file_path: str) -> dict:
    """Parse a JSON file and return metadata."""
    df = pd.read_json(file_path)
    return {
        "dataframe": df,
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
