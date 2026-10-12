import React, { useState } from 'react';
import { 
  Receipt, 
  CheckCircle, 
  AlertTriangle, 
  Copy, 
  ArrowUpRight, 
  ShieldAlert, 
  ShieldCheck,
  FileText, 
  Building, 
  Plane, 
  Coffee, 
  Car, 
  Briefcase, 
  Smartphone, 
  Headphones,
  Fuel,
  Ban,
  MoreHorizontal,
  Send,
  ExternalLink,
  Trash2
} from 'lucide-react';

export default function ClaimWorkbench({ 
  session, 
  onSelectExpense, 
  onSubmitClaim, 
  onOpenPolicy,
  onDeleteExpense,
  isSubmitting 
}) {
  const [filter, setFilter] = useState('all'); // all, ready, clarification, duplicate, violation

  const expenses = session?.expenses || [];
  const summary = session?.summary || { total_amount: 0, eligible_amount: 0, exception_amount: 0 };

  const getCategoryIcon = (category) => {
    const cat = category?.toLowerCase() || '';
    if (cat.includes('headset') || cat.includes('headphone') || cat.includes('earphone')) {
      return <Headphones className="w-4 h-4 text-purple-400" />;
    }
    if (cat.includes('fuel') || cat.includes('petrol') || cat.includes('diesel')) {
      return <Fuel className="w-4 h-4 text-orange-400" />;
    }
    if (cat.includes('driver') || cat.includes('chauffeur')) {
      return <Car className="w-4 h-4 text-amber-400" />;
    }
    if (cat.includes('hotel') || cat.includes('lodging')) {
      return <Building className="w-4 h-4 text-blue-400" />;
    }
    if (cat.includes('taxi') || cat.includes('cab')) {
      return <Car className="w-4 h-4 text-amber-400" />;
    }
    if (cat.includes('meals') || cat.includes('dining')) {
      return <Coffee className="w-4 h-4 text-emerald-400" />;
    }
    if (cat.includes('transport') || cat.includes('flight')) {
      return <Plane className="w-4 h-4 text-indigo-400" />;
    }
    if (cat.includes('office')) {
      return <Briefcase className="w-4 h-4 text-purple-400" />;
    }
    if (cat.includes('telecom') || cat.includes('broadband')) {
      return <Smartphone className="w-4 h-4 text-cyan-400" />;
    }
    return <Receipt className="w-4 h-4 text-slate-400" />;
  };

  const filteredExpenses = expenses.filter(exp => {
    if (filter === 'ready') return exp.status === 'ready';
    if (filter === 'clarification') return exp.status === 'clarification_needed';
    if (filter === 'duplicate') return exp.status === 'duplicate';
    return true;
  });

  const duplicateItem = expenses.find(e => e.status === 'duplicate');
  const primaryItem = duplicateItem?.is_duplicate_of ? expenses.find(e => e.id === duplicateItem.is_duplicate_of) : null;

  return (
    <div className="bg-slate-900/60 rounded-2xl border border-slate-800 flex flex-col h-full overflow-hidden shadow-xl">
      {/* Top Banner: Financial Overview */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/90 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider m-0">Claim Workbench</h2>
            <div className="text-xs text-slate-400 mt-0.5">
              {expenses.length} documents processed
            </div>
          </div>
          
          <div className="flex items-center gap-1.5">
            {session?.status === 'submitted' ? (
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> Claim Submitted
              </span>
            ) : session?.pending_questions?.length === 0 && expenses.length > 0 ? (
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> Ready to Submit
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Clarification Required
              </span>
            )}
          </div>
        </div>

        {/* 3 Metric Cards */}
        <div className="grid grid-cols-3 gap-2.5 text-xs">
          {/* Total Claimed */}
          <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Total Claimed</div>
            <div className="text-base font-bold font-mono text-white mt-0.5">
              ₹{Math.round(summary.total_amount).toLocaleString()}
            </div>
            <div className="text-[10px] text-slate-500">{summary.total_count} expenses</div>
          </div>

          {/* Eligible */}
          <div className="p-2.5 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
            <div className="text-[10px] text-emerald-400 font-medium uppercase tracking-wider">Eligible</div>
            <div className="text-base font-bold font-mono text-emerald-400 mt-0.5">
              ₹{Math.round(summary.eligible_amount).toLocaleString()}
            </div>
            <div className="text-[10px] text-emerald-500/90 font-medium">Auto-approved</div>
          </div>

          {/* Exceptions */}
          <div className="p-2.5 rounded-xl bg-rose-950/20 border border-rose-800/40">
            <div className="text-[10px] text-rose-400 font-medium uppercase tracking-wider">Exceptions</div>
            <div className="text-base font-bold font-mono text-rose-400 mt-0.5">
              ₹{Math.round(summary.exception_amount).toLocaleString()}
            </div>
            <div className="text-[10px] text-rose-400/80">Duplicate / Excluded</div>
          </div>
        </div>

        {/* Corporate Policy Guide Button */}
        <button
          onClick={onOpenPolicy}
          className="w-full flex items-center justify-between p-2.5 rounded-xl bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950/60 hover:from-slate-800 hover:to-indigo-900/60 border border-indigo-500/30 text-xs text-slate-200 transition cursor-pointer group shadow-sm"
          title="Click to view policy rules for Mobile Headsets, Driver Salary, Fuel, etc."
        >
          <span className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-emerald-500/20 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
            </span>
            <span className="font-semibold text-white">Corporate Policy Rules</span>
            <span className="text-[10px] text-indigo-300 bg-indigo-500/20 px-1.5 py-0.5 rounded font-mono">Headset • Driver • Fuel</span>
          </span>
          <span className="text-[11px] text-indigo-400 group-hover:text-indigo-300 font-semibold flex items-center gap-1">
            <span>View Rules</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </span>
        </button>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 pt-1 overflow-x-auto text-xs">
          <button
            onClick={() => setFilter('all')}
            className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer ${
              filter === 'all'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800/80 text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({expenses.length})
          </button>
          <button
            onClick={() => setFilter('ready')}
            className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer flex items-center gap-1 ${
              filter === 'ready'
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-800/80 text-slate-400 hover:text-emerald-400'
            }`}
          >
            <span>✅ Ready</span>
            <span>({summary.ready_count})</span>
          </button>
          <button
            onClick={() => setFilter('clarification')}
            className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer flex items-center gap-1 ${
              filter === 'clarification'
                ? 'bg-amber-600 text-white'
                : 'bg-slate-800/80 text-slate-400 hover:text-amber-400'
            }`}
          >
            <span>⚠️ Needs Input</span>
            <span>({summary.clarification_count})</span>
          </button>
          <button
            onClick={() => setFilter('duplicate')}
            className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer flex items-center gap-1 ${
              filter === 'duplicate'
                ? 'bg-rose-600 text-white'
                : 'bg-slate-800/80 text-slate-400 hover:text-rose-400'
            }`}
          >
            <span>🔴 Duplicate</span>
            <span>({summary.duplicate_count})</span>
          </button>
        </div>
      </div>

      {/* Expenses Scroll Area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredExpenses.length === 0 ? (
          <div className="text-center py-12 px-4 text-slate-500 text-xs">
            <Receipt className="w-8 h-8 mx-auto mb-2 opacity-40" />
            No expenses matching this filter.
          </div>
        ) : (
          filteredExpenses.map((exp) => {
            const isDup = exp.status === 'duplicate';
            const isClar = exp.status === 'clarification_needed';
            const isViolation = exp.status === 'policy_violation';
            const isCapped = exp.status === 'ready' && exp.exception_amount > 0;

            return (
              <div
                key={exp.id}
                onClick={() => onSelectExpense(exp)}
                className={`p-3 rounded-xl border transition-all cursor-pointer hover:scale-[1.01] ${
                  isViolation
                    ? 'bg-rose-950/30 border-rose-600/60 hover:border-rose-500'
                    : isDup
                    ? 'bg-rose-950/20 border-rose-800/40 hover:border-rose-700/60'
                    : isClar
                    ? 'bg-amber-950/20 border-amber-800/40 hover:border-amber-700/60'
                    : isCapped
                    ? 'bg-slate-900 border-indigo-500/40 hover:border-indigo-400'
                    : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/50 shrink-0">
                      {getCategoryIcon(exp.category)}
                    </div>
                    <div className="truncate">
                      <div className="text-xs font-bold text-white truncate flex items-center gap-1.5">
                        <span>{exp.merchant}</span>
                        {isViolation && (
                          <span className="text-[9px] bg-rose-500/20 text-rose-300 border border-rose-500/30 px-1.5 py-0.2 rounded font-semibold">
                            🚫 Policy Violation
                          </span>
                        )}
                        {isDup && (
                          <span className="text-[9px] bg-rose-500/20 text-rose-300 px-1.5 py-0.2 rounded font-semibold">
                            Duplicate
                          </span>
                        )}
                        {isClar && (
                          <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.2 rounded font-semibold">
                            Needs Info
                          </span>
                        )}
                        {isCapped && (
                          <span className="text-[9px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.2 rounded font-semibold">
                            ⚖️ Cap Capped
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <span className="text-indigo-300 font-medium">{exp.category}</span>
                        <span>•</span>
                        <span>{exp.date || <span className="text-amber-400 font-semibold">[Date missing]</span>}</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <div className={`text-xs font-mono font-bold ${isDup || isViolation ? 'text-rose-400 line-through' : 'text-slate-100'}`}>
                      ₹{Math.round(exp.amount).toLocaleString()}
                    </div>
                    {exp.eligible_amount > 0 && exp.exception_amount > 0 ? (
                      <div className="text-[10px] font-mono text-emerald-400 font-bold">
                        ₹{Math.round(exp.eligible_amount).toLocaleString()} elg.
                      </div>
                    ) : (isDup || isViolation || exp.eligible_amount === 0) ? (
                      <div className="text-[9px] font-mono text-rose-400 font-medium">
                        ₹0 elg. (Excluded)
                      </div>
                    ) : null}
                    <div className="text-[10px] text-slate-500 flex items-center justify-end gap-1 mt-0.5">
                      <span>Inspect</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </div>
                  </div>
                </div>

                {/* Violation flag note */}
                {isViolation && exp.flags && exp.flags.length > 0 && (
                  <div className="mt-2 text-[11px] text-rose-300 bg-rose-500/10 border border-rose-500/20 px-2.5 py-1 rounded-md flex items-center gap-1.5">
                    <Ban className="w-3.5 h-3.5 shrink-0 text-rose-400" />
                    <span>{exp.flags[0].message} (Excluded from submission)</span>
                  </div>
                )}

                {/* Sub-note if capped by policy allowance */}
                {isCapped && (
                  <div className="mt-2 text-[11px] text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-md flex items-center justify-between">
                    <span>Allowance limit reached</span>
                    <span className="font-mono font-semibold text-emerald-300">
                      ₹{Math.round(exp.eligible_amount).toLocaleString()} eligible • ₹{Math.round(exp.exception_amount).toLocaleString()} excess
                    </span>
                  </div>
                )}

                {/* Sub-note if missing business purpose or date */}
                {isClar && exp.clarification_prompt && (
                  <div className="mt-2 text-[11px] text-amber-300 bg-amber-500/10 border border-amber-500/20 px-2 py-1 rounded-md flex items-center gap-1.5">
                    <AlertTriangle className="w-3 h-3 shrink-0" />
                    <span className="truncate">{exp.clarification_prompt}</span>
                  </div>
                )}

                {/* Duplicate reference note */}
                {isDup && (
                  <div className="mt-2 text-[11px] text-rose-300 bg-rose-500/10 border border-rose-500/20 px-2.5 py-1.5 rounded-md flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <Copy className="w-3.5 h-3.5 shrink-0 text-rose-400" />
                      <span className="truncate">Exact match duplicate of earlier receipt. Excluded from submission.</span>
                    </div>
                    {onDeleteExpense && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteExpense(exp.id);
                        }}
                        className="shrink-0 px-2 py-0.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-semibold text-[10px] flex items-center gap-1 transition shadow-sm cursor-pointer"
                        title="Remove duplicate from claim"
                      >
                        <Trash2 className="w-2.5 h-2.5" />
                        <span>Remove Duplicate</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Bottom Action Footer */}
      <div className="p-3.5 border-t border-slate-800 bg-slate-900/90 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-slate-400">Net Payable</div>
          <div className="text-base font-bold font-mono text-emerald-400">
            ₹{Math.round(summary.eligible_amount).toLocaleString()}
          </div>
        </div>

        <div className="flex flex-col items-end">
          {expenses.length > 0 && summary.eligible_amount <= 0 && (
            <span className="text-[10px] text-amber-400 mb-1 flex items-center gap-1 font-medium">
              <AlertTriangle className="w-3 h-3 shrink-0" />
              <span>₹0 eligible claims cannot be submitted</span>
            </span>
          )}
          <button
            onClick={onSubmitClaim}
            disabled={isSubmitting || session?.status === 'submitted' || expenses.length === 0 || summary.eligible_amount <= 0}
            title={summary.eligible_amount <= 0 ? "Cannot submit claim with ₹0 eligible reimbursement" : "Submit Claim to Corporate Finance"}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white shadow-lg shadow-emerald-500/25 transition transform active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <Send className="w-3.5 h-3.5" />
            <span>
              {session?.status === 'submitted'
                ? 'Claim Submitted'
                : summary.eligible_amount <= 0 && expenses.length > 0
                ? 'Net ₹0 (Ineligible)'
                : 'Submit Claim'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
