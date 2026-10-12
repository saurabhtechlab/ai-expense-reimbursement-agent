import os
import shutil
import uuid
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from backend.models import ClaimSession, ExpenseItem, ChatMessage
from backend.policy_engine import CorporatePolicyEngine
from backend.extractor import DocumentExtractor
from backend.agent import ExpenseReimbursementAgent
from backend.demo_generator import generate_sample_batch_files, generate_perks_batch_files
from backend.database import (
    init_db,
    check_bill_duplicate_in_db,
    save_submitted_claim,
    get_claims_list,
    get_claim_details,
    update_claim_status,
    get_policy_rules,
    create_policy_rule,
    update_policy_rule,
    toggle_policy_rule,
    delete_policy_rule,
    get_admin_reports_data
)

# Initialize SQLite database
init_db()

app = FastAPI(title="ReimburseAI - Expense & Reimbursement Agent API", version="1.0.0")

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_receipts")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(SAMPLE_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Mount static files for receipt viewing
app.mount("/static/sample", StaticFiles(directory=SAMPLE_DIR), name="sample_receipts")
app.mount("/static/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Mount production frontend build if present
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "dist"))
if os.path.exists(FRONTEND_DIST) and os.path.exists(os.path.join(FRONTEND_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    def serve_frontend():
        return FileResponse(
            os.path.join(FRONTEND_DIST, "index.html"),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    @app.get("/admin")
    def serve_admin():
        return FileResponse(
            os.path.join(FRONTEND_DIST, "index.html"),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
else:
    from fastapi.responses import HTMLResponse

    @app.get("/")
    @app.get("/admin")
    def serve_fallback():
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ReimburseAI - Backend Ready</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #e2e8f0; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .card { background: #1e293b; border: 1px solid #334155; padding: 2.5rem; border-radius: 1rem; max-width: 520px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); text-align: center; }
                h1 { color: #818cf8; margin-top: 0; font-size: 1.5rem; }
                p { color: #94a3b8; font-size: 0.95rem; line-height: 1.5; }
                code { background: #0f172a; padding: 0.2rem 0.5rem; border-radius: 0.25rem; color: #38bdf8; font-size: 0.9rem; }
                a { display: inline-block; margin-top: 1.25rem; background: #4f46e5; color: white; padding: 0.6rem 1.25rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600; font-size: 0.9rem; }
                a:hover { background: #4338ca; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🚀 ReimburseAI Backend is Running</h1>
                <p>The FastAPI backend server is active. To enable the React single-page UI, build the frontend:</p>
                <p><code>cd frontend && npm install && npm run build</code></p>
                <p>Or start the Vite dev server for hot-reload:</p>
                <p><code>cd frontend && npm run dev</code></p>
                <a href="/docs">Open Interactive API Docs (/docs)</a>
            </div>
        </body>
        </html>
        """)

@app.get("/api/tdd-pdf")
def serve_tdd_pdf():
    pdf_path = os.path.abspath(os.path.join(BASE_DIR, "..", "TECHNICAL_DESIGN_DOCUMENT.pdf"))
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Technical Design Document PDF not found")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="TECHNICAL_DESIGN_DOCUMENT.pdf"
    )

# In-memory single active session for the pair programming / employee demo
current_session = ClaimSession()

def init_fresh_session():
    global current_session
    current_session = ClaimSession()
    welcome_msg = (
        "👋 **Welcome to ReimburseAI!**\n\n"
        "I'm your corporate expense reimbursement assistant. Drop in your receipt photos, invoices, and PDFs, "
        "or click **'Load Sample Batch'** above to test with 11 sample bills.\n\n"
        "I will extract all line items, enforce corporate travel policy, identify duplicate expenses, and ask you **only** what is necessary to get your claim ready for submission."
    )
    current_session.chat_history.append(ChatMessage(
        role="assistant",
        content=welcome_msg,
        actions=[
            {"type": "load_sample", "label": "⚡ Load Sample Batch (11 Receipts)"}
        ]
    ))

init_fresh_session()

# Request schemas
class ChatRequest(BaseModel):
    message: str

class ExpenseUpdateRequest(BaseModel):
    merchant: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    category: Optional[str] = None
    business_purpose: Optional[str] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ReimburseAI Agent",
        "openai_available": bool(os.environ.get("OPENAI_API_KEY"))
    }

@app.get("/api/session", response_model=ClaimSession)
def get_session():
    return current_session

@app.post("/api/session/reset", response_model=ClaimSession)
def reset_session():
    init_fresh_session()
    return current_session

@app.post("/api/chat", response_model=ClaimSession)
def chat_with_agent(req: ChatRequest):
    global current_session
    was_submitted_before = current_session.status == "submitted"
    current_session = ExpenseReimbursementAgent.process_user_message(current_session, req.message)
    
    # If this message resulted in a successful new submission, persist to database
    if not was_submitted_before and current_session.status == "submitted" and current_session.submission:
        try:
            sub = current_session.submission
            if current_session.summary.eligible_amount > 0:
                claim_data = {
                    "id": sub.claim_reference,
                    "voucher_id": sub.submission_id,
                    "employee_id": sub.employee_id,
                    "employee_name": sub.employee_name,
                    "department": sub.department,
                    "submission_date": datetime.now().strftime("%Y-%m-%d"),
                    "total_amount": current_session.summary.total_amount,
                    "eligible_amount": current_session.summary.eligible_amount,
                    "exception_amount": current_session.summary.exception_amount,
                    "notes": "Submitted via ReimburseAI Assistant (Chat)"
                }
                eligible_expenses_data = [exp.model_dump() for exp in current_session.expenses if (exp.eligible_amount or 0) > 0]
                save_submitted_claim(claim_data, eligible_expenses_data)
        except Exception as e:
            print(f"Error persisting chat-submitted claim to DB: {e}")

    return current_session

@app.post("/api/load-sample-batch", response_model=ClaimSession)
def load_sample_batch():
    global current_session
    # Generate files if not yet generated
    samples = generate_sample_batch_files(SAMPLE_DIR)

    # Parse each sample file into ExpenseItem
    expenses = []
    for s in samples:
        file_path = os.path.join(SAMPLE_DIR, s["file_name"])
        preview_url = f"/static/sample/{s['file_name']}"
        item = DocumentExtractor.parse_document(file_path, s["file_name"], preview_url)
        # Preserve specific intentional test attributes
        if s.get("highlight_missing") == "business_purpose":
            item.business_purpose = None
        elif s.get("business_purpose"):
            item.business_purpose = s["business_purpose"]
            
        if s.get("highlight_missing") == "date":
            item.date = None
        elif s.get("date"):
            item.date = s["date"]
            
        expenses.append(item)

    current_session.expenses = expenses
    current_session.status = "clarification_pending"

    # Evaluate all expenses through corporate policy engine
    current_session.expenses, current_session.pending_questions, current_session.summary = CorporatePolicyEngine.evaluate_all(current_session.expenses)

    # Add initial user action simulation message
    current_session.chat_history.append(ChatMessage(
        role="user",
        content="I want to claim my expenses. (Uploaded 8 receipt photos, 2 PDFs, 1 hotel invoice, 1 taxi receipt)"
    ))

    # Add agent's response message
    agent_msg = ExpenseReimbursementAgent.generate_batch_analysis_message(current_session)
    current_session.chat_history.append(agent_msg)

    return current_session

@app.post("/api/load-perks-batch", response_model=ClaimSession)
def load_perks_batch():
    global current_session
    perks = generate_perks_batch_files(SAMPLE_DIR)

    expenses = []
    for p in perks:
        file_path = os.path.join(SAMPLE_DIR, p["file_name"])
        preview_url = f"/static/sample/{p['file_name']}"
        item = DocumentExtractor.parse_document(file_path, p["file_name"], preview_url)
        if p.get("business_purpose"):
            item.business_purpose = p["business_purpose"]
        if p.get("date"):
            item.date = p["date"]
        expenses.append(item)

    current_session.expenses = expenses
    current_session.status = "ready_for_review"

    # Evaluate all expenses through corporate policy engine
    current_session.expenses, current_session.pending_questions, current_session.summary = CorporatePolicyEngine.evaluate_all(current_session.expenses)

    current_session.chat_history.append(ChatMessage(
        role="user",
        content="I want to claim my benefits & travel expenses: Mobile Headset bills, Driver Salary, and Fuel receipts."
    ))

    agent_msg = ExpenseReimbursementAgent.generate_batch_analysis_message(current_session)
    current_session.chat_history.append(agent_msg)

    return current_session

@app.post("/api/upload", response_model=ClaimSession)
async def upload_receipts(files: List[UploadFile] = File(...)):
    global current_session
    saved_items = []
    blocked_duplicates = []
    
    for file in files:
        # Read file binary to compute SHA-256 hash for exact-duplicate detection
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()

        # 1. Check if identical bill is already in the SQLite database (under_process or approved)
        db_dup = check_bill_duplicate_in_db(
            file_hash=file_hash,
            file_name=file.filename
        )
        if db_dup:
            blocked_duplicates.append({
                "file_name": file.filename,
                "reason": "db_duplicate",
                "claim_id": db_dup.get("claim_id"),
                "claim_status": db_dup.get("claim_status"),
                "matched_merchant": db_dup.get("merchant"),
                "matched_amount": db_dup.get("amount")
            })
            continue

        # 2. Check if identical bill is already in current active session
        existing_dup = next(
            (e for e in current_session.expenses if (e.file_hash and e.file_hash == file_hash) or e.file_name.lower() == file.filename.lower()),
            None
        )

        # 3. Check if identical bill is already processed within this same batch
        batch_dup = next(
            (e for e in saved_items if (e.file_hash and e.file_hash == file_hash) or e.file_name.lower() == file.filename.lower()),
            None
        )

        if existing_dup:
            blocked_duplicates.append({
                "file_name": file.filename,
                "reason": "already_in_claim",
                "matched_merchant": existing_dup.merchant,
                "matched_amount": existing_dup.amount
            })
            continue
        elif batch_dup:
            blocked_duplicates.append({
                "file_name": file.filename,
                "reason": "batch_duplicate",
                "matched_merchant": batch_dup.merchant,
                "matched_amount": batch_dup.amount
            })
            continue

        # Unique receipt: save to disk and extract
        unique_name = f"{uuid.uuid4().hex[:6]}_{file.filename}"
        dest_path = os.path.join(UPLOADS_DIR, unique_name)
        with open(dest_path, "wb") as buffer:
            buffer.write(content)

        preview_url = f"/static/uploads/{unique_name}"
        item = DocumentExtractor.parse_document(dest_path, file.filename, preview_url)
        item.file_hash = file_hash

        # Check post-extraction: does vendor + amount match an under_process or approved bill in DB?
        post_db_dup = check_bill_duplicate_in_db(
            file_hash=file_hash,
            merchant=item.merchant,
            amount=item.amount,
            date=item.date,
            file_name=file.filename
        )
        if post_db_dup:
            blocked_duplicates.append({
                "file_name": file.filename,
                "reason": "db_duplicate",
                "claim_id": post_db_dup.get("claim_id"),
                "claim_status": post_db_dup.get("claim_status"),
                "matched_merchant": post_db_dup.get("merchant"),
                "matched_amount": post_db_dup.get("amount")
            })
            continue

        saved_items.append(item)

    if saved_items:
        current_session.expenses.extend(saved_items)
        # Run Policy Engine evaluation
        current_session.expenses, current_session.pending_questions, current_session.summary = CorporatePolicyEngine.evaluate_all(current_session.expenses)
        
        if len(current_session.pending_questions) > 0:
            current_session.status = "clarification_pending"
        else:
            current_session.status = "ready_for_review"

    # Log user action in chat
    total_uploaded = len(files)
    current_session.chat_history.append(ChatMessage(
        role="user",
        content=f"Uploaded {total_uploaded} receipt file{'s' if total_uploaded > 1 else ''} for reimbursement."
    ))

    # Construct Agent response with Duplicate Upload Shield notifications
    db_blocked = [d for d in blocked_duplicates if d.get("reason") == "db_duplicate"]
    session_blocked = [d for d in blocked_duplicates if d.get("reason") != "db_duplicate"]

    if db_blocked and not saved_items:
        dup_details = "\n".join([
            f"• **{d['file_name']}** ({d['matched_merchant']} - ₹{d['matched_amount']:,.0f}) is already registered under **Claim #{d['claim_id']}** (Status: **{d['claim_status'].upper()}**)."
            for d in db_blocked
        ])
        agent_msg = ChatMessage(
            role="assistant",
            content=(
                f"🚫 **Database Duplicate Shield: Bill Blocked**\n\n"
                f"I detected that the bill(s) you uploaded are already registered in the corporate reimbursement system:\n\n"
                f"{dup_details}\n\n"
                f"Under company financial policy, bills that are currently **under process** or **approved** cannot be entered into the system again at any time."
            )
        )
        current_session.chat_history.append(agent_msg)
    elif session_blocked and not saved_items:
        dup_names = ", ".join([f"'{d['file_name']}'" for d in session_blocked])
        dup_details = "\n".join([f"• **{d['file_name']}** matches active claim: **{d['matched_merchant']}** (₹{d['matched_amount']:,.0f})" for d in session_blocked])
        agent_msg = ChatMessage(
            role="assistant",
            content=(
                f"🛡️ **Duplicate Upload Shield: Duplicate Bill Blocked**\n\n"
                f"I detected that the bill(s) you just uploaded ({dup_names}) have **already been added** to your active reimbursement claim:\n\n"
                f"{dup_details}\n\n"
                f"To keep your claim clean and prevent accidental double-billing, duplicate uploads are prevented.\n\n"
                f"Your active claim contains **{current_session.summary.total_count} expenses** totaling **₹{current_session.summary.total_amount:,.0f}**."
            )
        )
        current_session.chat_history.append(agent_msg)
    elif blocked_duplicates and saved_items:
        dup_details = ", ".join([f"'{d['file_name']}'" for d in blocked_duplicates])
        agent_msg = ExpenseReimbursementAgent.generate_batch_analysis_message(current_session)
        agent_msg.content = (
            f"🛡️ **Duplicate Upload Shield**: Skipped duplicate file(s) ({dup_details}) as they are already recorded in your claim or database.\n\n"
            + agent_msg.content
        )
        current_session.chat_history.append(agent_msg)
    else:
        # Normal fresh upload batch
        agent_msg = ExpenseReimbursementAgent.generate_batch_analysis_message(current_session)
        current_session.chat_history.append(agent_msg)

    return current_session

@app.post("/api/expenses/{expense_id}/update", response_model=ClaimSession)
def update_expense(expense_id: str, req: ExpenseUpdateRequest):
    global current_session
    found = False
    for exp in current_session.expenses:
        if exp.id == expense_id:
            if req.merchant is not None:
                exp.merchant = req.merchant
            if req.amount is not None:
                exp.amount = req.amount
            if req.date is not None:
                exp.date = req.date
            if req.category is not None:
                exp.category = req.category
            if req.business_purpose is not None:
                exp.business_purpose = req.business_purpose
            found = True
            break
            
    if not found:
        raise HTTPException(status_code=404, detail="Expense item not found")

    # Re-evaluate policies
    current_session.expenses, current_session.pending_questions, current_session.summary = CorporatePolicyEngine.evaluate_all(current_session.expenses)
    
    if len(current_session.pending_questions) == 0 and current_session.summary.total_count > 0:
        current_session.status = "ready_for_review"
    return current_session

@app.delete("/api/expenses/{expense_id}", response_model=ClaimSession)
def delete_expense(expense_id: str):
    global current_session
    removed = [e for e in current_session.expenses if e.id == expense_id]
    current_session.expenses = [e for e in current_session.expenses if e.id != expense_id]
    current_session.expenses, current_session.pending_questions, current_session.summary = CorporatePolicyEngine.evaluate_all(current_session.expenses)
    
    if len(current_session.pending_questions) > 0:
        current_session.status = "clarification_pending"
    elif current_session.summary.total_count > 0:
        current_session.status = "ready_for_review"
    else:
        current_session.status = "idle"

    if removed:
        r = removed[0]
        current_session.chat_history.append(ChatMessage(
            role="assistant",
            content=f"🗑️ Removed **{r.merchant}** (₹{r.amount:,.0f}) from your claim. Your total is now **₹{current_session.summary.total_amount:,.0f}** across **{current_session.summary.total_count} expenses**."
        ))

    return current_session

@app.post("/api/submit-claim", response_model=ClaimSession)
def submit_claim():
    global current_session
    if not current_session.expenses:
        raise HTTPException(status_code=400, detail="Cannot submit an empty claim")
    if current_session.summary.eligible_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot submit a claim with ₹0 eligible reimbursement. Only claims with approved/eligible expenses can be submitted."
        )
    if len(current_session.pending_questions) > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot submit claim while clarification questions are pending. Please resolve pending questions first."
        )

    current_session = ExpenseReimbursementAgent.submit_claim(current_session)

    # Persist claim and ONLY eligible itemized receipts into SQLite database for Admin oversight
    try:
        sub = current_session.submission
        if sub and current_session.summary.eligible_amount > 0:
            claim_data = {
                "id": sub.claim_reference,
                "voucher_id": sub.submission_id,
                "employee_id": sub.employee_id,
                "employee_name": sub.employee_name,
                "department": sub.department,
                "submission_date": datetime.now().strftime("%Y-%m-%d"),
                "total_amount": current_session.summary.total_amount,
                "eligible_amount": current_session.summary.eligible_amount,
                "exception_amount": current_session.summary.exception_amount,
                "notes": "Submitted via ReimburseAI Assistant"
            }
            # Strictly filter: only expenses with eligible_amount > 0 are persisted
            eligible_expenses_data = [exp.model_dump() for exp in current_session.expenses if (exp.eligible_amount or 0) > 0]
            save_submitted_claim(claim_data, eligible_expenses_data)
    except Exception as e:
        print(f"Error persisting claim to DB: {e}")

    return current_session

@app.get("/api/claim-voucher")
def get_claim_voucher():
    if not current_session.submission:
        raise HTTPException(status_code=400, detail="Claim has not been submitted yet")
    return {
        "voucher": current_session.submission,
        "summary": current_session.summary,
        "expenses": [e for e in current_session.expenses if (e.eligible_amount or 0) > 0],
        "excluded_ineligible_expenses": [e for e in current_session.expenses if (e.eligible_amount or 0) <= 0]
    }

# ==============================================================================
# Admin Portal Endpoints
# ==============================================================================

class ClaimStatusUpdateRequest(BaseModel):
    status: str  # 'approved', 'rejected', 'under_process'
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[str] = "Finance Admin"

class PolicyRuleRequest(BaseModel):
    rule_name: str
    category: str
    keywords: str
    max_limit: float
    limit_period: str  # 'financial_year', 'monthly', 'per_claim', 'no_limit'
    vendor_restriction: Optional[str] = ""
    require_business_purpose: Optional[bool] = False
    require_date: Optional[bool] = False
    is_active: Optional[bool] = True
    description: Optional[str] = ""

class PolicyToggleRequest(BaseModel):
    is_active: bool

@app.get("/api/admin/claims")
def api_admin_get_claims(
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Admin endpoint: Get all submitted records with dynamic multi-field filtering."""
    return get_claims_list(status, category, search, start_date, end_date)

@app.get("/api/admin/claims/{claim_id}")
def api_admin_get_claim_detail(claim_id: str):
    """Admin endpoint: Get full claim details, itemized receipts, and audit trail."""
    claim = get_claim_details(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

@app.post("/api/admin/claims/{claim_id}/status")
def api_admin_update_claim_status(claim_id: str, req: ClaimStatusUpdateRequest):
    """Admin endpoint: Approve, reject, or mark claim under process."""
    return update_claim_status(claim_id, req.status, req.rejection_reason, req.reviewed_by or "Finance Admin")

@app.get("/api/admin/reports")
def api_admin_get_reports():
    """Admin endpoint: Aggregate reports for spend, category, monthly trends, and compliance."""
    return get_admin_reports_data()

@app.get("/api/admin/policies")
def api_admin_get_policies(active_only: bool = False):
    """Admin endpoint: View all configured corporate policy rules."""
    return get_policy_rules(active_only)

@app.post("/api/admin/policies")
def api_admin_create_policy(req: PolicyRuleRequest):
    """Admin endpoint: Configure and add a new corporate policy rule."""
    return create_policy_rule(req.model_dump())

@app.put("/api/admin/policies/{policy_id}")
def api_admin_update_policy(policy_id: str, req: PolicyRuleRequest):
    """Admin endpoint: Update an existing corporate policy rule."""
    updated = update_policy_rule(policy_id, req.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    return updated

@app.post("/api/admin/policies/{policy_id}/toggle")
def api_admin_toggle_policy(policy_id: str, req: PolicyToggleRequest):
    """Admin endpoint: Toggle a policy rule on or off."""
    toggle_policy_rule(policy_id, req.is_active)
    return {"success": True, "policy_id": policy_id, "is_active": req.is_active}

@app.delete("/api/admin/policies/{policy_id}")
def api_admin_delete_policy(policy_id: str):
    """Admin endpoint: Delete a policy rule."""
    delete_policy_rule(policy_id)
    return {"success": True, "policy_id": policy_id}
