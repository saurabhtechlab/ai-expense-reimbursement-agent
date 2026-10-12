from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class LineItem(BaseModel):
    item: str
    quantity: int = 1
    amount: float

class ExpenseFlag(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"
    field: Optional[str] = None

class ExpenseItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: Optional[str] = None
    file_name: str
    file_hash: Optional[str] = None
    file_type: str = "image/png"
    preview_url: Optional[str] = None
    merchant: str
    amount: float
    currency: str = "₹"
    date: Optional[str] = None
    category: str = "Other"
    tax_amount: Optional[float] = 0.0
    payment_method: Optional[str] = "Personal Card"
    business_purpose: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    
    # State tracking
    status: Literal["ready", "clarification_needed", "duplicate", "policy_violation"] = "ready"
    flags: List[ExpenseFlag] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None
    is_duplicate_of: Optional[str] = None  # Reference to other expense ID
    
    # Financial breakdown
    eligible_amount: float = 0.0
    exception_amount: float = 0.0
    confidence: float = 0.95
    raw_ocr_text: Optional[str] = None

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%I:%M %p"))
    actions: Optional[List[Dict[str, Any]]] = None
    summary_card: Optional[Dict[str, Any]] = None

class ClarificationQuestion(BaseModel):
    expense_id: str
    question_number: int
    field: str
    prompt: str
    current_value: Optional[str] = None
    quick_suggestions: Optional[List[str]] = None

class ClaimSummary(BaseModel):
    total_count: int = 0
    ready_count: int = 0
    clarification_count: int = 0
    duplicate_count: int = 0
    total_amount: float = 0.0
    eligible_amount: float = 0.0
    exception_amount: float = 0.0
    currency: str = "₹"

class CorporateSubmission(BaseModel):
    submission_id: str
    claim_reference: str
    submitted_at: str
    employee_name: str
    employee_id: str
    department: str
    total_amount: float
    eligible_amount: float
    exceptions_amount: float
    status: str = "Approved - Pending Finance Disbursement"
    audit_id: str
    approval_route: str = "Manager Approved -> Auto Policy Check Passed -> ERP Synced"

class ClaimSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_name: str = "Saurabh Gupta"
    employee_id: str = "EMP-4091"
    department: str = "Product Engineering"
    expenses: List[ExpenseItem] = Field(default_factory=list)
    pending_questions: List[ClarificationQuestion] = Field(default_factory=list)
    chat_history: List[ChatMessage] = Field(default_factory=list)
    summary: ClaimSummary = Field(default_factory=ClaimSummary)
    submission: Optional[CorporateSubmission] = None
    status: Literal["draft", "clarification_pending", "ready_for_review", "submitted"] = "draft"
