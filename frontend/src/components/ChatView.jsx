import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Paperclip, 
  Sparkles, 
  CheckCircle, 
  AlertTriangle, 
  AlertCircle, 
  Copy, 
  ArrowRight, 
  HelpCircle,
  FileSpreadsheet,
  CornerDownLeft,
  Bot,
  User,
  ShieldCheck,
  Zap
} from 'lucide-react';

export default function ChatView({
  session,
  onSendMessage,
  onUploadFiles,
  onReviewClaim,
  onSubmitClaim,
  onLoadSample,
  onLoadPerks,
  onOpenPolicy,
  loading
}) {
  const [inputText, setInputText] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [session?.chat_history, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    onSendMessage(inputText);
    setInputText("");
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUploadFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onUploadFiles(e.target.files);
      e.target.value = null;
    }
  };

  const pendingQuestions = session?.pending_questions || [];

  return (
    <div 
      className="bg-slate-900/60 rounded-2xl border border-slate-800 flex flex-col h-full overflow-hidden shadow-xl relative"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drag Overlay */}
      {isDragging && (
        <div className="absolute inset-0 z-40 bg-indigo-950/85 backdrop-blur-sm border-2 border-dashed border-indigo-400 flex flex-col items-center justify-center text-center p-6 animate-in fade-in duration-150">
          <Paperclip className="w-12 h-12 text-indigo-300 animate-bounce mb-3" />
          <h3 className="text-lg font-bold text-white">Drop receipts & invoices here</h3>
          <p className="text-xs text-indigo-200 mt-1">Accepts PNG, JPG, PDF documents</p>
        </div>
      )}

      {/* Chat Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {session?.chat_history?.map((msg, index) => {
          const isUser = msg.role === 'user';

          return (
            <div
              key={msg.id || index}
              className={`flex gap-3 text-sm animate-in fade-in slide-in-from-bottom-2 duration-200 ${
                isUser ? 'justify-end' : 'justify-start'
              }`}
            >
              {/* Assistant Avatar */}
              {!isUser && (
                <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              {/* Message Content Bubble */}
              <div
                className={`max-w-[85%] rounded-2xl p-4 ${
                  isUser
                    ? 'bg-indigo-600 text-white rounded-tr-xs shadow-md shadow-indigo-600/20'
                    : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-xs shadow-md'
                }`}
              >
                {/* Text Formatting with Markdown-like lists */}
                <div className="whitespace-pre-wrap leading-relaxed text-xs md:text-sm">
                  {msg.content}
                </div>

                {/* Summary Card Widget if present */}
                {msg.summary_card && (
                  <div className="mt-3 p-3 rounded-xl bg-slate-950/70 border border-slate-800 grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase">Total Amount</div>
                      <div className="text-sm font-bold font-mono text-white mt-0.5">
                        ₹{Math.round(msg.summary_card.total).toLocaleString()}
                      </div>
                    </div>
                    <div className="p-2 rounded-lg bg-emerald-950/30 border border-emerald-800/40">
                      <div className="text-[10px] text-emerald-400 uppercase">Eligible</div>
                      <div className="text-sm font-bold font-mono text-emerald-300 mt-0.5">
                        ₹{Math.round(msg.summary_card.eligible).toLocaleString()}
                      </div>
                    </div>
                    <div className="p-2 rounded-lg bg-rose-950/30 border border-rose-800/40 col-span-2 sm:col-span-1">
                      <div className="text-[10px] text-rose-400 uppercase">Exceptions</div>
                      <div className="text-sm font-bold font-mono text-rose-300 mt-0.5">
                        ₹{Math.round(msg.summary_card.exceptions).toLocaleString()}
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Buttons Attached to Message */}
                {msg.actions && msg.actions.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-slate-800/60 flex flex-wrap gap-2">
                    {msg.actions.map((act, aIdx) => {
                      if (act.type === 'quick_answer') {
                        return (
                          <button
                            key={aIdx}
                            onClick={() => onSendMessage(act.payload)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/30 transition cursor-pointer"
                          >
                            <Zap className="w-3.5 h-3.5 text-amber-300" />
                            <span>{act.label}</span>
                          </button>
                        );
                      }
                      if (act.type === 'review_claim') {
                        return (
                          <button
                            key={aIdx}
                            onClick={onReviewClaim}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition cursor-pointer"
                          >
                            <FileSpreadsheet className="w-3.5 h-3.5 text-indigo-400" />
                            <span>{act.label}</span>
                          </button>
                        );
                      }
                      if (act.type === 'submit_claim') {
                        const isEligible = (session?.summary?.eligible_amount || 0) > 0;
                        const isSubmitted = session?.status === 'submitted';
                        return (
                          <button
                            key={aIdx}
                            onClick={onSubmitClaim}
                            disabled={!isEligible || isSubmitted}
                            title={!isEligible ? "Cannot submit claim with ₹0 eligible reimbursement" : "Submit Claim"}
                            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold ${
                              isEligible && !isSubmitted
                                ? 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white shadow-md shadow-emerald-500/20 cursor-pointer'
                                : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed opacity-50'
                            } transition`}
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>{isSubmitted ? 'Claim Submitted' : isEligible ? act.label : 'Eligible ₹0 (Cannot Submit)'}</span>
                          </button>
                        );
                      }
                      if (act.type === 'load_sample') {
                        return (
                          <button
                            key={aIdx}
                            onClick={onLoadSample}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition cursor-pointer"
                          >
                            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                            <span>{act.label}</span>
                          </button>
                        );
                      }
                      if (act.type === 'load_perks') {
                        return (
                          <button
                            key={aIdx}
                            onClick={onLoadPerks}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition cursor-pointer"
                          >
                            <span>🎧🚗</span>
                            <span>{act.label}</span>
                          </button>
                        );
                      }
                      return null;
                    })}
                  </div>
                )}

                <div className="mt-1 text-[10px] text-slate-500 text-right">
                  {msg.timestamp}
                </div>
              </div>

              {/* User Avatar */}
              {isUser && (
                <div className="w-8 h-8 rounded-xl bg-slate-800 text-slate-300 border border-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {/* Loading / Typing indicator */}
        {loading && (
          <div className="flex gap-3 text-sm animate-in fade-in duration-200">
            <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-xs p-3.5 text-slate-300 flex items-center gap-2 text-xs">
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
              <span>Analyzing receipts and checking corporate compliance...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Clarification Suggestion Chips Bar */}
      <div className="px-4 py-2 bg-slate-950/80 border-t border-slate-800/80 flex items-center gap-2 overflow-x-auto text-xs">
        {pendingQuestions.length > 0 && (
          <>
            <span className="text-[11px] text-amber-400 font-semibold uppercase tracking-wider shrink-0 flex items-center gap-1">
              <HelpCircle className="w-3 h-3" /> Quick Fill:
            </span>
            <button
              onClick={() => onSendMessage("1. Client meeting in Bangalore\n2. 24 September")}
              className="px-2.5 py-1 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 text-xs shrink-0 transition cursor-pointer font-medium"
            >
              ⚡ 1. Client meeting in Bangalore, 2. 24 September
            </button>
            <button
              onClick={() => setInputText("1. Client meeting in Bangalore\n2. 24 September")}
              className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs shrink-0 transition cursor-pointer"
            >
              ✏️ Copy to Input
            </button>
          </>
        )}
        <button
          onClick={onOpenPolicy}
          className="px-2.5 py-1 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 text-xs shrink-0 transition cursor-pointer flex items-center gap-1 font-semibold ml-auto"
          title="Open corporate reimbursement policy guide"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Policy Rules Guide</span>
        </button>
      </div>

      {/* Input Form Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/95">
        <form onSubmit={handleSubmit} className="flex items-center gap-2">
          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            multiple
            accept="image/*,application/pdf"
            className="hidden"
          />

          {/* Attachment Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            className="p-2.5 text-slate-400 hover:text-indigo-400 hover:bg-slate-800 rounded-xl border border-slate-800 transition cursor-pointer"
            title="Attach receipt photos or PDFs"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          {/* Chat Input Field */}
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              pendingQuestions.length > 0
                ? "Answer questions (e.g. '1. Client meeting in Bangalore, 2. 24 September')..."
                : "Type a message or drag & drop bills here..."
            }
            disabled={loading}
            className="flex-1 bg-slate-950/80 border border-slate-800 focus:border-indigo-500 rounded-xl px-4 py-2.5 text-xs md:text-sm text-white placeholder-slate-500 focus:outline-none transition"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || loading}
            className="p-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl transition shadow-md shadow-indigo-600/20 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        <div className="text-[10px] text-slate-500 text-center mt-2 flex items-center justify-center gap-2">
          <span>Drop bills anytime</span>
          <span>•</span>
          <span>Auto duplicate detection</span>
          <span>•</span>
          <span>Instant policy audit</span>
        </div>
      </div>
    </div>
  );
}
