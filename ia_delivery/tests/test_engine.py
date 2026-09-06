import unittest
from ia_delivery.engine import screen_customer, analyze_transaction

NOW = "2026-09-06T12:00:00Z"
SNAPSHOT = {"synthetic": True, "version": "DEMO-1", "issued_at": "2026-09-06T00:00:00Z",
            "expires_at": "2026-09-07T00:00:00Z", "entities": [
                {"entity_id": "SYN-PEP", "name": "Balafena Narikemi", "category": "PEP",
                 "birth_date": "1980-01-01", "aliases": []}]}
CUSTOMER = {"customer_id": "SYN-C", "name": "Balafena Narikemi", "birth_date": "1980-01-01"}
POLICY = {"version": "DEMO-P1", "aggregate_threshold_minor": 1000000, "window_hours": 48}


def tx(i, hour=10, direction="IN", amount=400000):
    return {"transaction_id": str(i), "customer_id": "SYN-C", "institution_id": "SYN-I",
            "currency": "XOF", "amount_minor": amount, "direction": direction,
            "occurred_at": f"2026-09-06T{hour:02d}:00:00Z", "received_at": f"2026-09-06T{hour:02d}:00:00Z"}


class EngineTests(unittest.TestCase):
    def test_pep_is_not_blocked(self):
        r = screen_customer(CUSTOMER, SNAPSHOT, as_of=NOW)
        self.assertEqual(r["candidates"][0]["recommended_action"], "IDENTITY_REVIEW")
        self.assertEqual(r["operational_decision"], "NOT_TAKEN_BY_ENGINE")

    def test_expired_reference(self):
        self.assertEqual(screen_customer(CUSTOMER, SNAPSHOT, as_of="2026-09-08T00:00:00Z")["status"], "INCOMPLETE")

    def test_real_reference_rejected(self):
        with self.assertRaises(ValueError): screen_customer(CUSTOMER, {**SNAPSHOT, "synthetic": False}, as_of=NOW)

    def test_homonym_evidence(self):
        r = screen_customer({**CUSTOMER, "birth_date": "1991-01-01"}, SNAPSHOT, as_of=NOW)
        self.assertIn("BIRTH_DATE_CONFLICT", r["candidates"][0]["reason_codes"])

    def test_duplicate_and_order_invariance(self):
        a, b, c = tx(1), tx(2), tx(3)
        r = analyze_transaction(c, [a, b], as_of=NOW, history_complete=True, policy=POLICY)
        repeat = analyze_transaction(c, [c, b, a, a], as_of=NOW, history_complete=True, policy=POLICY)
        self.assertEqual(r, repeat)
        self.assertEqual(len(r["findings"]), 1)

    def test_future_excluded(self):
        r = analyze_transaction(tx(1), [tx(2), tx(3, 13)], as_of=NOW, history_complete=True, policy=POLICY)
        self.assertEqual(r["findings"], [])

    def test_late_receipt_excluded(self):
        late = {**tx(3), "received_at": "2026-09-07T10:00:00Z"}
        r = analyze_transaction(tx(1), [tx(2), late], as_of=NOW, history_complete=False, policy=POLICY)
        self.assertEqual(r["findings"], [])
        self.assertEqual(r["status"], "PARTIAL")

    def test_conflicting_duplicate(self):
        with self.assertRaises(ValueError):
            analyze_transaction(tx(1), [tx(1, amount=1)], as_of=NOW, history_complete=True, policy=POLICY)

    def test_currency_and_tenant(self):
        for field, value in [("currency", "EUR"), ("institution_id", "OTHER")]:
            with self.assertRaises(ValueError):
                analyze_transaction(tx(1), [{**tx(2), field: value}], as_of=NOW, history_complete=True, policy=POLICY)

    def test_rapid_movement(self):
        r = analyze_transaction(tx(2, 11, "OUT"), [tx(1)], as_of=NOW, history_complete=True, policy=POLICY)
        self.assertEqual(r["findings"][0]["rule_id"], "RAPID_IN_OUT")

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            analyze_transaction(tx(1, amount=-1), [], as_of=NOW, history_complete=True, policy=POLICY)


if __name__ == "__main__": unittest.main()
