"""File parsing service - IMPLEMENTED."""

import csv
import json

import pandas as pd
from datapulse.exceptions import InvalidFileException


def parse_csv(file_path: str) -> dict:
    """Parse a CSV file and return metadata."""
    df = None
    try:
        # Check if file is empty first
        with open(file_path, "rb") as f:
            if not f.read(1):
                raise InvalidFileException("The uploaded file is completely empty.")

        # Try to explicitly sniff the delimiter
        delimiter = ","
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sample = f.read(4096)
                if sample:
                    sniffer = csv.Sniffer()
                    dialect = sniffer.sniff(sample, delimiters=",;\t|")
                    delimiter = dialect.delimiter
        except Exception:
            pass  # fallback to pandas auto-detect

        encodings = ["utf-8", "latin1", "cp1252"]
        for enc in encodings:
            try:
                kwargs = {"filepath_or_buffer": file_path, "encoding": enc, "engine": "python", "on_bad_lines": "skip"}
                if delimiter:
                    kwargs["sep"] = delimiter
                else:
                    kwargs["sep"] = None

                df = pd.read_csv(**kwargs)
                break  # Success
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError:
                raise InvalidFileException("The CSV file contains no parsable data.")

        if df is None:
            # Last resort
            df = pd.read_csv(file_path, on_bad_lines="skip")

        if df.empty and len(df.columns) == 0:
            raise InvalidFileException("The CSV file has no columns or data.")

        # Sanitize columns
        df.columns = df.columns.astype(str).str.strip()

    except InvalidFileException:
        raise
    except Exception as e:
        raise InvalidFileException(f"Failed to parse CSV: {str(e)}")

    return {
        "dataframe": df,
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }


def parse_json(file_path: str) -> dict:
    """Parse a JSON file and return metadata."""
    try:
        with open(file_path, "rb") as f:
            if not f.read(1):
                raise InvalidFileException("The uploaded file is completely empty.")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Unwrap nested arrays if needed
        if isinstance(data, dict):
            for key in ["data", "records", "results", "items"]:
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
            else:
                data = [data]  # Wrap the single dictionary in a list

        if not isinstance(data, list):
            raise InvalidFileException("JSON must contain an array of objects.")

        if len(data) == 0:
            raise InvalidFileException("The uploaded JSON file is empty or contains no records.")

        df = pd.json_normalize(data)

        if df.empty and len(df.columns) == 0:
            raise InvalidFileException("The JSON file has no parsable tabular structure.")

        df.columns = df.columns.astype(str).str.strip()

    except InvalidFileException:
        raise
    except json.JSONDecodeError as e:
        raise InvalidFileException(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise InvalidFileException(f"Failed to parse JSON: {str(e)}")

    return {
        "dataframe": df,
        "row_count": len(df),
        "column_count": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }
