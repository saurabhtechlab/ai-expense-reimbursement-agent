import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  FileText, 
  BarChart3, 
  Settings, 
  Plus, 
  Search, 
  Filter, 
  ArrowLeft, 
  Download, 
  Trash2, 
  Edit3, 
  ExternalLink, 
  Building, 
  Receipt, 
  Calendar, 
  User, 
  RefreshCw,
  Check,
  X
} from 'lucide-react';

export default function AdminPortal({ onBackToEmployee }) {
  const [activeTab, setActiveTab] = useState('records'); // 'records', 'reports', 'policies'
  const [loading, setLoading] = useState(false);

  // Claims state
  const [claims, setClaims] = useState([]);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Reports state
  const [reportsData, setReportsData] = useState(null);

  // Policies state
  const [policies, setPolicies] = useState([]);
  const [isPolicyModalOpen, setIsPolicyModalOpen] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState(null);

  // Rejection modal state
  const [rejectingClaimId, setRejectingClaimId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');

  // Fetch initial data
  useEffect(() => {
    fetchClaims();
    fetchReports();
    fetchPolicies();
  }, []);

  const fetchClaims = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter && statusFilter !== 'all') params.append('status', statusFilter);
      if (categoryFilter && categoryFilter !== 'all') params.append('category', categoryFilter);
      if (searchQuery.trim()) params.append('search', searchQuery.trim());
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const res = await fetch(`/api/admin/claims?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setClaims(data);
      }
    } catch (err) {
      console.error("Failed to fetch claims:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async () => {
    try {
      const res = await fetch('/api/admin/reports');
      if (res.ok) {
        const data = await res.json();
        setReportsData(data);
      }
    } catch (err) {
      console.error("Failed to fetch reports:", err);
    }
  };

  const fetchPolicies = async () => {
    try {
      const res = await fetch('/api/admin/policies');
      if (res.ok) {
        const data = await res.json();
        setPolicies(data);
      }
    } catch (err) {
      console.error("Failed to fetch policies:", err);
    }
  };

  const handleUpdateClaimStatus = async (claimId, newStatus, reason = '') => {
    try {
      const res = await fetch(`/api/admin/claims/${claimId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          rejection_reason: reason || undefined,
          reviewed_by: "Finance Admin"
        })
      });
      if (res.ok) {
        fetchClaims();
        fetchReports();
        if (selectedClaim && selectedClaim.id === claimId) {
          const detailRes = await fetch(`/api/admin/claims/${claimId}`);
          if (detailRes.ok) setSelectedClaim(await detailRes.json());
        }
      }
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const handleTogglePolicy = async (policyId, currentActive) => {
    try {
      const res = await fetch(`/api/admin/policies/${policyId}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !currentActive })
      });
      if (res.ok) fetchPolicies();
    } catch (err) {
      console.error("Failed to toggle policy:", err);
    }
  };

  const handleDeletePolicy = async (policyId) => {
    if (!confirm("Are you sure you want to delete this policy rule?")) return;
    try {
      const res = await fetch(`/api/admin/policies/${policyId}`, { method: 'DELETE' });
      if (res.ok) fetchPolicies();
    } catch (err) {
      console.error("Failed to delete policy:", err);
    }
  };

  const handleSavePolicy = async (policyData) => {
    try {
      const isEdit = Boolean(editingPolicy?.id);
      const url = isEdit ? `/api/admin/policies/${editingPolicy.id}` : '/api/admin/policies';
      const method = isEdit ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(policyData)
      });
      if (res.ok) {
        setIsPolicyModalOpen(false);
        setEditingPolicy(null);
        fetchPolicies();
      }
    } catch (err) {
      console.error("Failed to save policy:", err);
    }
  };

  const handleInspectClaim = async (claimId) => {
    try {
      const res = await fetch(`/api/admin/claims/${claimId}`);
      if (res.ok) {
        setSelectedClaim(await res.json());
      }
    } catch (err) {
      console.error("Failed to load claim detail:", err);
    }
  };

  const handleDownloadCSV = () => {
    if (!claims || claims.length === 0) return;
    const headers = ["Claim ID", "Voucher ID", "Employee", "Department", "Date", "Status", "Total Amount", "Eligible Amount", "Exceptions"];
    const rows = claims.map(c => [
      c.id,
      c.voucher_id,
      `"${c.employee_name} (${c.employee_id})"`,
      `"${c.department}"`,
      c.submission_date,
      c.status,
      c.total_amount,
      c.eligible_amount,
      c.exception_amount
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `reimbursement_claims_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const kpis = reportsData?.kpis || {
    total_claims: claims.length,
    under_process_count: claims.filter(c => c.status === 'under_process').length,
    approved_count: claims.filter(c => c.status === 'approved').length,
    rejected_count: claims.filter(c => c.status === 'rejected').length,
    total_claimed_amount: claims.reduce((s, c) => s + c.total_amount, 0),
    total_paid_out: claims.filter(c => c.status === 'approved').reduce((s, c) => s + c.eligible_amount, 0)
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Admin Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 px-4 py-3">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={onBackToEmployee}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Employee Assistant</span>
            </button>
            <div className="h-5 w-px bg-slate-800 hidden md:block" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-black tracking-tight text-white flex items-center gap-1.5">
                  <ShieldCheck className="w-5 h-5 text-indigo-400" />
                  ReimburseAI Admin Portal
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  URL: /admin
                </span>
              </div>
              <p className="text-[11px] text-slate-400 m-0">Corporate Claims Audit, Reports & Policy Configuration</p>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
            <div className="px-2.5 py-1 rounded-lg bg-slate-950/70 border border-slate-800 text-center shrink-0">
              <div className="text-[9px] text-slate-400 font-medium uppercase">Total Claims</div>
              <div className="text-xs font-bold font-mono text-white">{kpis.total_claims}</div>
            </div>
            <div className="px-2.5 py-1 rounded-lg bg-amber-950/30 border border-amber-800/40 text-center shrink-0">
              <div className="text-[9px] text-amber-400 font-medium uppercase">Under Process</div>
              <div className="text-xs font-bold font-mono text-amber-400">{kpis.under_process_count}</div>
            </div>
            <div className="px-2.5 py-1 rounded-lg bg-emerald-950/30 border border-emerald-800/40 text-center shrink-0">
              <div className="text-[9px] text-emerald-400 font-medium uppercase">Approved</div>
              <div className="text-xs font-bold font-mono text-emerald-400">{kpis.approved_count}</div>
            </div>
            <div className="px-2.5 py-1 rounded-lg bg-rose-950/30 border border-rose-800/40 text-center shrink-0">
              <div className="text-[9px] text-rose-400 font-medium uppercase">Rejected</div>
              <div className="text-xs font-bold font-mono text-rose-400">{kpis.rejected_count}</div>
            </div>
            <div className="px-2.5 py-1 rounded-lg bg-indigo-950/30 border border-indigo-800/40 text-center shrink-0">
              <div className="text-[9px] text-indigo-400 font-medium uppercase">Total Payout</div>
              <div className="text-xs font-bold font-mono text-indigo-300">₹{Math.round(kpis.total_paid_out).toLocaleString()}</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Tab Switcher */}
      <div className="border-b border-slate-800 bg-slate-900/60 px-4">
        <div className="max-w-7xl mx-auto flex items-center gap-2">
          <button
            onClick={() => setActiveTab('records')}
            className={`px-4 py-2.5 text-xs font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'records'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Submitted Records ({claims.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('reports')}
            className={`px-4 py-2.5 text-xs font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'reports'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Multiple Reports & Analytics</span>
          </button>

          <button
            onClick={() => setActiveTab('policies')}
            className={`px-4 py-2.5 text-xs font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'policies'
                ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Settings className="w-4 h-4" />
            <span>Policy Rules Configuration ({policies.length})</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="max-w-7xl w-full mx-auto p-4 flex-1">
        {/* ========================================================================= */}
        {/* TAB 1: SUBMITTED RECORDS WITH DYNAMIC FILTERS */}
        {/* ========================================================================= */}
        {activeTab === 'records' && (
          <div className="space-y-4">
            {/* Filter Bar */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
                <div className="flex items-center gap-2 w-full md:w-auto flex-1">
                  <div className="relative flex-1 max-w-md">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      placeholder="Search Claim ID, Voucher, Employee or Dept..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && fetchClaims()}
                      className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <button
                    onClick={fetchClaims}
                    className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition cursor-pointer"
                  >
                    Search
                  </button>
                </div>

                <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
                  {/* Status Filter */}
                  <select
                    value={statusFilter}
                    onChange={(e) => {
                      setStatusFilter(e.target.value);
                      setTimeout(fetchClaims, 50);
                    }}
                    className="px-3 py-2 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="all">All Statuses</option>
                    <option value="under_process">Under Process</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>

                  {/* Category Filter */}
                  <select
                    value={categoryFilter}
                    onChange={(e) => {
                      setCategoryFilter(e.target.value);
                      setTimeout(fetchClaims, 50);
                    }}
                    className="px-3 py-2 bg-slate-950 border border-slate-700/80 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="all">All Categories</option>
                    <option value="Mobile Headset">Mobile Headset</option>
                    <option value="Driver Salary">Driver Salary</option>
                    <option value="Fuel">Fuel</option>
                    <option value="Hotel">Hotel</option>
                    <option value="Taxi">Taxi</option>
                    <option value="Meals">Meals</option>
                    <option value="Telecommunication">Telecommunication</option>
                  </select>

                  <button
                    onClick={handleDownloadCSV}
                    className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition cursor-pointer"
                    title="Export claims to CSV"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Export CSV</span>
                  </button>
                </div>
              </div>

              {/* Date Range Row */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                <span>Filter by Date Range:</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="px-2.5 py-1 bg-slate-950 border border-slate-700/80 rounded text-slate-200 text-xs"
                />
                <span>to</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="px-2.5 py-1 bg-slate-950 border border-slate-700/80 rounded text-slate-200 text-xs"
                />
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setStatusFilter('all');
                    setCategoryFilter('all');
                    setStartDate('');
                    setEndDate('');
                    setTimeout(fetchClaims, 50);
                  }}
                  className="text-indigo-400 hover:underline cursor-pointer ml-auto"
                >
                  Reset All Filters
                </button>
              </div>
            </div>

            {/* Claims Table */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="p-3">Claim Reference</th>
                      <th className="p-3">Employee</th>
                      <th className="p-3">Submission Date</th>
                      <th className="p-3">Total Amount</th>
                      <th className="p-3">Approved / Eligible</th>
                      <th className="p-3">Exceptions</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {claims.length === 0 ? (
                      <tr>
                        <td colSpan="8" className="p-8 text-center text-slate-500">
                          No submitted records match your active filters.
                        </td>
                      </tr>
                    ) : (
                      claims.map((claim) => {
                        const isUnderProcess = claim.status === 'under_process';
                        const isApproved = claim.status === 'approved';
                        const isRejected = claim.status === 'rejected';

                        return (
                          <tr key={claim.id} className="hover:bg-slate-800/30 transition">
                            <td className="p-3 font-mono font-bold text-white">
                              <div>{claim.id}</div>
                              <div className="text-[10px] text-slate-500 font-sans">{claim.voucher_id}</div>
                            </td>
                            <td className="p-3">
                              <div className="font-semibold text-slate-200">{claim.employee_name}</div>
                              <div className="text-[10px] text-slate-400">{claim.employee_id} • {claim.department}</div>
                            </td>
                            <td className="p-3 text-slate-300 font-mono">
                              {claim.submission_date}
                            </td>
                            <td className="p-3 font-mono font-bold text-slate-100">
                              ₹{Math.round(claim.total_amount).toLocaleString()}
                              <span className="text-[10px] text-slate-500 block font-sans">{claim.expense_count} bill(s)</span>
                            </td>
                            <td className="p-3 font-mono font-bold text-emerald-400">
                              ₹{Math.round(claim.eligible_amount).toLocaleString()}
                            </td>
                            <td className="p-3 font-mono font-bold text-rose-400">
                              ₹{Math.round(claim.exception_amount).toLocaleString()}
                            </td>
                            <td className="p-3">
                              {isUnderProcess && (
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                  <Clock className="w-3 h-3" /> Under Process
                                </span>
                              )}
                              {isApproved && (
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                  <CheckCircle className="w-3 h-3" /> Approved
                                </span>
                              )}
                              {isRejected && (
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                  <XCircle className="w-3 h-3" /> Rejected
                                </span>
                              )}
                            </td>
                            <td className="p-3 text-right">
                              <div className="flex items-center justify-end gap-1.5">
                                <button
                                  onClick={() => handleInspectClaim(claim.id)}
                                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition cursor-pointer"
                                >
                                  Inspect
                                </button>
                                {isUnderProcess && (
                                  <>
                                    <button
                                      onClick={() => handleUpdateClaimStatus(claim.id, 'approved')}
                                      className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition cursor-pointer"
                                      title="Approve this claim"
                                    >
                                      Approve
                                    </button>
                                    <button
                                      onClick={() => {
                                        setRejectingClaimId(claim.id);
                                        setRejectionReason('');
                                      }}
                                      className="px-2 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition cursor-pointer"
                                      title="Reject this claim"
                                    >
                                      Reject
                                    </button>
                                  </>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: MULTIPLE REPORTS BASED ON DATA */}
        {/* ========================================================================= */}
        {activeTab === 'reports' && reportsData && (
          <div className="space-y-6">
            {/* Top Report KPI Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Total Claimed</div>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  ₹{Math.round(reportsData.kpis.total_claimed_amount).toLocaleString()}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">{reportsData.kpis.total_claims} Claims Submitted</div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
                <div className="text-[10px] uppercase tracking-wider text-emerald-400 font-bold">Approved Payout</div>
                <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                  ₹{Math.round(reportsData.kpis.total_paid_out).toLocaleString()}
                </div>
                <div className="text-[10px] text-emerald-500/80 mt-0.5">{reportsData.kpis.approved_count} Claims Approved</div>
              </div>

              <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40">
                <div className="text-[10px] uppercase tracking-wider text-rose-400 font-bold">Policy Savings (Blocked)</div>
                <div className="text-xl font-bold font-mono text-rose-400 mt-1">
                  ₹{Math.round(reportsData.kpis.total_exception_amount).toLocaleString()}
                </div>
                <div className="text-[10px] text-rose-400/80 mt-0.5">Exceptions & Duplicates Protected</div>
              </div>

              <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-800/40">
                <div className="text-[10px] uppercase tracking-wider text-indigo-400 font-bold">Active Approval Rate</div>
                <div className="text-xl font-bold font-mono text-indigo-300 mt-1">
                  {reportsData.kpis.total_claims > 0
                    ? Math.round((reportsData.kpis.approved_count / reportsData.kpis.total_claims) * 100)
                    : 0}%
                </div>
                <div className="text-[10px] text-indigo-400/80 mt-0.5">{reportsData.kpis.under_process_count} Pending Review</div>
              </div>
            </div>

            {/* Report 1 & 2: Spend by Category & Monthly Trends */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Report 1: Spend by Category */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-white m-0 flex items-center gap-1.5">
                    <BarChart3 className="w-4 h-4 text-indigo-400" />
                    Report 1: Spend Breakdown by Category
                  </h3>
                  <span className="text-[10px] text-slate-500 font-mono">Live Audit</span>
                </div>

                <div className="space-y-2.5 pt-1">
                  {reportsData.category_spend.map((cat, idx) => {
                    const totalSpend = reportsData.kpis.total_claimed_amount || 1;
                    const percent = Math.round((cat.total_amount / totalSpend) * 100);

                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-200">{cat.category} ({cat.bill_count} bills)</span>
                          <span className="font-mono text-white font-bold">
                            ₹{Math.round(cat.total_amount).toLocaleString()} <span className="text-slate-500 text-[10px]">({percent}%)</span>
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden flex">
                          <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-teal-400 rounded-full"
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                          <span className="text-emerald-400">₹{Math.round(cat.eligible_amount).toLocaleString()} eligible</span>
                          {cat.exception_amount > 0 && (
                            <span className="text-rose-400">₹{Math.round(cat.exception_amount).toLocaleString()} exception</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Report 2: Monthly Trends */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-white m-0 flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-indigo-400" />
                    Report 2: Monthly Reimbursement Trends
                  </h3>
                  <span className="text-[10px] text-slate-500 font-mono">Timeline</span>
                </div>

                <div className="overflow-x-auto pt-1">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 uppercase text-[9px] border-b border-slate-800">
                      <tr>
                        <th className="p-2">Month</th>
                        <th className="p-2">Claims</th>
                        <th className="p-2">Total Claimed</th>
                        <th className="p-2">Eligible</th>
                        <th className="p-2">Approved</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {reportsData.monthly_trend.map((m, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="p-2 font-mono font-bold text-indigo-300">{m.month || "Current"}</td>
                          <td className="p-2 font-mono">{m.claim_count}</td>
                          <td className="p-2 font-mono font-bold text-white">₹{Math.round(m.total_amount).toLocaleString()}</td>
                          <td className="p-2 font-mono text-emerald-400">₹{Math.round(m.eligible_amount).toLocaleString()}</td>
                          <td className="p-2 font-mono text-slate-300">{m.approved_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Report 3 & 4: Top Merchants & Department Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Report 3: Top Merchants / Vendors */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-white m-0 flex items-center gap-1.5">
                    <Receipt className="w-4 h-4 text-indigo-400" />
                    Report 3: Top Merchants & Vendors by Spend
                  </h3>
                </div>

                <div className="overflow-x-auto pt-1">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 uppercase text-[9px] border-b border-slate-800">
                      <tr>
                        <th className="p-2">Vendor Name</th>
                        <th className="p-2">Category</th>
                        <th className="p-2">Frequency</th>
                        <th className="p-2 text-right">Total Spend</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {reportsData.top_merchants.map((vm, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="p-2 font-semibold text-slate-200">{vm.merchant}</td>
                          <td className="p-2 text-[11px] text-slate-400">{vm.category}</td>
                          <td className="p-2 font-mono text-slate-300">{vm.claim_frequency} bill(s)</td>
                          <td className="p-2 font-mono font-bold text-white text-right">
                            ₹{Math.round(vm.total_spend).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Report 4: Department Spend */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-white m-0 flex items-center gap-1.5">
                    <Building className="w-4 h-4 text-indigo-400" />
                    Report 4: Department Spend Analysis
                  </h3>
                </div>

                <div className="overflow-x-auto pt-1">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 uppercase text-[9px] border-b border-slate-800">
                      <tr>
                        <th className="p-2">Department</th>
                        <th className="p-2">Claims Count</th>
                        <th className="p-2">Claimed Amount</th>
                        <th className="p-2 text-right">Approved Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {reportsData.department_spend.map((dept, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="p-2 font-semibold text-slate-200">{dept.department}</td>
                          <td className="p-2 font-mono">{dept.claims_count}</td>
                          <td className="p-2 font-mono font-bold text-white">₹{Math.round(dept.total_claimed).toLocaleString()}</td>
                          <td className="p-2 font-mono text-emerald-400 font-bold text-right">
                            ₹{Math.round(dept.total_approved).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: POLICY RULES CONFIGURATION */}
        {/* ========================================================================= */}
        {activeTab === 'policies' && (
          <div className="space-y-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider m-0">Corporate Policy Engine Rules</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Configure caps, allowable vendor restrictions, and mandatory verification details. Newly added policies apply instantly.
                </p>
              </div>
              <button
                onClick={() => {
                  setEditingPolicy(null);
                  setIsPolicyModalOpen(true);
                }}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-lg shadow-indigo-600/30 transition cursor-pointer shrink-0"
              >
                <Plus className="w-4 h-4" />
                <span>Configure New Policy</span>
              </button>
            </div>

            {/* Policy Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {policies.map((p) => {
                const isActive = Boolean(p.is_active);

                return (
                  <div
                    key={p.id}
                    className={`p-4 rounded-xl border transition flex flex-col justify-between ${
                      isActive
                        ? 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                        : 'bg-slate-950/60 border-slate-900 opacity-60'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <div className="text-[10px] font-mono text-indigo-400 font-bold">{p.id}</div>
                          <h4 className="text-sm font-bold text-white mt-0.5 m-0">{p.rule_name}</h4>
                        </div>
                        <button
                          onClick={() => handleTogglePolicy(p.id, isActive)}
                          className={`px-2 py-0.5 rounded text-[10px] font-bold cursor-pointer transition ${
                            isActive
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {isActive ? 'ACTIVE' : 'INACTIVE'}
                        </button>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed mb-3">
                        {p.description || "Policy rule description"}
                      </p>

                      <div className="space-y-1.5 text-[11px] bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 font-mono">
                        <div className="flex justify-between text-slate-300">
                          <span className="text-slate-400 font-sans">Category:</span>
                          <span className="font-bold text-white">{p.category}</span>
                        </div>
                        <div className="flex justify-between text-slate-300">
                          <span className="text-slate-400 font-sans">Max Cap:</span>
                          <span className="font-bold text-emerald-400">
                            {p.max_limit > 0 ? `₹${Math.round(p.max_limit).toLocaleString()}` : "No Limit"}
                          </span>
                        </div>
                        <div className="flex justify-between text-slate-300">
                          <span className="text-slate-400 font-sans">Period:</span>
                          <span className="text-indigo-300 uppercase text-[10px]">{p.limit_period}</span>
                        </div>
                        {p.vendor_restriction && (
                          <div className="flex justify-between text-slate-300">
                            <span className="text-slate-400 font-sans">Vendor Only:</span>
                            <span className="text-amber-400 font-semibold">{p.vendor_restriction}</span>
                          </div>
                        )}
                        <div className="flex items-center gap-2 pt-1 border-t border-slate-800 text-[10px] font-sans">
                          {p.require_business_purpose ? (
                            <span className="text-emerald-400 flex items-center gap-0.5">
                              <Check className="w-3 h-3" /> Purpose Req.
                            </span>
                          ) : null}
                          {p.require_date ? (
                            <span className="text-emerald-400 flex items-center gap-0.5">
                              <Check className="w-3 h-3" /> Date Req.
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-1.5 pt-3 mt-3 border-t border-slate-800/80">
                      <button
                        onClick={() => {
                          setEditingPolicy(p);
                          setIsPolicyModalOpen(true);
                        }}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
                      >
                        <Edit3 className="w-3 h-3" />
                        <span>Edit</span>
                      </button>
                      <button
                        onClick={() => handleDeletePolicy(p.id)}
                        className="px-2 py-1 rounded bg-rose-950/30 hover:bg-rose-900/50 text-rose-300 text-xs font-semibold flex items-center gap-1 transition cursor-pointer"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>

      {/* ========================================================================= */}
      {/* MODAL 1: INSPECT CLAIM DETAILS */}
      {/* ========================================================================= */}
      {selectedClaim && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <div>
                <h3 className="text-base font-bold text-white m-0 flex items-center gap-2">
                  <span>Claim {selectedClaim.id}</span>
                  <span className="text-xs text-slate-400">({selectedClaim.voucher_id})</span>
                </h3>
                <div className="text-xs text-slate-400 mt-0.5">
                  {selectedClaim.employee_name} ({selectedClaim.employee_id}) • {selectedClaim.department} • Submitted on {selectedClaim.submission_date}
                </div>
              </div>
              <button
                onClick={() => setSelectedClaim(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 flex-1 overflow-y-auto space-y-4">
              {/* Financial Snapshot */}
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-bold uppercase">Total Claimed</div>
                  <div className="text-lg font-bold font-mono text-white mt-0.5">
                    ₹{Math.round(selectedClaim.total_amount).toLocaleString()}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
                  <div className="text-[10px] text-emerald-400 font-bold uppercase">Eligible Payout</div>
                  <div className="text-lg font-bold font-mono text-emerald-400 mt-0.5">
                    ₹{Math.round(selectedClaim.eligible_amount).toLocaleString()}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-800/40">
                  <div className="text-[10px] text-rose-400 font-bold uppercase">Exceptions / Deductions</div>
                  <div className="text-lg font-bold font-mono text-rose-400 mt-0.5">
                    ₹{Math.round(selectedClaim.exception_amount).toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Itemized Bills */}
              <div>
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                  Itemized Bills & Receipts ({selectedClaim.expenses?.length || 0})
                </h4>
                <div className="space-y-2">
                  {selectedClaim.expenses?.map((exp) => (
                    <div
                      key={exp.id}
                      className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                          <Receipt className="w-4 h-4 text-indigo-400" />
                        </div>
                        <div>
                          <div className="text-xs font-bold text-white flex items-center gap-2">
                            <span>{exp.merchant}</span>
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-normal">
                              {exp.category}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 mt-0.5">
                            {exp.file_name} • Date: {exp.date || "N/A"} • Purpose: {exp.business_purpose || "Not specified"}
                          </div>
                          {exp.flags && exp.flags.length > 0 && (
                            <div className="text-[10px] text-rose-400 flex items-center gap-1 mt-1">
                              <AlertTriangle className="w-3 h-3 shrink-0" />
                              <span>{exp.flags[0].message}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <div className="text-xs font-bold font-mono text-white">
                          ₹{Math.round(exp.amount).toLocaleString()}
                        </div>
                        <div className="text-[10px] font-mono text-emerald-400">
                          ₹{Math.round(exp.eligible_amount).toLocaleString()} approved
                        </div>
                        {exp.preview_url && (
                          <a
                            href={exp.preview_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-[10px] text-indigo-400 hover:underline mt-1"
                          >
                            <ExternalLink className="w-2.5 h-2.5" /> View Receipt
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Audit Trail */}
              {selectedClaim.audit_logs && selectedClaim.audit_logs.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Audit History</h4>
                  <div className="bg-slate-950 rounded-xl p-3 border border-slate-800 space-y-2 text-xs">
                    {selectedClaim.audit_logs.map((log) => (
                      <div key={log.id} className="flex justify-between items-center text-slate-300">
                        <div>
                          <span className="font-semibold text-white">{log.action}: </span>
                          <span className="text-slate-400">{log.details}</span>
                        </div>
                        <span className="text-[10px] font-mono text-slate-500">{log.timestamp}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer with Approve / Reject buttons */}
            <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
              <div className="text-xs text-slate-400">
                Status: <span className="font-bold uppercase text-white">{selectedClaim.status}</span>
              </div>
              <div className="flex items-center gap-2">
                {selectedClaim.status === 'under_process' && (
                  <>
                    <button
                      onClick={() => handleUpdateClaimStatus(selectedClaim.id, 'approved')}
                      className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition cursor-pointer"
                    >
                      Approve Claim
                    </button>
                    <button
                      onClick={() => {
                        setRejectingClaimId(selectedClaim.id);
                        setRejectionReason('');
                      }}
                      className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs transition cursor-pointer"
                    >
                      Reject Claim
                    </button>
                  </>
                )}
                <button
                  onClick={() => setSelectedClaim(null)}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs font-semibold cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: REJECT CLAIM REASON MODAL */}
      {/* ========================================================================= */}
      {rejectingClaimId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white m-0">Reject Claim #{rejectingClaimId}</h3>
            <p className="text-xs text-slate-400">
              Please enter the corporate policy reason for rejecting this claim. This will be stored in the audit trail.
            </p>
            <textarea
              rows="3"
              placeholder="e.g. Non-Reliance vendor for mobile headset, or invalid receipt documentation..."
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setRejectingClaimId(null)}
                className="px-3 py-1.5 rounded bg-slate-800 text-slate-300 text-xs font-medium cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  handleUpdateClaimStatus(rejectingClaimId, 'rejected', rejectionReason);
                  setRejectingClaimId(null);
                }}
                className="px-4 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold cursor-pointer"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 3: CONFIGURE / EDIT POLICY RULE MODAL */}
      {/* ========================================================================= */}
      {isPolicyModalOpen && (
        <PolicyRuleFormModal
          policy={editingPolicy}
          onClose={() => {
            setIsPolicyModalOpen(false);
            setEditingPolicy(null);
          }}
          onSave={handleSavePolicy}
        />
      )}
    </div>
  );
}

function PolicyRuleFormModal({ policy, onClose, onSave }) {
  const [ruleName, setRuleName] = useState(policy?.rule_name || "");
  const [category, setCategory] = useState(policy?.category || "Meals");
  const [keywords, setKeywords] = useState(policy?.keywords || "");
  const [maxLimit, setMaxLimit] = useState(policy?.max_limit || 5000);
  const [limitPeriod, setLimitPeriod] = useState(policy?.limit_period || "monthly");
  const [vendorRestriction, setVendorRestriction] = useState(policy?.vendor_restriction || "");
  const [requirePurpose, setRequirePurpose] = useState(Boolean(policy?.require_business_purpose));
  const [requireDate, setRequireDate] = useState(Boolean(policy?.require_date));
  const [isActive, setIsActive] = useState(policy ? Boolean(policy.is_active) : true);
  const [description, setDescription] = useState(policy?.description || "");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      rule_name: ruleName,
      category,
      keywords,
      max_limit: parseFloat(maxLimit) || 0.0,
      limit_period: limitPeriod,
      vendor_restriction: vendorRestriction.trim(),
      require_business_purpose: requirePurpose,
      require_date: requireDate,
      is_active: isActive,
      description
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-white m-0 flex items-center gap-2">
            <Settings className="w-4 h-4 text-indigo-400" />
            {policy ? `Edit Policy Rule: ${policy.id}` : "Configure New Policy Rule"}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Policy Rule Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Broadband & Internet Allowance"
              value={ruleName}
              onChange={(e) => setRuleName(e.target.value)}
              className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Category</label>
              <input
                type="text"
                required
                placeholder="e.g. Telecommunication"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Limit Period</label>
              <select
                value={limitPeriod}
                onChange={(e) => setLimitPeriod(e.target.value)}
                className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="monthly">Per Month</option>
                <option value="financial_year">Per Financial Year</option>
                <option value="per_claim">Per Transaction / Claim</option>
                <option value="no_limit">No Limit</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Maximum Allowance Limit (₹)</label>
              <input
                type="number"
                min="0"
                step="500"
                value={maxLimit}
                onChange={(e) => setMaxLimit(e.target.value)}
                className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Mandatory Vendor (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Reliance Digital (Leave blank for Any)"
                value={vendorRestriction}
                onChange={(e) => setVendorRestriction(e.target.value)}
                className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Matching Keywords (comma-separated)</label>
            <input
              type="text"
              placeholder="e.g. broadband, fiber, airtel, wifi, internet"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Description / Policy Mandate</label>
            <textarea
              rows="2"
              placeholder="Official mandate details for employee guide..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full p-2 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Checkboxes */}
          <div className="space-y-2 pt-2 border-t border-slate-800">
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={requirePurpose}
                onChange={(e) => setRequirePurpose(e.target.checked)}
                className="rounded border-slate-700 text-indigo-600 focus:ring-0"
              />
              <span>Require Business Purpose (Clarification asked if missing)</span>
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={requireDate}
                onChange={(e) => setRequireDate(e.target.checked)}
                className="rounded border-slate-700 text-indigo-600 focus:ring-0"
              />
              <span>Require Receipt Date (Clarification asked if missing)</span>
            </label>
            <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="rounded border-slate-700 text-indigo-600 focus:ring-0"
              />
              <span>Activate this rule immediately</span>
            </label>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 font-medium cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold cursor-pointer shadow-md transition"
            >
              Save Policy Rule
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
