import React, { useEffect } from 'react';
import confetti from 'canvas-confetti';
import { CheckCircle2, Download, RefreshCw, X, ShieldCheck, Building2, User, Calendar, CreditCard, ArrowRight } from 'lucide-react';

export default function SubmissionSuccessModal({ submission, isOpen, onClose, onReset }) {
  if (!isOpen || !submission) return null;

  useEffect(() => {
    // Launch celebratory confetti burst
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 }
    });
  }, [isOpen]);

  const handleDownload = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(submission, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `Claim_Voucher_${submission.claim_reference}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-emerald-500/40 rounded-3xl max-w-lg w-full p-6 shadow-2xl relative overflow-hidden">
        
        {/* Glowing Top Banner */}
        <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-emerald-500 via-teal-400 to-indigo-500" />
        
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center pt-2 pb-4">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center justify-center mx-auto mb-3 shadow-lg shadow-emerald-500/20">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-white m-0">Claim Submitted to Finance</h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated corporate policy validation passed. Synchronized with Finance ERP.
          </p>
        </div>

        {/* Voucher Card */}
        <div className="bg-slate-950/80 rounded-2xl border border-slate-800 p-4 space-y-3.5 my-2">
          
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Claim Reference ID</div>
              <div className="text-base font-mono font-bold text-indigo-400">{submission.claim_reference}</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Submitted At</div>
              <div className="text-xs text-slate-300 font-mono">{submission.submitted_at}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400">Employee</div>
              <div className="font-semibold text-white mt-0.5">{submission.employee_name}</div>
              <div className="text-[10px] text-slate-400">{submission.employee_id} • {submission.department}</div>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400">Disbursement Status</div>
              <div className="font-semibold text-emerald-400 mt-0.5">Approved</div>
              <div className="text-[10px] text-slate-400">Scheduled for Payroll</div>
            </div>
          </div>

          {/* Amount Breakdown */}
          <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Total Invoices Claimed:</span>
              <span className="font-mono text-slate-200">₹{submission.total_amount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-emerald-400 font-semibold text-sm">
              <span>Eligible Reimbursement:</span>
              <span className="font-mono text-emerald-300">₹{submission.eligible_amount.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-rose-400">
              <span>Policy Exceptions / Duplicates:</span>
              <span className="font-mono">₹{submission.exceptions_amount.toLocaleString()}</span>
            </div>
            {submission.exceptions_amount > 0 && (
              <div className="pt-1 text-[10px] text-slate-400 border-t border-slate-800/60 flex items-center gap-1">
                <span>🛡️</span>
                <span>Only eligible expenses are submitted to finance. Ineligible items (₹0) are excluded.</span>
              </div>
            )}
          </div>

          {/* Audit trail */}
          <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between pt-1">
            <span>Audit Ref: {submission.audit_id}</span>
            <span className="text-emerald-500 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> Auto-Verified
            </span>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-2 mt-5">
          <button
            onClick={handleDownload}
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs border border-slate-700 transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            <span>Download Voucher JSON</span>
          </button>
          
          <button
            onClick={onReset}
            className="flex items-center justify-center gap-1.5 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-600/25 transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Claim</span>
          </button>
        </div>

      </div>
    </div>
  );
}
