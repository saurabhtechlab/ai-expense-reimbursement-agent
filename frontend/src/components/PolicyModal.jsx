import React from 'react';
import { X, ShieldCheck, AlertTriangle, CheckCircle, Info, Landmark, Headphones, Car, Fuel } from 'lucide-react';

export default function PolicyModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Landmark className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white m-0">Corporate Reimbursement Policies</h2>
            <p className="text-xs text-slate-400">Rules enforced automatically by ReimburseAI Policy Engine</p>
          </div>
        </div>

        <div className="space-y-3 text-sm">
          {/* New Policy 1: Mobile Headset */}
          <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-500/30 flex items-start gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-300 shrink-0">
              <Headphones className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-white flex items-center gap-2">
                <span>Mobile Headset Reimbursement</span>
                <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-md font-mono">Max ₹20,000 / FY</span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                An employee can reimburse <strong className="text-white">up to ₹20,000</strong> in one financial year.
                <span className="block text-amber-300 font-medium mt-0.5">⚠️ Mandatory: Invoice MUST be from Reliance Digital. Other retailers (Croma, Amazon, etc.) are strictly ineligible.</span>
              </p>
            </div>
          </div>

          {/* New Policy 2: Driver Salary */}
          <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30 flex items-start gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-300 shrink-0">
              <Car className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-white flex items-center gap-2">
                <span>Travel Assistance (Driver Salary)</span>
                <span className="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-md font-mono">Max ₹10,000 / Month</span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                An employee can reimburse <strong className="text-white">up to ₹10,000 per month</strong> for Driver salary. Voucher must indicate the active service month.
              </p>
            </div>
          </div>

          {/* New Policy 3: Fuel Expenses */}
          <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex items-start gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300 shrink-0">
              <Fuel className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-white flex items-center gap-2">
                <span>Fuel Expenses</span>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-md font-mono">Max ₹15,000 / Month</span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                An employee can reimburse <strong className="text-white">up to ₹15,000 per month</strong> for fuel expenses (Petrol/Diesel/CNG). Tax invoice required from recognized fuel stations.
              </p>
            </div>
          </div>

          {/* Policy 4: Hotel */}
          <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-start gap-3">
            <span className="text-base">🏨</span>
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-2">
                <span>Hotel & Lodging</span>
                <span className="text-[10px] bg-slate-700 text-slate-300 px-2 py-0.5 rounded-md font-mono">Max ₹8,000 / Night</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Must include business purpose. Excess over ₹8,000 routed as policy exception.
              </p>
            </div>
          </div>

          {/* Policy 5: Taxi */}
          <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-start gap-3">
            <span className="text-base">🚕</span>
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-2">
                <span>Taxi & Ground Transport</span>
                <span className="text-[10px] bg-slate-700 text-slate-300 px-2 py-0.5 rounded-md font-mono">Date Mandatory</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Travel date required on receipt for itinerary matching.
              </p>
            </div>
          </div>

          {/* Policy 6: Duplicates */}
          <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-start gap-3">
            <span className="text-base">🔴</span>
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-2">
                <span>Duplicate Detection</span>
                <span className="text-[10px] bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-md font-mono">Zero Tolerance</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Exact matches (identical vendor + amount) are automatically flagged and excluded.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition cursor-pointer"
          >
            Got it, thanks
          </button>
        </div>
      </div>
    </div>
  );
}
