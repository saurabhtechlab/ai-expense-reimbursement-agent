import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.models import ClaimSession, ChatMessage, CorporateSubmission
from backend.policy_engine import CorporatePolicyEngine

class ExpenseReimbursementAgent:
    """
    Intelligent conversational agent managing user interactions, Q&A clarification,
    policy reconciliation, and corporate claim compilation.
    """

    @classmethod
    def process_user_message(cls, session: ClaimSession, user_text: str) -> ClaimSession:
        # Append user message
        session.chat_history.append(ChatMessage(
            role="user",
            content=user_text
        ))

        cleaned_text = user_text.strip()
        lower_text = cleaned_text.lower()

        # Check if user wants to start fresh or greeting
        if any(greet in lower_text for greet in ["hello", "hi", "hey", "start", "i want to claim my expenses", "claim my expenses"]) and len(session.expenses) == 0:
            welcome_msg = (
                "👋 Hello! I'm your AI Reimbursement Assistant.\n\n"
                "Simply drop your receipt photos, invoices, and PDFs here (or click **'Load Sample Batch'** in the top bar). "
                "I'll automatically parse line items, check corporate travel policy, identify duplicates, and only ask you for details that are truly missing."
            )
            session.chat_history.append(ChatMessage(
                role="assistant",
                content=welcome_msg,
                actions=[{"type": "load_sample", "label": "⚡ Load Sample Batch (11 Receipts)"}]
            ))
            return session

        # Check if user wants to submit claim
        if any(cmd in lower_text for cmd in ["submit claim", "submit", "confirm submission", "file claim"]):
            if session.summary.eligible_amount <= 0:
                block_msg = (
                    "⚠️ **Submission Blocked: ₹0 Eligible Amount**\n\n"
                    "Your claim currently has **₹0.00** in eligible reimbursement (all items are either duplicates or violate company expense policy).\n\n"
                    "Under corporate financial policy, claims with ₹0 eligible amount cannot be submitted into the system. "
                    "Please upload valid, eligible receipts or adjust expense details before submitting."
                )
                session.chat_history.append(ChatMessage(
                    role="assistant",
                    content=block_msg,
                    actions=[
                        {"type": "review_claim", "label": "📋 Review Claim"},
                        {"type": "load_sample", "label": "⚡ Load Sample Batch (11 Receipts)"}
                    ]
                ))
                return session
            return cls.submit_claim(session)

        # Check if user is asking about policy rules
        if any(q in lower_text for q in ["policy", "rules", "headset", "driver", "fuel", "reliance digital", "allowance", "limits"]):
            policy_info = (
                "📖 **Corporate Reimbursement Policy Guide:**\n\n"
                "1. 🎧 **Mobile Headset Reimbursement:**\n"
                "   • Allowance: Up to **₹20,000** in one financial year.\n"
                "   • Vendor Restriction: Invoice **MUST be from Reliance Digital** (non-Reliance vendors like Croma or Amazon are not eligible).\n\n"
                "2. 🚗 **Travel Assistance (Driver Salary):**\n"
                "   • Allowance: Up to **₹10,000 per month**.\n"
                "   • Requirement: Service month must be indicated on voucher.\n\n"
                "3. ⛽ **Fuel Expenses:**\n"
                "   • Allowance: Up to **₹15,000 per month** with fuel station tax receipt.\n\n"
                "4. 🏨 **Hotel Accommodations:** Standard allowance up to ₹8,000/night (business purpose required).\n"
                "5. 🚕 **Taxi / Ground Transport:** Travel date mandatory.\n"
                "6. 🔴 **Duplicate Prevention:** Identical amount & vendor submissions are excluded automatically."
            )
            session.chat_history.append(ChatMessage(
                role="assistant",
                content=policy_info,
                actions=[
                    {"type": "load_perks", "label": "⚡ Test Headset, Driver & Fuel Batch"},
                    {"type": "load_sample", "label": "⚡ Test 11-Receipt Prompt Batch"}
                ]
            ))
            return session

        # Check if user wants to review claim
        if any(cmd in lower_text for cmd in ["review claim", "review", "show breakdown", "breakdown"]):
            review_msg = (
                f"📋 **Expense Claim Breakdown (Session #{session.session_id[:8]}):**\n\n"
                f"• **Total Receipts:** {session.summary.total_count} items (₹{session.summary.total_amount:,.2f})\n"
                f"• **Eligible for Reimbursement:** ₹{session.summary.eligible_amount:,.2f}\n"
                f"• **Exceptions / Exclusions:** ₹{session.summary.exception_amount:,.2f}\n\n"
                f"**Category Breakdown:**\n"
            )
            cat_totals = {}
            for exp in session.expenses:
                cat_totals[exp.category] = cat_totals.get(exp.category, 0.0) + exp.amount
            for cat, amt in cat_totals.items():
                review_msg += f"  - {cat}: ₹{amt:,.2f}\n"

            actions = []
            if session.summary.eligible_amount > 0:
                actions.append({"type": "submit_claim", "label": "🚀 Submit Claim"})
            actions.append({"type": "export_json", "label": "📥 Download Claim JSON"})

            session.chat_history.append(ChatMessage(
                role="assistant",
                content=review_msg,
                actions=actions
            ))
            return session

        # Check if user is answering clarification questions
        if session.pending_questions:
            resolved = cls._resolve_pending_questions(session, cleaned_text)
            if resolved:
                # Re-evaluate all expenses with policy engine
                session.expenses, session.pending_questions, session.summary = CorporatePolicyEngine.evaluate_all(session.expenses)

                if len(session.pending_questions) == 0:
                    session.status = "ready_for_review"
                    ready_msg = (
                        "Great. Your claim is now ready.\n\n"
                        f"**Total:** ₹{int(session.summary.total_amount):,}\n"
                        f"**Eligible:** ₹{int(session.summary.eligible_amount):,}\n"
                        f"**Exceptions:** ₹{int(session.summary.exception_amount):,}"
                    )
                    ready_actions = [{"type": "review_claim", "label": "Review Claim"}]
                    if session.summary.eligible_amount > 0:
                        ready_actions.append({"type": "submit_claim", "label": "Submit Claim"})

                    session.chat_history.append(ChatMessage(
                        role="assistant",
                        content=ready_msg,
                        actions=ready_actions,
                        summary_card={
                            "total": session.summary.total_amount,
                            "eligible": session.summary.eligible_amount,
                            "exceptions": session.summary.exception_amount,
                            "count": session.summary.total_count
                        }
                    ))
                    return session
                else:
                    # Still some questions pending
                    still_needed_msg = f"Thank you. I recorded those details, but still need clarification on {len(session.pending_questions)} item(s):\n\n"
                    for q in session.pending_questions:
                        still_needed_msg += f"{q.question_number}. {q.prompt}\n"
                    session.chat_history.append(ChatMessage(
                        role="assistant",
                        content=still_needed_msg
                    ))
                    return session

        # Default conversational response
        default_actions = [{"type": "review_claim", "label": "Review Claim"}]
        if session.summary.eligible_amount > 0:
            default_actions.append({"type": "submit_claim", "label": "Submit Claim"})

        session.chat_history.append(ChatMessage(
            role="assistant",
            content="I've noted that. You can review your expenses or proceed to submit whenever you're ready.",
            actions=default_actions
        ))
        return session

    @classmethod
    def _resolve_pending_questions(cls, session: ClaimSession, user_input: str) -> bool:
        """
        Parses answers provided by user either via:
        1. Numbered format (e.g. '1. Client meeting in Bangalore \n 2. 24 September')
        2. Line-by-line format
        3. Inline / natural language
        """
        updated_any = False

        # Pattern 1: Numbered lines: "1. Client meeting in Bangalore\n2. 24 September" or "1) ... 2) ..."
        numbered_lines = re.findall(r'(?:^|\n)\s*(\d+)[\.\)\:\-]\s*([^\n]+)', user_input)
        if numbered_lines:
            for num_str, answer_text in numbered_lines:
                q_num = int(num_str)
                ans = answer_text.strip()
                for q in session.pending_questions:
                    if q.question_number == q_num:
                        cls._apply_answer_to_expense(session, q.expense_id, q.field, ans)
                        updated_any = True
            if updated_any:
                return True

        # Pattern 2: Multi-line matching line count with question count
        lines = [line.strip() for line in user_input.split("\n") if line.strip()]
        if len(lines) == len(session.pending_questions):
            for idx, q in enumerate(session.pending_questions):
                clean_ans = re.sub(r'^\d+[\.\)\:\-]\s*', '', lines[idx]).strip()
                cls._apply_answer_to_expense(session, q.expense_id, q.field, clean_ans)
                updated_any = True
            if updated_any:
                return True

        # Pattern 3: Inline numbers e.g. "1. Client meeting in Bangalore, 2. 24 September"
        inline_matches = re.findall(r'(?:^|[,\;])\s*(\d+)[\.\)\:\-]\s*([^,\;]+)', user_input)
        if inline_matches:
            for num_str, answer_text in inline_matches:
                q_num = int(num_str)
                ans = answer_text.strip()
                for q in session.pending_questions:
                    if q.question_number == q_num:
                        cls._apply_answer_to_expense(session, q.expense_id, q.field, ans)
                        updated_any = True
            if updated_any:
                return True

        # Pattern 4: Semantic keyword matching
        date_pattern = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', user_input, re.IGNORECASE)
        for q in session.pending_questions:
            if q.field == "date" and date_pattern:
                cls._apply_answer_to_expense(session, q.expense_id, "date", date_pattern.group(1))
                updated_any = True
            elif q.field == "business_purpose":
                purpose_match = re.search(r'(?:client\s+meeting[^\n,\.]*|project[^\n,\.]*|onsite[^\n,\.]*|conference[^\n,\.]*)', user_input, re.IGNORECASE)
                if purpose_match:
                    cls._apply_answer_to_expense(session, q.expense_id, "business_purpose", purpose_match.group(0).strip())
                    updated_any = True
                elif len(session.pending_questions) == 1:
                    cls._apply_answer_to_expense(session, q.expense_id, "business_purpose", user_input.strip())
                    updated_any = True

        return updated_any

    @classmethod
    def _apply_answer_to_expense(cls, session: ClaimSession, expense_id: str, field: str, value: str):
        for exp in session.expenses:
            if exp.id == expense_id:
                if field == "business_purpose":
                    exp.business_purpose = value
                elif field == "date":
                    exp.date = value
                elif field == "merchant":
                    exp.merchant = value
                break

    @classmethod
    def generate_batch_analysis_message(cls, session: ClaimSession) -> ChatMessage:
        """
        Creates the standardized user-facing prompt response:
        'I found 11 expenses totaling ₹38,420.
        ✅ 8 expenses are ready
        ⚠️ 2 need clarification
        🔴 1 appears to be a duplicate
        I only need 2 answers from you:
        1. The ₹4,850 hotel expense is missing the business purpose. What was the purpose?
        2. The ₹1,200 taxi receipt doesn't show the travel date. What was the date?'
        """
        s = session.summary
        msg = f"I found **{s.total_count} expenses** totaling **₹{int(s.total_amount):,}**.\n\n"
        msg += f"✅ **{s.ready_count} expenses** are ready\n"
        if s.clarification_count > 0:
            msg += f"⚠️ **{s.clarification_count}** need clarification\n"
        if s.duplicate_count > 0:
            msg += f"🔴 **{s.duplicate_count}** appears to be a duplicate\n"

        violations = [e for e in session.expenses if e.status == "policy_violation"]
        if violations:
            msg += f"🚫 **{len(violations)}** policy violation (non-approved vendor / ineligible expense)\n"

        capped_items = [e for e in session.expenses if e.status == "ready" and e.exception_amount > 0]
        if capped_items:
            msg += f"⚖️ **{len(capped_items)}** capped by policy allowances (excess routed to exceptions)\n"

        if session.pending_questions:
            q_count = len(session.pending_questions)
            msg += f"\nI only need **{q_count} answer{'s' if q_count > 1 else ''}** from you:\n"
            for q in session.pending_questions:
                msg += f"**{q.question_number}.** {q.prompt}\n"

        quick_replies = []
        if len(session.pending_questions) == 2:
            quick_replies.append({
                "type": "quick_answer",
                "label": "⚡ Send answers: 1. Client meeting in Bangalore, 2. 24 September",
                "payload": "1. Client meeting in Bangalore\n2. 24 September"
            })
        elif len(session.pending_questions) == 0 and s.total_count > 0:
            quick_replies.append({"type": "review_claim", "label": "📋 Review Claim"})
            if s.eligible_amount > 0:
                quick_replies.append({"type": "submit_claim", "label": "🚀 Submit Claim"})

        return ChatMessage(
            role="assistant",
            content=msg,
            actions=quick_replies,
            summary_card={
                "total": s.total_amount,
                "eligible": s.eligible_amount,
                "exceptions": s.exception_amount,
                "count": s.total_count,
                "ready": s.ready_count,
                "clarification": s.clarification_count,
                "duplicate": s.duplicate_count
            }
        )

    @classmethod
    def submit_claim(cls, session: ClaimSession) -> ClaimSession:
        """
        Finalizes claim submission to corporate reimbursement system.
        Only claims and expenses with eligible_amount > 0 can be submitted.
        """
        if session.summary.eligible_amount <= 0:
            block_msg = (
                "⚠️ **Submission Blocked: ₹0 Eligible Reimbursement**\n\n"
                "Your claim currently has **₹0.00 in eligible reimbursement**. "
                "Under corporate financial policy, claims with ₹0 eligible amount cannot be submitted into the system.\n\n"
                "Please upload valid, eligible receipts or adjust expense details before submitting."
            )
            session.chat_history.append(ChatMessage(
                role="assistant",
                content=block_msg,
                actions=[
                    {"type": "review_claim", "label": "📋 Review Claim"},
                    {"type": "load_sample", "label": "⚡ Load Sample Batch (11 Receipts)"}
                ]
            ))
            return session

        # Filter submitted expenses: only expenses with eligible_amount > 0 are submitted
        submitted_expenses = [e for e in session.expenses if (e.eligible_amount or 0) > 0]
        excluded_count = len(session.expenses) - len(submitted_expenses)

        sub_id = f"SUB-{uuid.uuid4().hex[:8].upper()}"
        claim_ref = f"CLM-2026-{uuid.uuid4().hex[:4].upper()}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        submission = CorporateSubmission(
            submission_id=sub_id,
            claim_reference=claim_ref,
            submitted_at=timestamp,
            employee_name=session.employee_name,
            employee_id=session.employee_id,
            department=session.department,
            total_amount=session.summary.total_amount,
            eligible_amount=session.summary.eligible_amount,
            exceptions_amount=session.summary.exception_amount,
            status="Approved - Synced with Corporate Finance ERP",
            audit_id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
            approval_route="Employee Submitted -> Policy Check Auto-Approved -> Queued for Direct Bank Deposit"
        )

        session.submission = submission
        session.status = "submitted"

        exclusion_note = ""
        if excluded_count > 0:
            exclusion_note = f"\n• **Excluded Ineligible Items:** {excluded_count} item(s) with ₹0 eligible amount (duplicates / policy violations) were strictly excluded from final submission."

        submit_msg = (
            f"🎉 **Claim Successfully Submitted!**\n\n"
            f"• **Claim Reference:** `{claim_ref}`\n"
            f"• **Employee:** {session.employee_name} ({session.employee_id}) — {session.department}\n"
            f"• **Total Claimed:** ₹{session.summary.total_amount:,.2f}\n"
            f"• **Approved Reimbursement:** **₹{session.summary.eligible_amount:,.2f}** ({len(submitted_expenses)} eligible item{'s' if len(submitted_expenses) > 1 else ''} queued for payroll cycle)\n"
            f"• **Policy Exceptions:** ₹{session.summary.exception_amount:,.2f}{exclusion_note}\n"
            f"• **Status:** *{submission.status}*\n\n"
            f"An audit log `{submission.audit_id}` has been securely recorded."
        )

        session.chat_history.append(ChatMessage(
            role="assistant",
            content=submit_msg,
            actions=[
                {"type": "download_summary", "label": "📄 Download Claim Voucher (JSON)"},
                {"type": "new_session", "label": "🔄 Start New Claim"}
            ]
        ))
        return session
