import sqlite3
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "reimbursements.db")
)

def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables and seeds initial policies and sample submitted claims."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Claims Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id TEXT PRIMARY KEY,
        voucher_id TEXT,
        employee_id TEXT NOT NULL,
        employee_name TEXT NOT NULL,
        department TEXT NOT NULL,
        submission_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('under_process', 'approved', 'rejected')),
        total_amount REAL NOT NULL DEFAULT 0.0,
        eligible_amount REAL NOT NULL DEFAULT 0.0,
        exception_amount REAL NOT NULL DEFAULT 0.0,
        expense_count INTEGER NOT NULL DEFAULT 0,
        notes TEXT,
        rejection_reason TEXT,
        reviewed_by TEXT,
        reviewed_at TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Expenses Table (Itemized bills linked to claims)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id TEXT PRIMARY KEY,
        claim_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_hash TEXT,
        file_type TEXT,
        preview_url TEXT,
        merchant TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT '₹',
        date TEXT,
        category TEXT NOT NULL,
        tax_amount REAL DEFAULT 0.0,
        payment_method TEXT,
        business_purpose TEXT,
        status TEXT NOT NULL,
        eligible_amount REAL NOT NULL DEFAULT 0.0,
        exception_amount REAL NOT NULL DEFAULT 0.0,
        flags_json TEXT,
        claim_status TEXT NOT NULL CHECK(claim_status IN ('under_process', 'approved', 'rejected')),
        created_at TEXT NOT NULL,
        FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
    );
    """)

    # Index for super-fast duplicate detection
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_hash ON expenses(file_hash);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_dup_lookup ON expenses(merchant, amount, date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_claim_status ON expenses(claim_status);")

    # 3. Policy Rules Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policy_rules (
        id TEXT PRIMARY KEY,
        rule_name TEXT NOT NULL,
        category TEXT NOT NULL,
        keywords TEXT NOT NULL,
        max_limit REAL NOT NULL DEFAULT 0.0,
        limit_period TEXT NOT NULL CHECK(limit_period IN ('financial_year', 'monthly', 'per_claim', 'no_limit')),
        vendor_restriction TEXT DEFAULT '',
        require_business_purpose INTEGER NOT NULL DEFAULT 0,
        require_date INTEGER NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1,
        description TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 4. Audit Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        performed_by TEXT NOT NULL,
        details TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed Policy Rules if none exist
    cursor.execute("SELECT COUNT(*) as cnt FROM policy_rules;")
    if cursor.fetchone()["cnt"] == 0:
        _seed_default_policies(cursor)
        conn.commit()

    # Seed Sample Claims if none exist
    cursor.execute("SELECT COUNT(*) as cnt FROM claims;")
    if cursor.fetchone()["cnt"] == 0:
        _seed_sample_claims(cursor)
        conn.commit()

    conn.close()

def _seed_default_policies(cursor):
    policies = [
        (
            "POL-001",
            "Mobile Headset Reimbursement",
            "Mobile Headset",
            "headset, headphones, earphones, airpods, sony, bose",
            20000.0,
            "financial_year",
            "Reliance Digital",
            1,
            1,
            1,
            "Reimbursement up to ₹20,000 per financial year. Invoices must be exclusively from Reliance Digital.",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "POL-002",
            "Driver Salary (Travel Assistance)",
            "Driver Salary",
            "driver, chauffeur, driver salary",
            10000.0,
            "monthly",
            "",
            1,
            1,
            1,
            "Personal driver salary allowance up to ₹10,000 per calendar month for official business transit.",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "POL-003",
            "Fuel Expenses",
            "Fuel",
            "fuel, petrol, diesel, hpcl, indian oil, bpcl, shell",
            15000.0,
            "monthly",
            "",
            1,
            1,
            1,
            "Monthly fuel allowance up to ₹15,000 per calendar month for official travel.",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "POL-004",
            "Hotel Accommodation",
            "Hotel",
            "hotel, lodging, stay, orchid, marriott, hyatt",
            10000.0,
            "per_claim",
            "",
            1,
            1,
            1,
            "Hotel stay reimbursement requires explicit business purpose and travel dates.",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "POL-005",
            "Taxi & Local Transit",
            "Taxi",
            "taxi, cab, uber, ola, auto, transit",
            2500.0,
            "per_claim",
            "",
            0,
            1,
            1,
            "Taxi transit for business meetings requires clear travel date on receipt.",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "POL-006",
            "Broadband & Home Internet",
            "Telecommunication",
            "broadband, fiber, airtel, jio, internet, wifi",
            5000.0,
            "monthly",
            "",
            1,
            1,
            1,
            "Monthly work-from-home internet reimbursement up to ₹5,000/month.",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    ]
    cursor.executemany("""
    INSERT INTO policy_rules (
        id, rule_name, category, keywords, max_limit, limit_period, vendor_restriction,
        require_business_purpose, require_date, is_active, description, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, policies)

def _seed_sample_claims(cursor):
    """Seeds historical submitted/approved/rejected claims to populate the admin dashboard."""
    now = datetime.now()
    
    # Claim 1: Vikram Malhotra - Mobile Headset (Approved in August)
    c1_id = "CLM-2026-0041"
    cursor.execute("""
    INSERT INTO claims (
        id, voucher_id, employee_id, employee_name, department, submission_date,
        status, total_amount, eligible_amount, exception_amount, expense_count,
        notes, reviewed_by, reviewed_at, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        c1_id, "VOUCH-8821", "EMP-1024", "Vikram Malhotra", "Product Engineering", "2026-08-18",
        "approved", 18000.0, 18000.0, 0.0, 1,
        "Sony ANC Headphones purchased from Reliance Digital with tax invoice.",
        "Admin (Finance Team)", "2026-08-19 11:30:00", "2026-08-18 16:45:00"
    ))
    cursor.execute("""
    INSERT INTO expenses (
        id, claim_id, file_name, file_hash, file_type, preview_url,
        merchant, amount, currency, date, category, tax_amount,
        payment_method, business_purpose, status, eligible_amount, exception_amount,
        flags_json, claim_status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        "exp-seed-1", c1_id, "past_headset_reliance_aug.png", "hash_seed_past_headset_reliance", "image/png", "/static/sample/headset_reliance_digital.png",
        "Reliance Digital Superstore - Indiranagar", 18000.0, "₹", "2026-08-18", "Mobile Headset", 2745.0,
        "Corporate Card", "ANC headset for remote client calls", "ready", 18000.0, 0.0,
        "[]", "approved", "2026-08-18 16:45:00"
    ))

    # Claim 2: Priya Sharma - Driver & Fuel (Under Process in August)
    c2_id = "CLM-2026-0038"
    cursor.execute("""
    INSERT INTO claims (
        id, voucher_id, employee_id, employee_name, department, submission_date,
        status, total_amount, eligible_amount, exception_amount, expense_count,
        notes, reviewed_by, reviewed_at, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        c2_id, "VOUCH-7742", "EMP-2155", "Priya Sharma", "Enterprise Sales", "2026-08-29",
        "under_process", 20500.0, 20500.0, 0.0, 2,
        "August travel assistance and fuel.",
        None, None, "2026-08-29 10:15:00"
    ))
    cursor.execute("""
    INSERT INTO expenses (
        id, claim_id, file_name, file_hash, file_type, preview_url,
        merchant, amount, currency, date, category, tax_amount,
        payment_method, business_purpose, status, eligible_amount, exception_amount,
        flags_json, claim_status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        "exp-seed-2a", c2_id, "past_driver_salary_july.png", "hash_seed_driver_july", "image/png", "/static/sample/driver_salary_receipt_12k.png",
        "Suresh Yadav (Chauffeur)", 9500.0, "₹", "July 2026", "Driver Salary", 0.0,
        "Bank Transfer", "Driver salary for client transit", "ready", 9500.0, 0.0,
        "[]", "under_process", "2026-08-29 10:15:00"
    ))
    cursor.execute("""
    INSERT INTO expenses (
        id, claim_id, file_name, file_hash, file_type, preview_url,
        merchant, amount, currency, date, category, tax_amount,
        payment_method, business_purpose, status, eligible_amount, exception_amount,
        flags_json, claim_status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        "exp-seed-2b", c2_id, "past_fuel_shell_aug.png", "hash_seed_fuel_shell_aug", "image/png", "/static/sample/fuel_hpcl_auto_care.png",
        "Shell Petrol Bunk Koramangala", 11000.0, "₹", "2026-08-20", "Fuel", 0.0,
        "Personal Card", "Field sales client visits", "ready", 11000.0, 0.0,
        "[]", "under_process", "2026-08-29 10:15:00"
    ))

    # Claim 3: Amit Verma - Non-Reliance Headset (Rejected in August)
    c3_id = "CLM-2026-0032"
    cursor.execute("""
    INSERT INTO claims (
        id, voucher_id, employee_id, employee_name, department, submission_date,
        status, total_amount, eligible_amount, exception_amount, expense_count,
        notes, rejection_reason, reviewed_by, reviewed_at, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        c3_id, "VOUCH-6619", "EMP-3042", "Amit Verma", "Marketing", "2026-08-22",
        "rejected", 21500.0, 0.0, 21500.0, 1,
        "Headset claim from non-approved vendor.",
        "Headset invoices must be strictly from Reliance Digital per company perk policy. Vendor 'Croma' is not allowed.",
        "Admin (Finance Team)", "2026-08-23 09:20:00", "2026-08-22 14:10:00"
    ))
    cursor.execute("""
    INSERT INTO expenses (
        id, claim_id, file_name, file_hash, file_type, preview_url,
        merchant, amount, currency, date, category, tax_amount,
        payment_method, business_purpose, status, eligible_amount, exception_amount,
        flags_json, claim_status, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        "exp-seed-3", c3_id, "past_croma_headset.png", "hash_seed_croma_aug", "image/png", "/static/sample/headset_croma_electronics.png",
        "Croma Electronics Indiranagar", 21500.0, "₹", "2026-08-15", "Mobile Headset", 3280.0,
        "Personal Card", "Bose QC45 Headset", "policy_violation", 0.0, 21500.0,
        json.dumps([{"code": "HEADSET_NON_RELIANCE_VENDOR", "message": "Invoices must be from Reliance Digital"}]),
        "rejected", "2026-08-22 14:10:00"
    ))

# ==============================================================================
# Database Operations: Duplicate Detection Against Database
# ==============================================================================

def check_bill_duplicate_in_db(
    file_hash: Optional[str] = None,
    merchant: Optional[str] = None,
    amount: Optional[float] = None,
    date: Optional[str] = None,
    file_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Checks if a receipt matches any existing bill in the database that is
    'under_process' or 'approved'.
    Returns the matching record dictionary or None.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Match by binary SHA-256 hash (exact duplicate file)
    if file_hash:
        cursor.execute("""
        SELECT e.*, c.voucher_id, c.employee_name, c.employee_id as claimant_id
        FROM expenses e
        JOIN claims c ON e.claim_id = c.id
        WHERE e.file_hash = ?
          AND e.claim_status IN ('under_process', 'approved')
        LIMIT 1;
        """, (file_hash,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    # 2. Match by exact (Merchant + Amount + Date) or (Merchant + Amount)
    if merchant and amount:
        clean_merchant = merchant.strip().lower()
        if date and len(date) >= 7:
            cursor.execute("""
            SELECT e.*, c.voucher_id, c.employee_name, c.employee_id as claimant_id
            FROM expenses e
            JOIN claims c ON e.claim_id = c.id
            WHERE LOWER(e.merchant) = ?
              AND ABS(e.amount - ?) < 0.01
              AND (e.date = ? OR e.date LIKE ?)
              AND e.claim_status IN ('under_process', 'approved')
            LIMIT 1;
            """, (clean_merchant, amount, date, f"{date[:7]}%"))
        else:
            cursor.execute("""
            SELECT e.*, c.voucher_id, c.employee_name, c.employee_id as claimant_id
            FROM expenses e
            JOIN claims c ON e.claim_id = c.id
            WHERE LOWER(e.merchant) = ?
              AND ABS(e.amount - ?) < 0.01
              AND e.claim_status IN ('under_process', 'approved')
            LIMIT 1;
            """, (clean_merchant, amount))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    # 3. Match by file_name (with or without amount)
    if file_name:
        if amount is not None:
            cursor.execute("""
            SELECT e.*, c.voucher_id, c.employee_name, c.employee_id as claimant_id
            FROM expenses e
            JOIN claims c ON e.claim_id = c.id
            WHERE LOWER(e.file_name) = ?
              AND ABS(e.amount - ?) < 0.01
              AND e.claim_status IN ('under_process', 'approved')
            LIMIT 1;
            """, (file_name.lower(), amount))
        else:
            cursor.execute("""
            SELECT e.*, c.voucher_id, c.employee_name, c.employee_id as claimant_id
            FROM expenses e
            JOIN claims c ON e.claim_id = c.id
            WHERE LOWER(e.file_name) = ?
              AND e.claim_status IN ('under_process', 'approved')
            LIMIT 1;
            """, (file_name.lower(),))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)

    conn.close()
    return None

# ==============================================================================
# Database Operations: Claims Management
# ==============================================================================

def save_submitted_claim(claim_data: Dict[str, Any], expenses_list: List[Dict[str, Any]]) -> str:
    """Saves a newly submitted claim and strictly its eligible line expenses to the database."""
    eligible_amt = float(claim_data.get("eligible_amount", 0.0))
    if eligible_amt <= 0:
        raise ValueError("Cannot persist claim with ₹0 eligible reimbursement. Only claims with eligible amount > 0 can be submitted.")

    # Strictly filter out any expenses with eligible_amount <= 0 (e.g. duplicates, policy violations)
    valid_expenses = [exp for exp in expenses_list if float(exp.get("eligible_amount") or 0.0) > 0.0]
    if not valid_expenses:
        raise ValueError("Cannot persist claim: No line expenses with eligible amount > 0.")

    conn = get_connection()
    cursor = conn.cursor()

    claim_id = claim_data.get("id") or f"CLM-2026-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO claims (
        id, voucher_id, employee_id, employee_name, department, submission_date,
        status, total_amount, eligible_amount, exception_amount, expense_count,
        notes, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        claim_id,
        claim_data.get("voucher_id", f"VOUCH-{uuid.uuid4().hex[:6].upper()}"),
        claim_data.get("employee_id", "EMP-4091"),
        claim_data.get("employee_name", "Saurabh Gupta"),
        claim_data.get("department", "Product Engineering"),
        claim_data.get("submission_date", datetime.now().strftime("%Y-%m-%d")),
        "under_process",
        float(claim_data.get("total_amount", 0.0)),
        eligible_amt,
        float(claim_data.get("exception_amount", 0.0)),
        len(valid_expenses),
        claim_data.get("notes", "Submitted via ReimburseAI Assistant"),
        now_str
    ))

    for exp in valid_expenses:
        flags_json = json.dumps(exp.get("flags", [])) if isinstance(exp.get("flags"), list) else "[]"
        cursor.execute("""
        INSERT INTO expenses (
            id, claim_id, file_name, file_hash, file_type, preview_url,
            merchant, amount, currency, date, category, tax_amount,
            payment_method, business_purpose, status, eligible_amount, exception_amount,
            flags_json, claim_status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            exp.get("id") or str(uuid.uuid4()),
            claim_id,
            exp.get("file_name", "receipt.png"),
            exp.get("file_hash"),
            exp.get("file_type", "image/png"),
            exp.get("preview_url", ""),
            exp.get("merchant", "Unknown Merchant"),
            float(exp.get("amount", 0.0)),
            exp.get("currency", "₹"),
            exp.get("date"),
            exp.get("category", "Other"),
            float(exp.get("tax_amount", 0.0)),
            exp.get("payment_method", "Card"),
            exp.get("business_purpose"),
            exp.get("status", "ready"),
            float(exp.get("eligible_amount", 0.0)),
            float(exp.get("exception_amount", 0.0)),
            flags_json,
            "under_process",
            now_str
        ))

    # Log audit
    cursor.execute("""
    INSERT INTO audit_logs (id, action, entity_type, entity_id, performed_by, details, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        str(uuid.uuid4()),
        "CLAIM_SUBMITTED",
        "claim",
        claim_id,
        claim_data.get("employee_name", "Employee"),
        f"Submitted claim for eligible ₹{eligible_amt:,.2f} ({len(valid_expenses)} eligible items)",
        now_str
    ))

    conn.commit()
    conn.close()
    return claim_id

def get_claims_list(
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetches all submitted claims with flexible filtering for the Admin Portal."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM claims WHERE 1=1"
    params = []

    if status and status.lower() != "all":
        query += " AND status = ?"
        params.append(status.lower())

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query += " AND (LOWER(id) LIKE ? OR LOWER(voucher_id) LIKE ? OR LOWER(employee_name) LIKE ? OR LOWER(employee_id) LIKE ? OR LOWER(department) LIKE ?)"
        params.extend([term, term, term, term, term])

    if start_date:
        query += " AND submission_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND submission_date <= ?"
        params.append(end_date)

    query += " ORDER BY created_at DESC;"
    cursor.execute(query, params)
    claims = [dict(row) for row in cursor.fetchall()]

    # If filtering by category, attach expenses and filter claims that have matching category
    result = []
    for c in claims:
        cursor.execute("SELECT * FROM expenses WHERE claim_id = ?;", (c["id"],))
        exp_rows = [dict(r) for r in cursor.fetchall()]
        
        # Parse flags_json
        for e in exp_rows:
            try:
                e["flags"] = json.loads(e.get("flags_json") or "[]")
            except Exception:
                e["flags"] = []

        c["expenses"] = exp_rows

        if category and category.lower() != "all":
            has_cat = any(e["category"].lower() == category.lower() for e in exp_rows)
            if has_cat:
                result.append(c)
        else:
            result.append(c)

    conn.close()
    return result

def get_claim_details(claim_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single claim with its full itemized expenses and audit trail."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM claims WHERE id = ?;", (claim_id,))
    claim_row = cursor.fetchone()
    if not claim_row:
        conn.close()
        return None

    claim = dict(claim_row)
    cursor.execute("SELECT * FROM expenses WHERE claim_id = ? ORDER BY amount DESC;", (claim_id,))
    expenses = [dict(r) for r in cursor.fetchall()]
    for e in expenses:
        try:
            e["flags"] = json.loads(e.get("flags_json") or "[]")
        except Exception:
            e["flags"] = []
    claim["expenses"] = expenses

    cursor.execute("SELECT * FROM audit_logs WHERE entity_id = ? ORDER BY timestamp DESC;", (claim_id,))
    claim["audit_logs"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return claim

def update_claim_status(claim_id: str, new_status: str, rejection_reason: Optional[str] = None, reviewed_by: str = "Finance Admin") -> Dict[str, Any]:
    """Updates a claim's status ('approved', 'rejected', 'under_process') and syncs its expense records."""
    conn = get_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE claims
    SET status = ?,
        rejection_reason = ?,
        reviewed_by = ?,
        reviewed_at = ?
    WHERE id = ?;
    """, (new_status, rejection_reason, reviewed_by, now_str, claim_id))

    # Synchronize expense status in expenses table
    cursor.execute("""
    UPDATE expenses
    SET claim_status = ?
    WHERE claim_id = ?;
    """, (new_status, claim_id))

    # Add audit log
    cursor.execute("""
    INSERT INTO audit_logs (id, action, entity_type, entity_id, performed_by, details, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        str(uuid.uuid4()),
        f"STATUS_CHANGED_TO_{new_status.upper()}",
        "claim",
        claim_id,
        reviewed_by,
        f"Status changed to {new_status}. {f'Reason: {rejection_reason}' if rejection_reason else ''}",
        now_str
    ))

    conn.commit()
    conn.close()
    return {"success": True, "claim_id": claim_id, "new_status": new_status, "updated_at": now_str}

# ==============================================================================
# Database Operations: Policy Rules Management
# ==============================================================================

def get_policy_rules(active_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieves all corporate policy rules."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM policy_rules"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY created_at ASC;"

    cursor.execute(query)
    rules = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rules

def create_policy_rule(data: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new corporate policy rule."""
    conn = get_connection()
    cursor = conn.cursor()

    rule_id = data.get("id") or f"POL-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO policy_rules (
        id, rule_name, category, keywords, max_limit, limit_period,
        vendor_restriction, require_business_purpose, require_date, is_active,
        description, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        rule_id,
        data.get("rule_name", "Untitled Policy"),
        data.get("category", "General"),
        data.get("keywords", ""),
        float(data.get("max_limit", 0.0)),
        data.get("limit_period", "monthly"),
        data.get("vendor_restriction", ""),
        1 if data.get("require_business_purpose") else 0,
        1 if data.get("require_date") else 0,
        1 if data.get("is_active", True) else 0,
        data.get("description", ""),
        now_str
    ))

    cursor.execute("""
    INSERT INTO audit_logs (id, action, entity_type, entity_id, performed_by, details, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        str(uuid.uuid4()),
        "POLICY_CREATED",
        "policy_rule",
        rule_id,
        "Admin",
        f"Created policy '{data.get('rule_name')}' with limit ₹{data.get('max_limit', 0):,.2f}",
        now_str
    ))

    conn.commit()
    conn.close()
    return {"id": rule_id, **data, "created_at": now_str}

def update_policy_rule(rule_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates an existing corporate policy rule."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE policy_rules
    SET rule_name = ?,
        category = ?,
        keywords = ?,
        max_limit = ?,
        limit_period = ?,
        vendor_restriction = ?,
        require_business_purpose = ?,
        require_date = ?,
        is_active = ?,
        description = ?
    WHERE id = ?;
    """, (
        data.get("rule_name"),
        data.get("category"),
        data.get("keywords"),
        float(data.get("max_limit", 0.0)),
        data.get("limit_period"),
        data.get("vendor_restriction", ""),
        1 if data.get("require_business_purpose") else 0,
        1 if data.get("require_date") else 0,
        1 if data.get("is_active", True) else 0,
        data.get("description"),
        rule_id
    ))

    conn.commit()
    conn.close()
    return {"id": rule_id, **data}

def toggle_policy_rule(rule_id: str, is_active: bool) -> bool:
    """Toggles active status of a policy rule."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE policy_rules SET is_active = ? WHERE id = ?;", (1 if is_active else 0, rule_id))
    conn.commit()
    conn.close()
    return True

def delete_policy_rule(rule_id: str) -> bool:
    """Deletes a policy rule."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM policy_rules WHERE id = ?;", (rule_id,))
    conn.commit()
    conn.close()
    return True

# ==============================================================================
# Database Operations: Reports & Analytics
# ==============================================================================

def get_admin_reports_data() -> Dict[str, Any]:
    """Computes comprehensive analytics across claims and expenses for the Admin Portal."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. High-level KPIs
    cursor.execute("""
    SELECT 
        COUNT(*) as total_claims,
        SUM(CASE WHEN status = 'under_process' THEN 1 ELSE 0 END) as under_process_count,
        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_count,
        SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_count,
        COALESCE(SUM(total_amount), 0) as total_claimed_amount,
        COALESCE(SUM(eligible_amount), 0) as total_eligible_amount,
        COALESCE(SUM(exception_amount), 0) as total_exception_amount,
        COALESCE(SUM(CASE WHEN status = 'approved' THEN eligible_amount ELSE 0 END), 0) as total_paid_out
    FROM claims;
    """)
    kpi_row = dict(cursor.fetchone())

    # 2. Spend by Category
    cursor.execute("""
    SELECT 
        category,
        COUNT(*) as bill_count,
        SUM(amount) as total_amount,
        SUM(eligible_amount) as eligible_amount,
        SUM(exception_amount) as exception_amount
    FROM expenses
    GROUP BY category
    ORDER BY total_amount DESC;
    """)
    category_spend = [dict(r) for r in cursor.fetchall()]

    # 3. Monthly Trend
    cursor.execute("""
    SELECT 
        SUBSTR(submission_date, 1, 7) as month,
        COUNT(*) as claim_count,
        SUM(total_amount) as total_amount,
        SUM(eligible_amount) as eligible_amount,
        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_count
    FROM claims
    GROUP BY SUBSTR(submission_date, 1, 7)
    ORDER BY month ASC;
    """)
    monthly_trend = [dict(r) for r in cursor.fetchall()]

    # 4. Top Merchants by Spend
    cursor.execute("""
    SELECT 
        merchant,
        category,
        COUNT(*) as claim_frequency,
        SUM(amount) as total_spend,
        SUM(eligible_amount) as eligible_spend
    FROM expenses
    GROUP BY merchant
    ORDER BY total_spend DESC
    LIMIT 10;
    """)
    top_merchants = [dict(r) for r in cursor.fetchall()]

    # 5. Department Breakdown
    cursor.execute("""
    SELECT 
        department,
        COUNT(*) as claims_count,
        SUM(total_amount) as total_claimed,
        SUM(eligible_amount) as total_approved
    FROM claims
    GROUP BY department
    ORDER BY total_claimed DESC;
    """)
    department_spend = [dict(r) for r in cursor.fetchall()]

    # 6. Policy Exceptions / Savings
    cursor.execute("""
    SELECT 
        COUNT(*) as total_bills,
        SUM(CASE WHEN exception_amount > 0 THEN 1 ELSE 0 END) as bills_with_exceptions,
        SUM(exception_amount) as total_policy_savings
    FROM expenses;
    """)
    exceptions_summary = dict(cursor.fetchone())

    conn.close()
    return {
        "kpis": kpi_row,
        "category_spend": category_spend,
        "monthly_trend": monthly_trend,
        "top_merchants": top_merchants,
        "department_spend": department_spend,
        "exceptions_summary": exceptions_summary
    }
