"""Write a computed example for the frontend without executing UI actions."""
import json
from pathlib import Path
from .engine import screen_customer, analyze_transaction


def main():
    now = "2026-09-06T12:00:00Z"
    customer = {"customer_id": "SYN-C001", "name": "Balafena Narikemi", "birth_date": "1980-01-01"}
    reference = {"synthetic": True, "version": "DEMO-1", "issued_at": "2026-09-06T00:00:00Z",
                 "expires_at": "2026-09-07T00:00:00Z", "entities": [
                     {"entity_id": "SYN-PEP1", "name": customer["name"], "birth_date": customer["birth_date"],
                      "category": "PEP", "aliases": []}]}
    transactions = [{"transaction_id": f"SYN-T{i}", "institution_id": "SYN-I1", "customer_id": customer["customer_id"],
                     "currency": "XOF", "amount_minor": 400000, "direction": "IN",
                     "occurred_at": f"2026-09-06T{8+i:02d}:00:00Z", "received_at": f"2026-09-06T{8+i:02d}:00:00Z"}
                    for i in range(3)]
    result = {"synthetic": True, "screening": screen_customer(customer, reference, as_of=now),
              "monitoring": analyze_transaction(transactions[-1], transactions[:-1], as_of=now,
                  history_complete=True, policy={"version": "DEMO-P1", "aggregate_threshold_minor": 1000000})}
    path = Path(__file__).parent / "artifacts/frontend-example.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__": main()
