import json
import random
import time
from datetime import datetime

from checks.services.scoring_service import calculate_quality_score
from datasets.models import Dataset
from django.core.management.base import BaseCommand
from django.db import transaction
from schedule.tasks import _handle_alerts

rules_models = __import__("rules.models", fromlist=["ValidationRule"])
checks_models = __import__("checks.models", fromlist=["CheckResult", "QualityScore"])

ValidationRule = rules_models.ValidationRule
CheckResult = checks_models.CheckResult
QualityScore = checks_models.QualityScore


class Command(BaseCommand):
    help = "Stream mock check_results to simulate continuous evaluation"

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=10, help="Number of check_results per cycle (default: 10)")
        parser.add_argument("--interval", type=int, default=30, help="Seconds between cycles (default: 30)")
        parser.add_argument("--cycles", type=int, default=0, help="Number of cycles, 0 = infinite (default: 0)")

    def handle(self, *args, **options):
        rows = options["rows"]
        interval = options["interval"]
        max_cycles = options["cycles"]

        self.stdout.write(self.style.SUCCESS(f"Starting stream: {rows} rows every {interval}s"))

        cycle = 0
        try:
            while max_cycles == 0 or cycle < max_cycles:
                cycle += 1
                self.stdout.write(f"--- Cycle {cycle} started at {datetime.now().strftime('%H:%M:%S')} ---")

                # Get random dataset and active rules
                dataset = (
                    Dataset.objects.filter(status="VALIDATED").order_by("?").first()
                    or Dataset.objects.order_by("?").first()
                )
                if not dataset:
                    self.stderr.write("No datasets found. Seed the database first.")
                    time.sleep(interval)
                    continue

                rules = ValidationRule.objects.filter(is_active=True, dataset_type=dataset.file_type)
                if not rules.exists():
                    self.stderr.write(f"No active rules found for type '{dataset.file_type}'.")
                    time.sleep(interval)
                    continue

                self.stdout.write(f"Cycle {cycle}: Running checks for {dataset.name}")

                with transaction.atomic():
                    # Generate mock results
                    mock_results = []
                    for rule in rules:
                        total_rows = dataset.row_count or random.randint(100, 1000)
                        # Randomize quality: 80% chance of passing well
                        pass_rate = random.uniform(0.7, 1.0) if random.random() > 0.2 else random.uniform(0.3, 0.7)
                        passed_rows = int(total_rows * pass_rate)
                        failed_rows = total_rows - passed_rows
                        passed = failed_rows == 0

                        mock_results.append(
                            {
                                "rule_id": rule.id,
                                "passed": passed,
                                "failed_rows": failed_rows,
                                "total_rows": total_rows,
                                "details": json.dumps({"message": "Mock streamed check", "samples": []}),
                            }
                        )

                        CheckResult.objects.create(
                            dataset=dataset,
                            rule=rule,
                            passed=passed,
                            failed_rows=failed_rows,
                            total_rows=total_rows,
                            details=mock_results[-1]["details"],
                        )

                    # Calculate and save quality score
                    score_data = calculate_quality_score(mock_results, list(rules))
                    qs = QualityScore.objects.create(  # noqa: F841
                        dataset=dataset,
                        score=score_data["score"],
                        total_rules=score_data["total_rules"],
                        passed_rules=score_data["passed_rules"],
                        failed_rules=score_data["failed_rules"],
                    )

                    # Trigger alerts
                    _handle_alerts(dataset, score_data["score"])

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Successfully inserted {len(mock_results)} check results for '{dataset.name}'"
                    )
                )
                self.stdout.write(self.style.SUCCESS(f"  Score: {score_data['score']}%"))

                if max_cycles != 0 and cycle >= max_cycles:
                    break
                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write("\nStopped by user")

        self.stdout.write(f"Finished after {cycle} cycles")
