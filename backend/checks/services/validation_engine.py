"""Validation engine - PARTIAL implementation."""

import json
import re
import pandas as pd


class ValidationEngine:
    """Runs data quality checks against a DataFrame."""

    def run_all_checks(self, df: pd.DataFrame, rules: list) -> list:
        """Run all validation checks. Returns list of result dicts."""
        results = []
        for rule in rules:
            params = json.loads(rule.parameters) if rule.parameters else {}
            if rule.rule_type == "NOT_NULL":
                result = self.null_check(df, rule.field_name)
            elif rule.rule_type == "DATA_TYPE":
                result = self.type_check(df, rule.field_name, params.get("expected_type", "str"))
            elif rule.rule_type == "RANGE":
                result = self.range_check(df, rule.field_name, params.get("min"), params.get("max"))
            elif rule.rule_type == "UNIQUE":
                result = self.unique_check(df, rule.field_name)
            elif rule.rule_type == "REGEX":
                result = self.regex_check(df, rule.field_name, params.get("pattern", ""))
            else:
                result = {"passed": False, "failed_rows": 0, "total_rows": len(df),
                    "details": f"Unknown rule_type: {rule.rule_type}"}
            result["rule_id"] = rule.id
            results.append(result)
        return results

    def null_check(self, df: pd.DataFrame, field: str) -> dict:
        """Check for null values in a field - IMPLEMENTED."""
        if field not in df.columns:
            return {"passed": False, "failed_rows": len(df), "total_rows": len(df),
                "details": f"Field {field} not found in dataset"}
        null_count = int(df[field].isnull().sum())
        return {
            "passed": null_count == 0,
            "failed_rows": null_count,
            "total_rows": len(df),
            "details": f"{null_count} null values found in {field}",
        }

    def type_check(self, df, field, expected_type):
        """Check data types - IMPLEMENTED."""
        if field not in df.columns:
            return {"passed": False, "failed_rows": len(df), "total_rows": len(df),
                "details": f"Field {field} not found"}
        
        etype = expected_type.lower()
        
        if etype == "str":
            return {"passed": True, "failed_rows": 0, "total_rows": len(df), "details": "String type always match"}

        if etype == "numeric":
            passed_mask = pd.to_numeric(df[field], errors='coerce').notnull()
            failed_count = int((~passed_mask).sum())
            return {
                "passed": failed_count == 0,
                "failed_rows": failed_count,
                "total_rows": len(df),
                "details": f"{failed_count} non-numeric values found"
            }

        if etype == "datetime":
            passed_mask = pd.to_datetime(df[field], errors='coerce').notnull()
            failed_count = int((~passed_mask).sum())
            return {
                "passed": failed_count == 0,
                "failed_rows": failed_count,
                "total_rows": len(df),
                "details": f"{failed_count} invalid datetime values found"
            }

        # Simple type mapping for others
        type_map = {
            "int": pd.api.types.is_integer_dtype,
            "float": pd.api.types.is_float_dtype,
            "bool": pd.api.types.is_bool_dtype,
        }
        
        check_func = type_map.get(etype)
        if check_func and check_func(df[field]):
            return {"passed": True, "failed_rows": 0, "total_rows": len(df),
                "details": f"All values in {field} are {expected_type}"}
        
        return {"passed": False, "failed_rows": len(df), "total_rows": len(df),
            "details": f"Field {field} is not of type {expected_type}"}

    def range_check(self, df, field, min_val, max_val):
        """Check value ranges - IMPLEMENTED."""
        if field not in df.columns:
            return {"passed": False, "failed_rows": len(df), "total_rows": len(df),
                "details": f"Field {field} not found"}
        
        # Ensure field is numeric
        if not pd.api.types.is_numeric_dtype(df[field]):
            # Try to convert if it's not numeric
            temp_numeric = pd.to_numeric(df[field], errors='coerce')
            if temp_numeric.isnull().all():
                return {"passed": False, "failed_rows": len(df), "total_rows": len(df),
                    "details": f"Field {field} is not numeric"}
            series = temp_numeric
        else:
            series = df[field]

        invalid_mask = pd.Series([False] * len(df), index=df.index)
        if min_val is not None:
            invalid_mask |= (series < min_val)
        if max_val is not None:
            invalid_mask |= (series > max_val)
        
        # Handle cases where conversion failed
        invalid_mask |= series.isnull()
        
        failed_count = int(invalid_mask.sum())
        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} values outside range [{min_val}, {max_val}] or non-numeric",
        }

    def unique_check(self, df, field):
        """Check uniqueness - IMPLEMENTED."""
        if field not in df.columns:
            return {"passed": False, "failed_rows": len(df), "total_rows": len(df),
                "details": f"Field {field} not found"}
        
        duplicates = df[field].duplicated(keep=False).sum()
        failed_count = int(duplicates)
        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} duplicate values found in {field}",
        }

    def regex_check(self, df, field, pattern):
        """Check regex pattern matching - IMPLEMENTED."""
        if field not in df.columns:
            return {"passed": False, "failed_rows": len(df), "total_rows": len(df),
                "details": f"Field {field} not found"}
        
        if not pattern:
            return {"passed": False, "failed_rows": len(df), "total_rows": len(df), "details": "No pattern provided"}

        # Use fillna to handle nulls in regex check
        matches = df[field].astype(str).str.match(pattern, na=False)
        failed_count = int((~matches).sum())
        
        return {
            "passed": failed_count == 0,
            "failed_rows": failed_count,
            "total_rows": len(df),
            "details": f"{failed_count} values do not match pattern {pattern}",
        }
