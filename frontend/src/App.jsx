import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatView from './components/ChatView';
import ClaimWorkbench from './components/ClaimWorkbench';
import PolicyModal from './components/PolicyModal';
import ExpenseModal from './components/ExpenseModal';
import ReviewClaimModal from './components/ReviewClaimModal';
import SubmissionSuccessModal from './components/SubmissionSuccessModal';
import AdminPortal from './components/AdminPortal';

export default function App() {
  const [currentView, setCurrentView] = useState(() => {
    return window.location.pathname.startsWith('/admin') ? 'admin' : 'employee';
  });

  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Modals state
  const [isPolicyOpen, setIsPolicyOpen] = useState(false);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [isSuccessOpen, setIsSuccessOpen] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState(null);

  // Synchronize browser history / URL path
  useEffect(() => {
    const handlePopState = () => {
      setCurrentView(window.location.pathname.startsWith('/admin') ? 'admin' : 'employee');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateToAdmin = () => {
    window.history.pushState({}, '', '/admin');
    setCurrentView('admin');
  };

  const navigateToEmployee = () => {
    window.history.pushState({}, '', '/');
    setCurrentView('employee');
  };

  // Initial fetch
  useEffect(() => {
    fetchSession();
  }, []);

  const fetchSession = async () => {
    try {
      const res = await fetch('/api/session');
      if (res.ok) {
        const data = await res.json();
        setSession(data);
      }
    } catch (err) {
      console.error("Failed to load session:", err);
    }
  };

  const handleSendMessage = async (text) => {
    setLoading(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
        if (updated.status === 'submitted') {
          setIsSuccessOpen(true);
        }
      }
    } catch (err) {
      console.error("Chat error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/load-sample-batch', { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
      }
    } catch (err) {
      console.error("Failed to load demo batch:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadPerks = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/load-perks-batch', { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
      }
    } catch (err) {
      console.error("Failed to load benefits batch:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadFiles = async (fileList) => {
    setLoading(true);
    try {
      const formData = new FormData();
      for (let i = 0; i < fileList.length; i++) {
        formData.append("files", fileList[i]);
      }
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
      }
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/session/reset', { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
        setIsSuccessOpen(false);
        setIsReviewOpen(false);
        setSelectedExpense(null);
      }
    } catch (err) {
      console.error("Reset failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveExpense = async (id, updateData) => {
    try {
      const res = await fetch(`/api/expenses/${id}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
      }
    } catch (err) {
      console.error("Expense update error:", err);
    }
  };

  const handleDeleteExpense = async (id) => {
    try {
      const res = await fetch(`/api/expenses/${id}`, { method: 'DELETE' });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
        if (selectedExpense && selectedExpense.id === id) {
          setSelectedExpense(null);
        }
      }
    } catch (err) {
      console.error("Expense delete error:", err);
    }
  };

  const handleSubmitClaim = async () => {
    if (!session || !session.summary || (session.summary.eligible_amount || 0) <= 0) {
      alert("⚠️ Cannot submit claim with ₹0 eligible reimbursement. Only claims with approved/eligible expenses can be submitted.");
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await fetch('/api/submit-claim', { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSession(updated);
        setIsSuccessOpen(true);
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(`⚠️ ${errData.detail || 'Failed to submit claim.'}`);
      }
    } catch (err) {
      console.error("Submit error:", err);
      alert("Submission error occurred. Please check network connection.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (currentView === 'admin') {
    return <AdminPortal onBackToEmployee={navigateToEmployee} />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <Header
        session={session}
        onLoadSample={handleLoadSample}
        onLoadPerks={handleLoadPerks}
        onReset={handleReset}
        onOpenPolicy={() => setIsPolicyOpen(true)}
        onOpenAdmin={navigateToAdmin}
        onUploadClick={() => document.querySelector('input[type="file"]')?.click()}
        loading={loading}
      />

      {/* Main Dual-Pane Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 lg:p-5 flex flex-col lg:flex-row gap-4 h-[calc(100vh-65px)]">
        {/* Left Column: Conversational Assistant */}
        <div className="w-full lg:w-[56%] h-[55vh] lg:h-full flex flex-col min-h-0">
          <ChatView
            session={session}
            onSendMessage={handleSendMessage}
            onUploadFiles={handleUploadFiles}
            onReviewClaim={() => setIsReviewOpen(true)}
            onSubmitClaim={handleSubmitClaim}
            onLoadSample={handleLoadSample}
            onLoadPerks={handleLoadPerks}
            onOpenPolicy={() => setIsPolicyOpen(true)}
            loading={loading}
          />
        </div>

        {/* Right Column: Claim Workbench & Live Audit */}
        <div className="w-full lg:w-[44%] h-[45vh] lg:h-full flex flex-col min-h-0">
          <ClaimWorkbench
            session={session}
            onSelectExpense={(exp) => setSelectedExpense(exp)}
            onSubmitClaim={handleSubmitClaim}
            onOpenPolicy={() => setIsPolicyOpen(true)}
            onDeleteExpense={handleDeleteExpense}
            isSubmitting={isSubmitting}
          />
        </div>
      </main>

      {/* Modals */}
      <PolicyModal
        isOpen={isPolicyOpen}
        onClose={() => setIsPolicyOpen(false)}
      />

      <ExpenseModal
        expense={selectedExpense}
        isOpen={Boolean(selectedExpense)}
        onClose={() => setSelectedExpense(null)}
        onSave={handleSaveExpense}
        onDelete={handleDeleteExpense}
      />

      <ReviewClaimModal
        session={session}
        isOpen={isReviewOpen}
        onClose={() => setIsReviewOpen(false)}
        onSubmitClaim={handleSubmitClaim}
        onSelectExpense={(exp) => setSelectedExpense(exp)}
      />

      <SubmissionSuccessModal
        submission={session?.submission}
        isOpen={isSuccessOpen}
        onClose={() => setIsSuccessOpen(false)}
        onReset={handleReset}
      />
    </div>
  );
}
