import React, { useState, useEffect } from 'react';
import { X, Check, ExternalLink, AlertTriangle, ShieldAlert, Sparkles, Receipt, Calendar, Tag, FileText, Trash2 } from 'lucide-react';

export default function ExpenseModal({ expense, isOpen, onClose, onSave, onDelete }) {
  if (!isOpen || !expense) return null;

  const [merchant, setMerchant] = useState(expense.merchant || "");
  const [amount, setAmount] = useState(expense.amount || 0);
  const [date, setDate] = useState(expense.date || "");
  const [category, setCategory] = useState(expense.category || "Other");
  const [purpose, setPurpose] = useState(expense.business_purpose || "");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setMerchant(expense.merchant || "");
    setAmount(expense.amount || 0);
    setDate(expense.date || "");
    setCategory(expense.category || "Other");
    setPurpose(expense.business_purpose || "");
  }, [expense]);

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    await onSave(expense.id, {
      merchant,
      amount: parseFloat(amount),
      date,
      category,
      business_purpose: purpose
    });
    setIsSaving(false);
    onClose();
  };

  const isDuplicate = expense.status === 'duplicate';
  const needsClarification = expense.status === 'clarification_needed';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl flex flex-col md:flex-row">
        
        {/* Left Side: Receipt Image Preview */}
        <div className="md:w-1/2 bg-slate-950 p-4 border-b md:border-b-0 md:border-r border-slate-800 flex flex-col items-center justify-center relative overflow-y-auto max-h-[45vh] md:max-h-full">
          <div className="text-xs font-medium text-slate-400 mb-2 flex items-center justify-between w-full px-2">
            <span className="flex items-center gap-1.5 truncate">
              <Receipt className="w-3.5 h-3.5 text-indigo-400" />
              {expense.file_name}
            </span>
            <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-300">
              {expense.file_type.includes('pdf') ? 'PDF Document' : 'PNG Image'}
            </span>
          </div>

          <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-900 w-full flex items-center justify-center p-2 min-h-[260px]">
            {expense.preview_url ? (
              expense.file_type.includes('pdf') ? (
                <div className="text-center p-6 space-y-3">
                  <FileText className="w-16 h-16 text-indigo-400 mx-auto opacity-80" />
                  <div className="text-sm font-medium text-slate-200">PDF Tax Invoice / Ticket</div>
                  <a
                    href={expense.preview_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Open PDF Document
                  </a>
                </div>
              ) : (
                <img
                  src={expense.preview_url}
                  alt={expense.merchant}
                  className="max-h-[380px] w-auto object-contain rounded-lg shadow-md"
                />
              )
            ) : (
              <div className="text-slate-500 text-xs">No preview available</div>
            )}
          </div>
        </div>

        {/* Right Side: Metadata & Form */}
        <div className="md:w-1/2 p-6 flex flex-col justify-between overflow-y-auto max-h-[50vh] md:max-h-[85vh]">
          <div>
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white m-0">{expense.merchant}</h3>
                  {isDuplicate && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
                      🔴 DUPLICATE
                    </span>
                  )}
                  {expense.status === 'policy_violation' && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                      🚫 POLICY VIOLATION
                    </span>
                  )}
                  {needsClarification && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      ⚠️ NEEDS CLARIFICATION
                    </span>
                  )}
                  {expense.status === 'ready' && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      ✅ READY
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Extracted with {Math.round(expense.confidence * 100)}% AI confidence
                </p>
              </div>

              <button
                onClick={onClose}
                className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Flags Alert if any */}
            {expense.flags && expense.flags.length > 0 && (
              <div className="mb-4 space-y-2">
                {expense.flags.map((flag, idx) => (
                  <div
                    key={idx}
                    className={`p-2.5 rounded-xl text-xs flex items-start gap-2 border ${
                      flag.severity === 'error'
                        ? 'bg-rose-500/10 border-rose-500/25 text-rose-300'
                        : 'bg-amber-500/10 border-amber-500/25 text-amber-300'
                    }`}
                  >
                    {flag.severity === 'error' ? (
                      <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
                    )}
                    <div>
                      <div className="font-semibold">{flag.code.replace(/_/g, ' ')}</div>
                      <div className="text-slate-300 text-[11px]">{flag.message}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Editable Form */}
            <form onSubmit={handleSave} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Merchant / Vendor</label>
                <input
                  type="text"
                  value={merchant}
                  onChange={(e) => setMerchant(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-700 text-white font-mono focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Date</label>
                  <input
                    type="text"
                    placeholder="YYYY-MM-DD or DD Month"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="Mobile Headset">Mobile Headset (Reliance Digital only)</option>
                  <option value="Driver Salary">Driver Salary (Travel Assistance)</option>
                  <option value="Fuel">Fuel Expenses</option>
                  <option value="Hotel">Hotel</option>
                  <option value="Taxi">Taxi / Ride</option>
                  <option value="Meals">Meals & Dining</option>
                  <option value="Transport">Transport / Flights</option>
                  <option value="Office Supplies">Office Supplies & Coworking</option>
                  <option value="Telecommunication">Telecommunication & Internet</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Business Purpose</label>
                <input
                  type="text"
                  placeholder="e.g. Client meeting in Bangalore"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Line items if present */}
              {expense.line_items && expense.line_items.length > 0 && (
                <div className="mt-3">
                  <div className="text-[11px] font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
                    Itemized Breakdown
                  </div>
                  <div className="bg-slate-950/60 rounded-lg p-2 border border-slate-800 space-y-1">
                    {expense.line_items.map((li, idx) => (
                      <div key={idx} className="flex justify-between text-slate-300 text-[11px]">
                        <span>{li.item}</span>
                        <span className="font-mono text-slate-400">₹{li.amount.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
                {onDelete ? (
                  <button
                    type="button"
                    onClick={async () => {
                      await onDelete(expense.id);
                      onClose();
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-medium transition cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                    <span>Remove from Claim</span>
                  </button>
                ) : <div />}

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition cursor-pointer"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Save & Re-validate
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>

      </div>
    </div>
  );
}
