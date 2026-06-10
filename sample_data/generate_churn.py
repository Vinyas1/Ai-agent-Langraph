"""
Generate a sample customer churn dataset for testing the agent.
Run: python sample_data/generate_churn.py
"""

import csv
import random

random.seed(42)

headers = [
    "customer_id", "tenure_months", "monthly_charges", "total_charges",
    "contract_type", "payment_method", "internet_service",
    "num_support_tickets", "senior_citizen", "churn"
]

contracts = ["month-to-month", "one-year", "two-year"]
payments = ["credit_card", "bank_transfer", "electronic_check", "mailed_check"]
internet = ["fiber_optic", "dsl", "none"]

rows = []
for i in range(1, 1001):
    tenure = random.randint(1, 72)
    monthly = round(random.uniform(20, 110), 2)
    contract = random.choice(contracts)
    payment = random.choice(payments)
    net = random.choice(internet)
    tickets = random.randint(0, 9)
    senior = random.choice([0, 1])

    churn_prob = 0.15
    if contract == "month-to-month":
        churn_prob += 0.25
    if monthly > 70:
        churn_prob += 0.15
    if tickets > 4:
        churn_prob += 0.15
    if tenure < 12:
        churn_prob += 0.10

    churn = 1 if random.random() < churn_prob else 0
    total = round(monthly * tenure, 2)

    rows.append([
        f"CUST_{i:04d}", tenure, monthly, total,
        contract, payment, net, tickets, senior, churn
    ])

with open("sample_data/churn.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Generated sample_data/churn.csv with {len(rows)} rows")
