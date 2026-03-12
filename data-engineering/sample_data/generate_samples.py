"""Generate sample datasets with configurable error rate - IMPLEMENTED."""

import csv
import os
import random
import string
from datetime import datetime, timedelta

DEPARTMENTS = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry"]
LAST_NAMES = ["Smith", "Jones", "White", "Brown", "Davis", "Miller", "Wilson", "Taylor"]


def generate_dataset(num_rows=100, error_rate=0.1, output_path="generated.csv"):
    """Generate a dataset with a given error rate."""
    rows = []
    for i in range(1, num_rows + 1):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        email = f"{name.split()[0].lower()}_{i}@company.com"
        age = random.randint(22, 65)
        dept = random.choice(DEPARTMENTS)
        salary = random.randint(50000, 150000)
        days_ago = random.randint(30, 2000)
        hire = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        # Introduce errors based on error_rate
        if random.random() < error_rate:
            choice = random.randint(0, 5)
            if choice == 0:
                name = ""
            elif choice == 1:
                email = "not-valid"
            elif choice == 2:
                age = random.choice([-5, 0, 200])
            elif choice == 3:
                dept = ""
            elif choice == 4:
                salary = "abc"
            elif choice == 5:
                hire = ""

        rows.append([i, name, email, age, dept, salary, hire])

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "email", "age", "department", "salary", "hire_date"])
        writer.writerows(rows)
    print(f"Generated {num_rows} rows -> {output_path} (error_rate={error_rate})")


if __name__ == "__main__":
    d = os.path.dirname(os.path.abspath(__file__))
    generate_dataset(100, 0.0, os.path.join(d, "large_clean.csv"))
    generate_dataset(100, 0.15, os.path.join(d, "large_dirty.csv"))
    generate_dataset(200, 0.08, os.path.join(d, "large_mixed.csv"))
