import json

import pandas as pd
from checks.services.validation_engine import ValidationEngine

df = pd.DataFrame(
    {
        "id": [1, 2, 3, 4],
        "name": ["Alice", "Bob", "Charlie", None],
        "age": [25, 30, "invalid", 40],
        "score": [90.5, 80.0, 70.1, 105.0],
        "date": ["2023-01-01", "2023-02-01", "not-a-date", "2023-04-01"],
        "email": ["a@a.com", "b@b.com", "c@c.com", "d@d"],
    }
)

engine = ValidationEngine()


class DummyRule:
    def __init__(self, rule_id, rule_type, field_name, parameters=None):
        self.id = rule_id
        self.rule_type = rule_type
        self.field_name = field_name
        self.parameters = parameters


rules = [
    DummyRule(1, "NOT_NULL", "name"),
    DummyRule(2, "DATA_TYPE", "age", '{"expected_type": "numeric"}'),
    DummyRule(3, "DATA_TYPE", "date", '{"expected_type": "datetime"}'),
    DummyRule(4, "RANGE", "score", '{"min": 0, "max": 100}'),
    DummyRule(5, "UNIQUE", "id"),
    DummyRule(6, "REGEX", "email", '{"pattern": "^[\\\\w\\\\.-]+@[\\\\w\\\\.-]+\\\\.\\\\w+$"}'),
    DummyRule(7, "NOT_NULL", "missing_field"),
]

results = engine.run_all_checks(df, rules)

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)
