import React from 'react';
import { Sparkles, UploadCloud, RotateCcw, ShieldCheck, FileSpreadsheet, Building2, User } from 'lucide-react';

export default function Header({ 
  onLoadSample, 
  onLoadPerks,
  onReset, 
  onOpenPolicy, 
  onOpenAdmin,
  onUploadClick, 
  loading, 
  session 
}) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30 px-4 lg:px-6 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Brand & Employee Identity */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/25 ring-1 ring-white/20">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white m-0">ReimburseAI</h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wide bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full">
                EXPENSE AGENT
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
              <span className="flex items-center gap-1">
                <User className="w-3 h-3 text-slate-500" />
                {session?.employee_name || "Saurabh Gupta"}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Building2 className="w-3 h-3 text-slate-500" />
                {session?.department || "Engineering"} ({session?.employee_id || "EMP-4091"})
              </span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center flex-wrap gap-2">
          {/* Quick Demo Batch Button */}
          <button
            onClick={onLoadSample}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white shadow-md shadow-indigo-500/20 transition-all transform active:scale-95 disabled:opacity-50 cursor-pointer"
            title="Load sample batch of 11 receipts matching prompt scenario"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>11-Receipt Batch</span>
          </button>

          {/* New Policy Batch Button */}
          <button
            onClick={onLoadPerks}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-md shadow-emerald-600/20 transition-all transform active:scale-95 disabled:opacity-50 cursor-pointer"
            title="Test Mobile Headset (Reliance vs Croma), Driver Salary, and Fuel Expense rules"
          >
            <span>🎧🚗</span>
            <span>Headset, Driver & Fuel</span>
          </button>

          {/* Upload Receipts Button */}
          <button
            onClick={onUploadClick}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700/80 text-slate-200 border border-slate-700 transition cursor-pointer"
          >
            <UploadCloud className="w-3.5 h-3.5 text-indigo-400" />
            <span>Upload Bills</span>
          </button>

          {/* Policy Guide */}
          <button
            onClick={onOpenPolicy}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-500/20 transition cursor-pointer"
            title="View corporate policy rules for Mobile Headsets, Driver Salary, Fuel, etc."
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Policy Rules</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          </button>

          {/* Admin Portal Button */}
          <button
            onClick={onOpenAdmin}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 shadow-sm transition cursor-pointer"
            title="Open Admin Portal (/admin) for Submitted Records, Reports & Policy Configuration"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-300" />
            <span>Admin Portal</span>
          </button>

          {/* Reset Session */}
          <button
            onClick={onReset}
            disabled={loading}
            className="p-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition cursor-pointer"
            title="Reset active session"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
