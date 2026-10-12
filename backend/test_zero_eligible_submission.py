from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_connection

def test_zero_eligible_submission_prevention():
    client = TestClient(app)

    # 1. Test empty claim submission
    client.post("/api/session/reset")
    r = client.post("/api/submit-claim")
    assert r.status_code == 400
    assert "Cannot submit an empty claim" in r.json()["detail"]
    print("Test 1 Passed: Empty claim blocked with 400")

    # 2. Test claim with ONLY 0 eligible items
    # Load perks batch (which has 1 Croma item that violates policy)
    client.post("/api/session/reset")
    r = client.post("/api/load-perks-batch")
    assert r.status_code == 200
    session_data = r.json()

    # Delete all expenses except the Croma one (which has 0 eligible amount)
    croma_exp = None
    for exp in session_data["expenses"]:
        if "croma" in exp["merchant"].lower():
            croma_exp = exp
        else:
            client.delete(f"/api/expenses/{exp['id']}")

    assert croma_exp is not None
    # Verify current session has only 1 expense with eligible_amount == 0
    r = client.get("/api/session")
    s = r.json()
    assert s["summary"]["total_count"] == 1
    assert s["summary"]["eligible_amount"] == 0.0
    assert s["summary"]["total_amount"] == 22000.0

    # Try to submit via API -> MUST FAIL with 400
    r = client.post("/api/submit-claim")
    assert r.status_code == 400
    assert "Cannot submit a claim with" in r.json()["detail"]
    print("Test 2 Passed: Claim with Rs.0 eligible amount blocked from submission with HTTP 400")

    # Try to submit via Chat ("submit claim") -> MUST NOT SUBMIT
    r = client.post("/api/chat", json={"message": "Submit claim"})
    chat_session = r.json()
    assert chat_session["status"] != "submitted"
    assert chat_session["submission"] is None
    # Assistant message should explain why
    last_msg = chat_session["chat_history"][-1]["content"]
    assert "Submission Blocked" in last_msg
    print("Test 3 Passed: Chat submission for Rs.0 eligible claim blocked with explanation")

    # 3. Test submitting claim with MIXED items (eligible > 0 and ineligible = 0)
    # Load fresh perks batch: 5 eligible items + 1 ineligible (Croma Rs.22,000, 0 eligible)
    client.post("/api/session/reset")
    r = client.post("/api/load-perks-batch")
    assert r.status_code == 200
    s = r.json()
    assert s["summary"]["total_count"] == 6
    assert s["summary"]["eligible_amount"] == 53000.0
    assert s["summary"]["exception_amount"] == 25500.0

    # Submit this claim
    r = client.post("/api/submit-claim")
    assert r.status_code == 200
    sub_session = r.json()
    assert sub_session["status"] == "submitted"
    claim_ref = sub_session["submission"]["claim_reference"]

    # Verify claim voucher endpoint:
    # 0 eligible items must NOT be in the main submitted 'expenses' list!
    r = client.get("/api/claim-voucher")
    assert r.status_code == 200
    voucher_data = r.json()
    submitted_vouchers = voucher_data["expenses"]
    excluded_vouchers = voucher_data["excluded_ineligible_expenses"]
    assert len(submitted_vouchers) == 5
    assert len(excluded_vouchers) == 1
    assert any("croma" in e["merchant"].lower() for e in excluded_vouchers)
    for exp in submitted_vouchers:
        assert exp["eligible_amount"] > 0
    print("Test 4 Passed: Claim voucher itemized expenses contain ONLY items with eligible > 0")

    # Verify Database:
    # The claim must be in 'claims' table with expense_count = 5 (not 6!)
    # The 'expenses' table must contain ONLY the 5 eligible items, NOT the Croma item!
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM claims WHERE id = ?", (claim_ref,))
    claim_row = dict(c.fetchone())
    assert claim_row["eligible_amount"] == 53000.0
    assert claim_row["expense_count"] == 5

    c.execute("SELECT * FROM expenses WHERE claim_id = ?", (claim_ref,))
    db_expenses = [dict(row) for row in c.fetchall()]
    assert len(db_expenses) == 5
    for de in db_expenses:
        assert de["eligible_amount"] > 0
        assert "croma" not in de["merchant"].lower()
    conn.close()
    print("Test 5 Passed: Database strictly persisted ONLY the 5 eligible items (Croma 0-eligible item excluded)")

    # Clean up test claim
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE claim_id = ?", (claim_ref,))
    c.execute("DELETE FROM claims WHERE id = ?", (claim_ref,))
    c.execute("DELETE FROM audit_logs WHERE entity_id = ?", (claim_ref,))
    conn.commit()
    conn.close()

    print("\n>>> ALL 0-ELIGIBLE AMOUNT TESTS PASSED WITH 100% SUCCESS! <<<")

if __name__ == "__main__":
    test_zero_eligible_submission_prevention()
