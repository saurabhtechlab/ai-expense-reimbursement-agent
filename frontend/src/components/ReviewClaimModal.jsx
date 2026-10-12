import React from 'react';
import { X, CheckCircle, AlertTriangle, FileSpreadsheet, Download, Send, Building, Plane, Coffee, Car, Briefcase, Smartphone, Receipt } from 'lucide-react';

export default function ReviewClaimModal({ 
  session, 
  isOpen, 
  onClose, 
  onSubmitClaim, 
  onSelectExpense 
}) {
  if (!isOpen) return null;

  const expenses = session?.expenses || [];
  const summary = session?.summary || { total_amount: 0, eligible_amount: 0, exception_amount: 0 };

  const handleDownload = () => {
    const report = {
      sessionId: session.session_id,
      employee: {
        name: session.employee_name,
        id: session.employee_id,
        department: session.department
      },
      summary: session.summary,
      expenses: session.expenses
    };
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `Expense_Claim_Report_${session.session_id.slice(0, 8)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-3xl max-w-5xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white m-0">Claim Review & Compliance Audit</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Itemized breakdown for {session?.employee_name} ({session?.employee_id})
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Financial Highlights */}
        <div className="p-4 bg-slate-950/60 border-b border-slate-800 grid grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-slate-400 font-medium">Total Claimed:</span>
            <div className="text-lg font-bold font-mono text-white mt-0.5">
              ₹{Math.round(summary.total_amount).toLocaleString()}
            </div>
            <span className="text-[10px] text-slate-500">{summary.total_count} Receipts</span>
          </div>

          <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
            <span className="text-emerald-400 font-medium">Eligible for Reimbursement:</span>
            <div className="text-lg font-bold font-mono text-emerald-300 mt-0.5">
              ₹{Math.round(summary.eligible_amount).toLocaleString()}
            </div>
            <span className="text-[10px] text-emerald-500">Scheduled for direct deposit</span>
          </div>

          <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-800/40">
            <span className="text-rose-400 font-medium">Policy Exceptions & Exclusions:</span>
            <div className="text-lg font-bold font-mono text-rose-300 mt-0.5">
              ₹{Math.round(summary.exception_amount).toLocaleString()}
            </div>
            <span className="text-[10px] text-rose-400">1 Duplicate excluded</span>
          </div>
        </div>

        {/* Zero Eligible Warning Banner */}
        {summary.eligible_amount <= 0 && expenses.length > 0 && (
          <div className="mx-4 mt-3 p-3 bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs rounded-xl flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Submission Blocked:</strong> Net eligible amount is ₹0. Under company policy, claims with zero eligible reimbursement cannot be submitted.
            </span>
          </div>
        )}

        {/* Expenses Table */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="rounded-xl border border-slate-800 overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-800/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-700">
                  <th className="p-3">#</th>
                  <th className="p-3">Vendor / Merchant</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Date</th>
                  <th className="p-3">Purpose</th>
                  <th className="p-3 text-right">Amount</th>
                  <th className="p-3 text-right">Eligible</th>
                  <th className="p-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {expenses.map((exp, idx) => {
                  const isDup = exp.status === 'duplicate';
                  const isClar = exp.status === 'clarification_needed';
                  const isZeroEligible = exp.eligible_amount === 0;

                  return (
                    <tr
                      key={exp.id}
                      onClick={() => {
                        onClose();
                        onSelectExpense(exp);
                      }}
                      className="hover:bg-slate-800/40 cursor-pointer transition"
                    >
                      <td className="p-3 text-slate-500 font-mono">{idx + 1}</td>
                      <td className="p-3 font-medium text-white flex items-center gap-2">
                        <span>{exp.merchant}</span>
                        {isDup && (
                          <span className="text-[9px] bg-rose-500/20 text-rose-300 px-1.5 py-0.5 rounded font-mono">
                            DUP
                          </span>
                        )}
                        {isZeroEligible && !isDup && (
                          <span className="text-[9px] bg-rose-500/20 text-rose-300 px-1.5 py-0.5 rounded font-mono">
                            EXCLUDED
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-slate-400">{exp.category}</td>
                      <td className="p-3 text-slate-300 font-mono">
                        {exp.date || <span className="text-amber-400">[Missing]</span>}
                      </td>
                      <td className="p-3 text-slate-300 max-w-[200px] truncate">
                        {exp.business_purpose || <span className="text-amber-400">[Missing]</span>}
                      </td>
                      <td className={`p-3 text-right font-mono ${isDup || isZeroEligible ? 'text-slate-500 line-through' : 'text-slate-200'}`}>
                        ₹{Math.round(exp.amount).toLocaleString()}
                      </td>
                      <td className={`p-3 text-right font-mono font-bold ${isZeroEligible ? 'text-rose-400' : 'text-emerald-400'}`}>
                        ₹{Math.round(exp.eligible_amount).toLocaleString()}
                      </td>
                      <td className="p-3 text-center">
                        {isDup ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            🔴 Duplicate
                          </span>
                        ) : isClar ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                            ⚠️ Clarify
                          </span>
                        ) : isZeroEligible ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            🚫 Ineligible
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            ✅ Ready
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-2.5 text-[11px] text-slate-400 flex items-center gap-1.5 px-1">
            <span className="text-indigo-400">ℹ️</span>
            <span>Only expenses with eligible amount &gt; ₹0 are submitted to finance. Ineligible items and duplicates (₹0 eligible) are excluded.</span>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between gap-3">
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs border border-slate-700 transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            <span>Download Claim Report (JSON)</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition cursor-pointer"
            >
              Back to Chat
            </button>
            <button
              onClick={() => {
                onClose();
                onSubmitClaim();
              }}
              disabled={session?.status === 'submitted' || summary.eligible_amount <= 0}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-xs shadow-lg shadow-emerald-500/25 transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Send className="w-3.5 h-3.5" />
              <span>
                {session?.status === 'submitted'
                  ? 'Claim Submitted'
                  : summary.eligible_amount <= 0
                  ? 'Eligible ₹0 (Cannot Submit)'
                  : 'Submit Claim Now'}
              </span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
