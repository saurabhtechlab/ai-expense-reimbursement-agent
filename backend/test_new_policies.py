from fastapi.testclient import TestClient
from backend.main import app

def test_new_policies():
    client = TestClient(app)

    # Reset session
    r = client.post("/api/session/reset")
    assert r.status_code == 200

    # Load Perks batch
    r = client.post("/api/load-perks-batch")
    assert r.status_code == 200
    data = r.json()

    print("=== Perks Batch Test Results ===")
    print("Total Expenses:", data["summary"]["total_count"])
    print("Total Amount: Rs.", data["summary"]["total_amount"])
    print("Eligible Amount: Rs.", data["summary"]["eligible_amount"])
    print("Exception Amount: Rs.", data["summary"]["exception_amount"])
    print("Ready Count:", data["summary"]["ready_count"])

    for e in data["expenses"]:
        print(f"\n- [{e['category']}] {e['merchant']}")
        print(f"  Amount: Rs.{e['amount']}, Eligible: Rs.{e['eligible_amount']}, Exception: Rs.{e['exception_amount']}, Status: {e['status']}")
        for f in e.get("flags", []):
            safe_msg = f['message'].replace("₹", "Rs.")
            print(f"  * Flag: {f['code']} - {safe_msg}")

    # 1. Total expenses should be 6
    assert data["summary"]["total_count"] == 6

    # 2. Check each specific policy:
    # Rule 1: Mobile Headset
    # - Reliance Digital: ₹18,500 <= ₹20,000 -> 18,500 eligible, 0 exception
    # - Croma: ₹22,000 -> Ineligible vendor -> 0 eligible, 22,000 exception
    # Rule 2: Driver Salary
    # - September: ₹9,500 <= ₹10,000 -> 9,500 eligible, 0 exception
    # - October: ₹12,000 > ₹10,000 -> 10,000 eligible, 2,000 exception
    # Rule 3: Fuel Expenses
    # - September part 1: ₹4,500 -> 4,500 eligible, 0 exception
    # - September part 2: ₹12,000 -> Cumulative ₹16,500 > ₹15,000 -> 10,500 eligible, 1,500 exception
    
    # Aggregates:
    # Total claimed: 18500 + 22000 + 9500 + 12000 + 4500 + 12000 = 78,500
    # Total eligible: 18500 + 0 + 9500 + 10000 + 4500 + 10500 = 53,000
    # Total exceptions: 0 + 22000 + 0 + 2000 + 0 + 1500 = 25,500
    assert data["summary"]["total_amount"] == 78500.0
    assert data["summary"]["eligible_amount"] == 53000.0
    assert data["summary"]["exception_amount"] == 25500.0

    print("\n>>> ALL 3 NEW POLICIES AND UNDERSTANDING VERIFIED 100% ACCURATELY! <<<")

if __name__ == "__main__":
    test_new_policies()
