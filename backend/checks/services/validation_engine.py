"""Validation engine - Implementation."""

import json
import re
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class ValidationEngine:
    """Runs data quality checks against a DataFrame."""

    def _build_result(self, passed: bool, failed_rows: int, total_rows: int, details: str) -> Dict[str, Any]:
        """Helper to standardise the validation result dictionary format."""
        return {
            "passed": passed,
            "failed_rows": failed_rows,
            "total_rows": total_rows,
            "details": details,
        }

    def _field_not_found(self, df: pd.DataFrame, field: str) -> Dict[str, Any]:
        """Helper to standardise the missing field error."""
        return self._build_result(
            passed=False, failed_rows=len(df), total_rows=len(df), details=f"Field {field} not found in dataset"
        )

    def run_all_checks(self, df: pd.DataFrame, rules: list) -> List[Dict[str, Any]]:
        """Run all validation checks. Returns list of result dicts."""
        results = []
        for rule in rules:
            params = json.loads(rule.parameters) if rule.parameters else {}
            field = getattr(rule, "field_name", "")

            # Verify field exists before running specific checks
            if field and field not in df.columns:
                result = self._field_not_found(df, field)
                result["rule_id"] = rule.id
                results.append(result)
                continue

            if rule.rule_type == "NOT_NULL":
                result = self.null_check(df, field)
            elif rule.rule_type == "DATA_TYPE":
                result = self.type_check(df, field, params.get("expected_type", "str"))
            elif rule.rule_type == "RANGE":
                result = self.range_check(df, field, params.get("min"), params.get("max"))
            elif rule.rule_type == "UNIQUE":
                result = self.unique_check(df, field)
            elif rule.rule_type == "REGEX":
                result = self.regex_check(df, field, params.get("pattern", ""))
            else:
                result = self._build_result(
                    passed=False, failed_rows=0, total_rows=len(df), details=f"Unknown rule_type: {rule.rule_type}"
                )

            result["rule_id"] = rule.id
            results.append(result)

        return results

    def null_check(self, df: pd.DataFrame, field: str) -> Dict[str, Any]:
        """Check for null values in a field."""
        null_count = int(df[field].isnull().sum())
        return self._build_result(
            passed=(null_count == 0),
            failed_rows=null_count,
            total_rows=len(df),
            details=f"{null_count} null values found in {field}" if null_count > 0 else f"No null values in {field}",
        )

    def type_check(self, df: pd.DataFrame, field: str, expected_type: str) -> Dict[str, Any]:
        """Check data types."""
        etype = str(expected_type).lower()

        if etype == "str":
            return self._build_result(True, 0, len(df), "String type always match")

        if etype == "numeric":
            passed_mask = pd.to_numeric(df[field], errors="coerce").notnull()
            failed_count = int((~passed_mask).sum())
            return self._build_result(
                failed_count == 0, failed_count, len(df), f"{failed_count} non-numeric values found"
            )

        if etype == "datetime":
            passed_mask = pd.to_datetime(df[field], errors="coerce").notnull()
            failed_count = int((~passed_mask).sum())
            return self._build_result(
                failed_count == 0, failed_count, len(df), f"{failed_count} invalid datetime values found"
            )

        # Handle other types like int, float, bool
        type_map = {
            "int": pd.api.types.is_integer_dtype,
            "float": pd.api.types.is_float_dtype,
            "bool": pd.api.types.is_bool_dtype,
        }
        check_func = type_map.get(etype)

        if check_func and check_func(df[field]):
            return self._build_result(True, 0, len(df), f"All values in {field} are {expected_type}")

        return self._build_result(False, len(df), len(df), f"Field {field} is not of type {expected_type}")

    def range_check(
        self, df: pd.DataFrame, field: str, min_val: Optional[Union[int, float]], max_val: Optional[Union[int, float]]
    ) -> Dict[str, Any]:
        """Check value ranges."""
        # Ensure field is numeric, try to convert if not
        if not pd.api.types.is_numeric_dtype(df[field]):
            temp_numeric = pd.to_numeric(df[field], errors="coerce")
            if temp_numeric.isnull().all():
                return self._build_result(False, len(df), len(df), f"Field {field} is not numeric")
            series = temp_numeric
        else:
            series = df[field]

        invalid_mask = pd.Series([False] * len(df), index=df.index)
        if min_val is not None:
            invalid_mask |= series < float(min_val)
        if max_val is not None:
            invalid_mask |= series > float(max_val)

        # Nulls or conversion failures are considered range failures
        invalid_mask |= series.isnull()

        failed_count = int(invalid_mask.sum())
        return self._build_result(
            passed=(failed_count == 0),
            failed_rows=failed_count,
            total_rows=len(df),
            details=f"{failed_count} values outside range [{min_val}, {max_val}] or non-numeric",
        )

    def unique_check(self, df: pd.DataFrame, field: str) -> Dict[str, Any]:
        """Check uniqueness."""
        duplicates = int(df[field].duplicated(keep=False).sum())
        return self._build_result(
            passed=(duplicates == 0),
            failed_rows=duplicates,
            total_rows=len(df),
            details=f"{duplicates} duplicate values found in {field}",
        )

    def regex_check(self, df: pd.DataFrame, field: str, pattern: str) -> Dict[str, Any]:
        """Check regex pattern matching."""
        if not pattern:
            return self._build_result(False, len(df), len(df), "No pattern provided")

        try:
            # Use na=False to ensure nulls fail the regex match
            matches = df[field].astype(str).str.match(pattern, na=False)
            failed_count = int((~matches).sum())
        except re.error as e:
            return self._build_result(False, len(df), len(df), f"Invalid regex pattern: {str(e)}")

        return self._build_result(
            passed=(failed_count == 0),
            failed_rows=failed_count,
            total_rows=len(df),
            details=f"{failed_count} values do not match pattern {pattern}",
        )
