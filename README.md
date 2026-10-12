# ReimburseAI — Autonomous Expense & Reimbursement Agent 🧾🤖

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-4.3-38B2AC.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An AI-native reimbursement assistant that transforms a messy pile of receipts, invoices, hotel bills, and cab slips into a policy-compliant, submission-ready corporate expense claim over a natural conversational chat interface and an interactive live workbench.

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

2. **ReimburseAI Agent processes documents & analyzes corporate policy**:
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
   *(or clicks the 1-click quick-answer chip)*

4. **Agent instantly reconciles and finalizes claim**:
   > *"Great. Your claim is now ready.*  
   > *Total: ₹38,420*  
   > *Eligible: ₹36,920*  
   > *Exceptions: ₹1,500*  
   > *[Review Claim] [Submit Claim]"*

5. **Submission to Corporate Finance**:
   - Generates mock ERP synchronization voucher (`CLM-2026-XXXX`).
   - Strict Zero-Eligible Guard: Claims with ₹0 net eligible reimbursement are strictly blocked; ₹0 line items are omitted from payouts.
   - Audit hash recorded with scheduled payroll disbursement.

---

## 🚀 Quick Start Guide (Run on Any Machine)

Clone the repository to your local machine:
```bash
git clone https://github.com/your-username/ExpenseReimbursementAssist.git
cd ExpenseReimbursementAssist
```

### Option A: Windows (One-Click)
Double-click `run.bat` or run in Command Prompt / PowerShell:
```cmd
run.bat
```

### Option B: macOS / Linux (One-Click)
Make executable and run:
```bash
chmod +x run.sh
./run.sh
```

### Option C: Universal Python
```bash
# 1. (Optional) Create virtual environment
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate

# 2. Run the dynamic runner (auto-installs dependencies if needed)
python run.py
```

### Option D: Docker Compose
```bash
docker compose up --build
```

---

## 🌐 Application URLs

Once started, open your web browser to:
- **Employee Copilot UI:** [http://localhost:8000](http://localhost:8000)
- **Admin Governance Portal:** [http://localhost:8000/admin](http://localhost:8000/admin)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Technical Design PDF:** [http://localhost:8000/api/tdd-pdf](http://localhost:8000/api/tdd-pdf)

> **Dynamic Port Fallback:** If port 8000 is occupied by another process on your machine, `run.py` automatically detects the conflict and switches to the next available port (e.g. 8001, 8002) without crashing!

---

## ⚙️ Environment Configuration

ReimburseAI is designed to be **100% functional out-of-the-box** without any external API keys.

If you have an OpenAI API key and wish to test multimodal vision OCR (`gpt-4o-mini`):
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and set your key:
   ```env
   OPENAI_API_KEY=sk-proj-your-actual-api-key-here
   PORT=8000
   HOST=0.0.0.0
   ```
> If `OPENAI_API_KEY` is not provided, ReimburseAI seamlessly uses its built-in offline heuristic extraction engine.

---

## 🏗️ Architecture & Features

### 1. Multimodal Document Understanding Engine (`backend/extractor.py`)
- Ingests receipt photos (`.png`, `.jpg`) and PDF tax invoices (`.pdf`).
- Extracts merchant, date, amount, taxes, payment method, category, and line items.
- Dual-mode architecture: Online OpenAI Vision (`gpt-4o-mini`) + Offline heuristic regex OCR.

### 2. Corporate Policy Engine (`backend/policy_engine.py`)
- **🎧 Mobile Headset Reimbursement**:
  - Allowance: Up to **₹20,000 per financial year**.
  - Strict Vendor Constraint: Invoice **MUST be from Reliance Digital**. Unapproved vendors (Croma, Amazon) are flagged as severe policy violations (`HEADSET_NON_RELIANCE_VENDOR`) with 0% reimbursement.
- **🚗 Travel Assistance (Driver Salary)**:
  - Allowance: Up to **₹10,000 per month**. Requires service month tracking; excess routed to policy exceptions.
- **⛽ Fuel Expenses**:
  - Allowance: Up to **₹15,000 per month** with fuel station tax receipt.
- **🏨 Hotel Accommodations**: Standard allowance up to ₹8,000/night with mandatory business purpose.
- **🚕 Taxi Transit**: Travel date verification mandatory.
- **🛡️ Deduplication Shield**: Blocks identical bills already recorded in the database (`under_process` or `approved`) across past claims.
- **🚫 Zero-Eligible Submission Guard**: Claims with ₹0 net eligible amount cannot be submitted. Individual ₹0 items are excluded from final payouts.

### 3. Dedicated Admin Governance Portal (`/admin`)
- **Claim Multi-Criteria Filter**: Filter records by status (`under_process`, `approved`, `rejected`), category, date range, or claimant keyword.
- **Executive Analytics & Reports**: Spend by category, monthly claim trends, top merchants, and department budgets.
- **Dynamic Policy Rules Manager**: Add, edit, toggle, or delete corporate policies at runtime.

### 4. Interactive Full-Stack UI (`frontend/`)
- Modern dark-mode UI built with React 19, Tailwind CSS, and Lucide icons.
- Dual-pane layout: Conversational copilot with drag-and-drop receipt dropzone on the left, live Claim Workbench on the right.
- Pre-built distribution in `frontend/dist` allows running the web UI without installing Node.js.

---

## 🧪 Automated Testing

ReimburseAI includes automated test suites covering corporate policy compliance and zero-eligible submission blocking:

```bash
# Test 1: Verify policy caps, Reliance Digital restrictions, Driver & Fuel allowances
python -m backend.test_new_policies

# Test 2: Verify zero-eligible submission prevention & voucher exclusion
python -m backend.test_zero_eligible_submission
```

---

## 📁 Repository Structure

```
ExpenseReimbursementAssist/
├── backend/
│   ├── main.py                     # FastAPI REST API endpoints & static file hosting
│   ├── agent.py                    # Conversational state machine & Q&A parser
│   ├── policy_engine.py            # Corporate policy rules & deduplication engine
│   ├── extractor.py                # Multimodal document parsing (OpenAI + Heuristic)
│   ├── database.py                 # SQLite database models, CRUD, and audit logging
│   ├── demo_generator.py           # Realistic sample receipt generator (images & PDFs)
│   ├── models.py                   # Pydantic data schemas
│   ├── test_new_policies.py        # Policy verification test suite
│   ├── test_zero_eligible_submission.py # Zero-eligible submission guard test suite
│   ├── sample_receipts/            # Auto-generated 11 realistic sample bills
│   └── uploads/                    # User uploaded receipts
├── frontend/
│   ├── src/                        # React 19 source code
│   │   ├── App.jsx                 # Top-level state and dual-pane layout
│   │   └── components/
│   │       ├── Header.jsx          # Top bar with demo batch triggers
│   │       ├── ChatView.jsx        # Conversational assistant & dropzone
│   │       ├── ClaimWorkbench.jsx  # Live claim workbench & action footer
│   │       ├── ExpenseModal.jsx    # Receipt inspector & line item editor
│   │       ├── ReviewClaimModal.jsx# Itemized claim audit review table
│   │       ├── PolicyModal.jsx     # Corporate policy rules reference
│   │       ├── SubmissionSuccessModal.jsx # Official voucher with celebration
│   │       └── AdminPortal.jsx     # Admin records, reports, & policy editor
│   ├── dist/                       # Optimized production bundle (served by FastAPI)
│   └── package.json
├── Dockerfile                      # Production container image definition
├── docker-compose.yml              # One-command container orchestration
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules for Python, Node, & OS
├── run.py                          # Dynamic startup runner with auto-port discovery
├── run.bat                         # 1-click Windows launcher
├── run.sh                          # 1-click Linux/macOS launcher
├── TECHNICAL_DESIGN_DOCUMENT.md    # Complete Technical Design Document (Markdown)
├── TECHNICAL_DESIGN_DOCUMENT.pdf   # Complete Technical Design Document (21-page PDF)
└── README.md                       # This document
```

---

## 📄 Documentation

- [Technical Design Document (Markdown)](TECHNICAL_DESIGN_DOCUMENT.md)
- [Technical Design Document (PDF)](TECHNICAL_DESIGN_DOCUMENT.pdf)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
