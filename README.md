# ReimburseAI — Autonomous Expense & Reimbursement Agent 🧾🤖

An AI-native reimbursement assistant that transforms a messy pile of receipts, invoices, hotel bills, and cab slips into a policy-compliant, submission-ready corporate expense claim over a natural conversational chat interface.

---

## 🌟 The Core Experience

```
Receipts ➔ Understand ➔ Validate ➔ Ask Only What Is Needed ➔ Detect Issues ➔ Build Claim ➔ Ready to Submit
```

### Prompt Scenario Walkthrough:
1. **Employee uploads bills**:
   - 8 receipt photos (meals, hotel, Uber, coworking)
   - 2 PDFs (Indigo Airlines flight ticket, Airtel telecom bill)
   - 1 hotel invoice
   - 1 taxi receipt
   *(Total: 11 expenses)*

2. **ReimburseAI Agent processes documents & analyzes policy**:
   > *"I found 11 expenses totaling ₹38,420.*  
   > *✅ 8 expenses are ready*  
   > *⚠️ 2 need clarification*  
   > *🔴 1 appears to be a duplicate*  
   >  
   > *I only need 2 answers from you:*  
   > *1. The ₹4,850 hotel expense is missing the business purpose. What was the purpose?*  
   > *2. The ₹1,200 taxi receipt doesn't show the travel date. What was the date?"*

3. **Employee answers in natural chat**:
   > *1. Client meeting in Bangalore*  
   > *2. 24 September*  
   *(or clicks the 1-click quick-fill banner)*

4. **Agent instantly reconciles and finalizes claim**:
   > *"Great. Your claim is now ready.*  
   > *Total: ₹38,420*  
   > *Eligible: ₹36,920*  
   > *Exceptions: ₹1,500*  
   > *[Review Claim] [Submit Claim]"*

5. **Submission to Corporate Finance**:
   - Generates mock ERP synchronization voucher (`CLM-2026-XXXX`).
   - Audit hash recorded with scheduled payroll disbursement.

---

## 🏗️ Architecture & Features

### 1. Multimodal Document Understanding Engine (`backend/extractor.py`)
- Parses receipt images (PNG, JPG) and PDF tax invoices.
- Extracts merchant, date, amount, tax, payment method, and itemized lines.
- Resilient offline heuristic OCR + OpenAI Vision integration (`gpt-4o-mini`).

### 2. Corporate Policy & Compliance Engine (`backend/policy_engine.py`)
- **🎧 Mobile Headset Reimbursement**:
  - Allowance: Up to **₹20,000 in one Financial Year**.
  - Strict Vendor Restriction: Invoice **MUST be from Reliance Digital**. Non-Reliance vendors (e.g. Croma, Amazon) are flagged as severe policy violations (`HEADSET_NON_RELIANCE_VENDOR`) with 0% reimbursement.
- **🚗 Travel Assistance (Driver Salary)**:
  - Allowance: Up to **₹10,000 per month**.
  - Requires service month tracking; excess over ₹10,000/month is routed to policy exceptions.
- **⛽ Fuel Expenses**:
  - Allowance: Up to **₹15,000 per month**.
  - Requires valid petrol pump / fuel tax invoice; monthly excess routed to policy exceptions.
- **🏨 Hotel Per-Diem Cap**: Enforces standard ₹8,000/night limit and mandatory business purpose.
- **🚕 Transport Verification**: Enforces travel date verification for ground transport.
- **🔴 Duplicate Detection**: Identifies exact matches (same merchant + amount) and flags them with zero false positives.
- **Eligible vs Exception Separation**: Excludes duplicates and caps policy excess automatically.

### 3. Agentic Conversational State Machine (`backend/agent.py`)
- Isolates unresolved policy gaps and asks **only what is needed**.
- Natural language parsing for numbered answers, multi-line answers, or casual chat.
- Live real-time claim recalculation upon answer receipt.

### 4. Interactive Full-Stack UI (`frontend/`)
- Modern dark-mode UI with Vite, React 19, and Tailwind CSS.
- Split-screen workspace:
  - **Left**: Conversational Copilot with quick-action chips and drag-and-drop receipt dropzone.
  - **Right**: Real-time Claim Workbench with financial totals, filterable expense cards, and receipt inspector modal.
  - **Modals**: Full Itemized Audit Review Table, Policy Rules Guide, and Official Voucher modal with celebratory confetti.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ (optional, pre-built production bundle included in `frontend/dist`)

### 1. Launch with One Command
From the root directory:
```bash
.\.venv\Scripts\python run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### 2. Testing the Demo Scenario
1. Click **"Load Demo Batch (11 Receipts)"** in the top header.
2. The agent will process all 11 receipts and output the prompt scenario:
   - Total: ₹38,420
   - 8 Ready, 2 Need Clarification, 1 Duplicate.
3. Click the suggestion button or type:
   ```
   1. Client meeting in Bangalore
   2. 24 September
   ```
4. The agent updates the claim to **Ready to Submit**:
   - Total: ₹38,420
   - Eligible: ₹36,920
   - Exceptions: ₹1,500
5. Click **"Review Claim"** to inspect the table or **"Submit Claim"** to submit!

---

## 📁 Repository Structure

```
ExpenseReimbursementAssist/
├── backend/
│   ├── main.py              # FastAPI REST endpoints & static file hosting
│   ├── agent.py             # Conversational agent logic & Q&A parser
│   ├── policy_engine.py     # Corporate policy rules & duplicate detector
│   ├── extractor.py         # Multimodal document parsing
│   ├── demo_generator.py    # Generates realistic sample receipts & PDFs
│   ├── models.py            # Pydantic data schemas
│   ├── sample_receipts/     # Generated 11 realistic receipt files
│   └── uploads/             # User uploaded receipts
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main application layout & state
│   │   ├── components/
│   │   │   ├── Header.jsx                # Top bar with demo batch triggers
│   │   │   ├── ChatView.jsx              # Interactive chat & dropzone
│   │   │   ├── ClaimWorkbench.jsx        # Right pane live financial workbench
│   │   │   ├── ExpenseModal.jsx          # Receipt inspector & edit dialog
│   │   │   ├── ReviewClaimModal.jsx      # Audit table breakdown
│   │   │   ├── PolicyModal.jsx           # Corporate policy rules modal
│   │   │   └── SubmissionSuccessModal.jsx# Official voucher with confetti
│   ├── dist/                # Production optimized build
│   └── package.json
├── run.py                   # Single-command startup script
└── README.md
```
