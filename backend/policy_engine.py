import re
from typing import List, Tuple, Dict, Optional
from backend.models import ExpenseItem, ExpenseFlag, ClarificationQuestion, ClaimSummary

def extract_month_key(date_str: Optional[str]) -> str:
    if not date_str:
        return "Current Month"
    # Match month names
    m_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)', date_str, re.IGNORECASE)
    if m_match:
        # Check if year is present
        y_match = re.search(r'20\d{2}', date_str)
        yr = f" {y_match.group(0)}" if y_match else ""
        return f"{m_match.group(0).capitalize()}{yr}"
    ym_match = re.search(r'(\d{4})[-/](\d{1,2})', date_str)
    if ym_match:
        return f"{ym_match.group(1)}-{int(ym_match.group(2)):02d}"
    return "Current Month"

class CorporatePolicyEngine:
    """
    Enforces corporate expense policies, validates mandatory fields,
    detects duplicate receipts, and isolates policy exceptions.
    
    Includes specific policies:
    1. Mobile Headset: Max ₹20,000 / Financial Year. MUST be from Reliance Digital.
    2. Travel Assistance: Max ₹10,000 / month for Driver Salary.
    3. Fuel Expenses: Max ₹15,000 / month.
    4. Hotel Accommodations: Max ₹8,000 / day standard cap; requires business purpose.
    5. Taxi & Ground Transport: Mandatory travel date.
    """
    
    HOTEL_DAILY_CAP = 8000.0
    MEAL_DAILY_CAP = 2500.0
    HEADSET_ANNUAL_CAP = 20000.0
    DRIVER_SALARY_MONTHLY_CAP = 10000.0
    FUEL_MONTHLY_CAP = 15000.0
    
    @classmethod
    def evaluate_all(cls, expenses: List[ExpenseItem]) -> Tuple[List[ExpenseItem], List[ClarificationQuestion], ClaimSummary]:
        # Reset evaluation state on expenses
        for exp in expenses:
            exp.flags = []
            exp.status = "ready"
            exp.is_duplicate_of = None
            exp.eligible_amount = exp.amount
            exp.exception_amount = 0.0
            exp.clarification_prompt = None

        # 1. Duplicate Detection Pass
        n = len(expenses)
        for i in range(n):
            for j in range(i + 1, n):
                exp1 = expenses[i]
                exp2 = expenses[j]
                
                # Check for duplicate: identical file hash OR (identical amount and matching merchant)
                is_same_hash = bool(exp1.file_hash and exp2.file_hash and exp1.file_hash == exp2.file_hash)
                is_same_merchant = exp1.merchant.strip().lower() == exp2.merchant.strip().lower()
                is_same_amount = abs(exp1.amount - exp2.amount) < 0.01
                
                if is_same_hash or (is_same_merchant and is_same_amount):
                    exp2.status = "duplicate"
                    exp2.is_duplicate_of = exp1.id
                    exp2.eligible_amount = 0.0
                    exp2.exception_amount = exp2.amount
                    if not any(f.code == "DUPLICATE_RECEIPT" for f in exp2.flags):
                        exp2.flags.append(ExpenseFlag(
                            code="DUPLICATE_RECEIPT",
                            message=f"Duplicate detected: Matches Receipt from {exp1.merchant} (₹{exp1.amount:,.0f})",
                            severity="error",
                            field="amount"
                        ))

        # 1b. Database Historical Duplicate Pass: Check against under_process / approved bills
        try:
            from backend.database import check_bill_duplicate_in_db
            for exp in expenses:
                if exp.status == "duplicate":
                    continue
                db_dup = check_bill_duplicate_in_db(
                    file_hash=exp.file_hash,
                    merchant=exp.merchant,
                    amount=exp.amount,
                    date=exp.date,
                    file_name=exp.file_name
                )
                if db_dup:
                    exp.status = "policy_violation"
                    exp.eligible_amount = 0.0
                    exp.exception_amount = exp.amount
                    status_lbl = db_dup.get("claim_status", "under_process").upper()
                    if not any(f.code == "ALREADY_SUBMITTED_IN_DB" for f in exp.flags):
                        exp.flags.append(ExpenseFlag(
                            code="ALREADY_SUBMITTED_IN_DB",
                            message=f"Duplicate in System: Already registered in Claim #{db_dup.get('claim_id')} ({status_lbl}). Cannot be claimed again.",
                            severity="error",
                            field="amount"
                        ))
        except Exception as e:
            pass

        # 2. Rule Validation Pass (for non-duplicate expenses)
        questions: List[ClarificationQuestion] = []
        question_idx = 1

        # Trackers for cumulative / monthly allowances
        cumulative_headset_claimed = 0.0
        driver_salary_by_month: Dict[str, float] = {}
        fuel_expenses_by_month: Dict[str, float] = {}

        for exp in expenses:
            if exp.status == "duplicate":
                continue

            cat_lower = exp.category.strip().lower()
            merchant_lower = exp.merchant.strip().lower()

            # ========================================================
            # Policy Rule 1: Mobile Headset Reimbursement
            # Cap: Up to ₹20,000 in one FY. Invoice MUST be from Reliance Digital.
            # ========================================================
            if any(k in cat_lower for k in ["headset", "headphones", "earphones", "airpods"]) or any(k in merchant_lower for k in ["headset", "headphone"]):
                is_reliance_digital = "reliance digital" in merchant_lower or "reliancedigital" in merchant_lower
                
                if not exp.merchant or merchant_lower in ["unknown", "unspecified"]:
                    exp.status = "clarification_needed"
                    prompt = f"The ₹{int(exp.amount):,} mobile headset invoice does not indicate the retailer. Is this purchase from Reliance Digital?"
                    exp.clarification_prompt = prompt
                    exp.flags.append(ExpenseFlag(
                        code="HEADSET_MERCHANT_CLARIFICATION",
                        message="Mobile headset reimbursement requires invoice from Reliance Digital.",
                        severity="warning",
                        field="merchant"
                    ))
                    questions.append(ClarificationQuestion(
                        expense_id=exp.id,
                        question_number=question_idx,
                        field="merchant",
                        prompt=prompt,
                        current_value=exp.merchant,
                        quick_suggestions=["Reliance Digital Store", "Reliance Digital Online", "Other Retailer"]
                    ))
                    question_idx += 1
                elif not is_reliance_digital:
                    # Policy violation: Must be Reliance Digital
                    exp.status = "policy_violation"
                    exp.eligible_amount = 0.0
                    exp.exception_amount = exp.amount
                    exp.flags.append(ExpenseFlag(
                        code="HEADSET_NON_RELIANCE_VENDOR",
                        message=f"Policy Restriction: Mobile headset invoices must be from Reliance Digital. Vendor '{exp.merchant}' is not eligible.",
                        severity="error",
                        field="merchant"
                    ))
                else:
                    # Valid Reliance Digital vendor! Check annual cap (₹20,000 / FY)
                    allowable = max(0.0, cls.HEADSET_ANNUAL_CAP - cumulative_headset_claimed)
                    if exp.amount <= allowable:
                        exp.eligible_amount = exp.amount
                        exp.exception_amount = 0.0
                        cumulative_headset_claimed += exp.amount
                    else:
                        exp.eligible_amount = allowable
                        exp.exception_amount = exp.amount - allowable
                        cumulative_headset_claimed += allowable
                        exp.flags.append(ExpenseFlag(
                            code="HEADSET_ANNUAL_CAP_EXCEEDED",
                            message=f"Exceeds annual Mobile Headset allowance of ₹{int(cls.HEADSET_ANNUAL_CAP):,}/FY. ₹{int(exp.exception_amount):,} routed as policy exception.",
                            severity="warning",
                            field="amount"
                        ))

            # ========================================================
            # Policy Rule 2: Travel Assistance (Driver Salary)
            # Cap: Up to ₹10,000 per month.
            # ========================================================
            elif any(k in cat_lower for k in ["driver", "driver salary", "chauffeur", "travel assistance"]):
                if not exp.date or exp.date.strip().lower() in ["none", "", "missing", "unknown", "null"]:
                    exp.status = "clarification_needed"
                    prompt = f"The ₹{int(exp.amount):,} driver salary claim is missing the service month/date. Which month is this for?"
                    exp.clarification_prompt = prompt
                    exp.flags.append(ExpenseFlag(
                        code="MISSING_DRIVER_MONTH",
                        message="Driver salary claims require the service month for monthly quota allocation.",
                        severity="warning",
                        field="date"
                    ))
                    questions.append(ClarificationQuestion(
                        expense_id=exp.id,
                        question_number=question_idx,
                        field="date",
                        prompt=prompt,
                        current_value=exp.date,
                        quick_suggestions=["September 2026", "October 2026", "August 2026"]
                    ))
                    question_idx += 1
                else:
                    month_key = extract_month_key(exp.date)
                    prior_claimed = driver_salary_by_month.get(month_key, 0.0)
                    allowable = max(0.0, cls.DRIVER_SALARY_MONTHLY_CAP - prior_claimed)
                    
                    if exp.amount <= allowable:
                        exp.eligible_amount = exp.amount
                        exp.exception_amount = 0.0
                        driver_salary_by_month[month_key] = prior_claimed + exp.amount
                    else:
                        exp.eligible_amount = allowable
                        exp.exception_amount = exp.amount - allowable
                        driver_salary_by_month[month_key] = prior_claimed + allowable
                        exp.flags.append(ExpenseFlag(
                            code="DRIVER_SALARY_MONTHLY_CAP_EXCEEDED",
                            message=f"Exceeds monthly Driver Salary cap of ₹{int(cls.DRIVER_SALARY_MONTHLY_CAP):,} for {month_key}. ₹{int(exp.exception_amount):,} routed as policy exception.",
                            severity="warning",
                            field="amount"
                        ))

            # ========================================================
            # Policy Rule 3: Fuel Expenses
            # Cap: Up to ₹15,000 per month.
            # ========================================================
            elif any(k in cat_lower for k in ["fuel", "fuel expenses", "petrol", "diesel", "gas"]):
                if not exp.date or exp.date.strip().lower() in ["none", "", "missing", "unknown", "null"]:
                    exp.status = "clarification_needed"
                    prompt = f"The ₹{int(exp.amount):,} fuel receipt doesn't show the purchase date. What was the date?"
                    exp.clarification_prompt = prompt
                    exp.flags.append(ExpenseFlag(
                        code="MISSING_FUEL_DATE",
                        message="Fuel expense claims require exact date for monthly allowance tracking.",
                        severity="warning",
                        field="date"
                    ))
                    questions.append(ClarificationQuestion(
                        expense_id=exp.id,
                        question_number=question_idx,
                        field="date",
                        prompt=prompt,
                        current_value=exp.date,
                        quick_suggestions=["25 September 2026", "28 September 2026", "Today"]
                    ))
                    question_idx += 1
                else:
                    month_key = extract_month_key(exp.date)
                    prior_claimed = fuel_expenses_by_month.get(month_key, 0.0)
                    allowable = max(0.0, cls.FUEL_MONTHLY_CAP - prior_claimed)
                    
                    if exp.amount <= allowable:
                        exp.eligible_amount = exp.amount
                        exp.exception_amount = 0.0
                        fuel_expenses_by_month[month_key] = prior_claimed + exp.amount
                    else:
                        exp.eligible_amount = allowable
                        exp.exception_amount = exp.amount - allowable
                        fuel_expenses_by_month[month_key] = prior_claimed + allowable
                        exp.flags.append(ExpenseFlag(
                            code="FUEL_MONTHLY_CAP_EXCEEDED",
                            message=f"Exceeds monthly Fuel expense limit of ₹{int(cls.FUEL_MONTHLY_CAP):,} for {month_key}. ₹{int(exp.exception_amount):,} routed as policy exception.",
                            severity="warning",
                            field="amount"
                        ))

            # ========================================================
            # Policy Rule 4: Hotel invoice requires explicit business purpose
            # ========================================================
            elif cat_lower in ["hotel", "lodging", "accommodation"]:
                if not exp.business_purpose or exp.business_purpose.strip().lower() in ["none", "", "missing", "n/a", "null"]:
                    exp.status = "clarification_needed"
                    exp.clarification_prompt = f"The ₹{int(exp.amount):,} hotel expense is missing the business purpose. What was the purpose?"
                    exp.flags.append(ExpenseFlag(
                        code="MISSING_BUSINESS_PURPOSE",
                        message="Corporate policy requires a clear business purpose for hotel accommodations.",
                        severity="warning",
                        field="business_purpose"
                    ))
                    questions.append(ClarificationQuestion(
                        expense_id=exp.id,
                        question_number=question_idx,
                        field="business_purpose",
                        prompt=exp.clarification_prompt,
                        current_value=exp.business_purpose,
                        quick_suggestions=["Client meeting in Bangalore", "Annual Sales Conference", "Engineering Onsite", "Project Kickoff"]
                    ))
                    question_idx += 1
                elif exp.amount > cls.HOTEL_DAILY_CAP:
                    excess = exp.amount - cls.HOTEL_DAILY_CAP
                    exp.eligible_amount = cls.HOTEL_DAILY_CAP
                    exp.exception_amount = excess
                    exp.flags.append(ExpenseFlag(
                        code="HOTEL_CAP_EXCEEDED",
                        message=f"Exceeds standard hotel allowance of ₹{int(cls.HOTEL_DAILY_CAP):,}/night. ₹{int(excess):,} routed as policy exception.",
                        severity="warning",
                        field="amount"
                    ))

            # ========================================================
            # Policy Rule 5: Taxi / Ground transport requires travel date
            # ========================================================
            elif cat_lower in ["taxi", "transport", "cab", "ride", "ground transport"]:
                if not exp.date or exp.date.strip().lower() in ["none", "", "missing", "unknown", "null"]:
                    exp.status = "clarification_needed"
                    exp.clarification_prompt = f"The ₹{int(exp.amount):,} taxi receipt doesn't show the travel date. What was the date?"
                    exp.flags.append(ExpenseFlag(
                        code="MISSING_TRAVEL_DATE",
                        message="Transport claims require exact travel date for trip itinerary verification.",
                        severity="warning",
                        field="date"
                    ))
                    questions.append(ClarificationQuestion(
                        expense_id=exp.id,
                        question_number=question_idx,
                        field="date",
                        prompt=exp.clarification_prompt,
                        current_value=exp.date,
                        quick_suggestions=["24 September", "25 September", "Yesterday", "Today"]
                    ))
                    question_idx += 1

            # ========================================================
            # Dynamic Policy Rules (Configured from Admin Portal)
            # ========================================================
            try:
                from backend.database import get_policy_rules
                active_rules = get_policy_rules(active_only=True)
                for rule in active_rules:
                    rule_cat = rule.get("category", "").strip().lower()
                    # Built-in policies have dedicated monthly/annual cumulative trackers above
                    if rule_cat in ["mobile headset", "driver salary", "fuel", "hotel", "taxi"]:
                        continue

                    rule_keywords = [k.strip().lower() for k in rule.get("keywords", "").split(",") if k.strip()]
                    matches_rule = (cat_lower == rule_cat) or (rule_keywords and (cat_lower in ["other", "general"] or any(k in cat_lower for k in rule_keywords)))
                    
                    if matches_rule:
                        # Check vendor restriction if configured
                        v_rest = (rule.get("vendor_restriction") or "").strip().lower()
                        if v_rest and v_rest not in merchant_lower:
                            exp.status = "policy_violation"
                            exp.eligible_amount = 0.0
                            exp.exception_amount = exp.amount
                            if not any(f.code == "VENDOR_RESTRICTION_VIOLATION" for f in exp.flags):
                                exp.flags.append(ExpenseFlag(
                                    code="VENDOR_RESTRICTION_VIOLATION",
                                    message=f"Policy Restriction ({rule['rule_name']}): Vendor must be '{rule['vendor_restriction']}'. '{exp.merchant}' is not approved.",
                                    severity="error",
                                    field="merchant"
                                ))
                        # Check business purpose requirement
                        if rule.get("require_business_purpose") and (not exp.business_purpose or exp.business_purpose.strip().lower() in ["none", "", "missing", "n/a", "null"]):
                            if exp.status not in ["policy_violation", "duplicate"]:
                                exp.status = "clarification_needed"
                                prompt = f"The ₹{int(exp.amount):,} {rule['category']} expense requires a stated business purpose. What was the purpose?"
                                exp.clarification_prompt = prompt
                                if not any(f.code == "POLICY_REQUIRES_PURPOSE" for f in exp.flags):
                                    exp.flags.append(ExpenseFlag(
                                        code="POLICY_REQUIRES_PURPOSE",
                                        message=f"Rule '{rule['rule_name']}' requires explicit business purpose.",
                                        severity="warning",
                                        field="business_purpose"
                                    ))
                        # Check limit cap
                        max_lim = float(rule.get("max_limit") or 0.0)
                        if max_lim > 0 and exp.status not in ["policy_violation", "duplicate"]:
                            if exp.amount > max_lim:
                                excess = exp.amount - max_lim
                                exp.eligible_amount = max_lim
                                exp.exception_amount = excess
                                if not any(f.code == "CUSTOM_POLICY_CAP_EXCEEDED" for f in exp.flags):
                                    exp.flags.append(ExpenseFlag(
                                        code="CUSTOM_POLICY_CAP_EXCEEDED",
                                        message=f"Exceeds allowance limit of ₹{int(max_lim):,} for '{rule['rule_name']}'. ₹{int(excess):,} routed to exceptions.",
                                        severity="warning",
                                        field="amount"
                                    ))
            except Exception:
                pass

            # ========================================================
            # General: Missing merchant
            # ========================================================
            if not exp.merchant or exp.merchant.strip().lower() in ["unknown", "unspecified"]:
                if exp.status != "clarification_needed":
                    exp.status = "clarification_needed"
                    prompt = f"The ₹{int(exp.amount):,} expense is missing the vendor/merchant name. Where was this spent?"
                    exp.clarification_prompt = prompt
                    exp.flags.append(ExpenseFlag(
                        code="MISSING_MERCHANT",
                        message="Valid merchant or vendor name is mandatory.",
                        severity="warning",
                        field="merchant"
                    ))
                    questions.append(ClarificationQuestion(
                        expense_id=exp.id,
                        question_number=question_idx,
                        field="merchant",
                        prompt=prompt,
                        current_value=exp.merchant,
                        quick_suggestions=["Reliance Digital", "Indian Oil", "City Cabs"]
                    ))
                    question_idx += 1

        # 3. Calculate Aggregates
        total_count = len(expenses)
        ready_count = sum(1 for e in expenses if e.status == "ready")
        clarification_count = sum(1 for e in expenses if e.status == "clarification_needed")
        duplicate_count = sum(1 for e in expenses if e.status == "duplicate")
        
        total_amount = sum(e.amount for e in expenses)
        eligible_amount = sum(e.eligible_amount for e in expenses if e.status not in ["duplicate", "policy_violation"])
        exception_amount = sum(e.exception_amount for e in expenses)

        summary = ClaimSummary(
            total_count=total_count,
            ready_count=ready_count,
            clarification_count=clarification_count,
            duplicate_count=duplicate_count,
            total_amount=round(total_amount, 2),
            eligible_amount=round(eligible_amount, 2),
            exception_amount=round(exception_amount, 2),
            currency="₹"
        )

        return expenses, questions, summary
