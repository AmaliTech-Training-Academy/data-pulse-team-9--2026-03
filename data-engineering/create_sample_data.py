"""Create sample check results for ETL testing."""

import os
import sys
from datetime import datetime, timedelta
import random

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datapulse.settings.dev")

import django

django.setup()

from datasets.models import Dataset
from rules.models import ValidationRule
from checks.models import CheckResult

print("Creating sample check results for ETL testing...")

# Get existing datasets
datasets = list(Dataset.objects.all()[:3])
if not datasets:
    print("No datasets found. Upload some datasets first!")
    sys.exit(1)

print(f"Found {len(datasets)} datasets")

# Create validation rules if they don't exist
rule_types = ["null_check", "type_check", "range_check", "uniqueness_check"]
severities = ["low", "medium", "high", "critical"]

rules = []
for i, rule_type in enumerate(rule_types):
    rule, created = ValidationRule.objects.get_or_create(
        name=f"Test {rule_type.replace('_', ' ').title()}",
        field_name=f"field_{i}",
        rule_type=rule_type,
        defaults={"severity": random.choice(severities), "config": {}},
    )
    rules.append(rule)
    if created:
        print(f"Created rule: {rule.name}")

# Create check results for the past 7 days
print("\nCreating check results...")
start_date = datetime.now() - timedelta(days=7)

for day in range(7):
    check_date = start_date + timedelta(days=day)

    for dataset in datasets:
        for rule in rules:
            # Random pass/fail
            passed = random.choice([True, True, True, False])  # 75% pass rate
            total_rows = dataset.row_count or 1000
            failed_rows = 0 if passed else random.randint(1, int(total_rows * 0.1))

            CheckResult.objects.create(
                dataset=dataset,
                rule=rule,
                passed=passed,
                failed_rows=failed_rows,
                total_rows=total_rows,
                checked_at=check_date,
            )

total_results = CheckResult.objects.count()
print(f"\n✅ Created {total_results} check results")
print(f"📊 Datasets: {len(datasets)}")
print(f"📋 Rules: {len(rules)}")
print(f"📅 Date range: {start_date.date()} to {datetime.now().date()}")
print("\n🚀 Ready to run ETL pipeline!")
