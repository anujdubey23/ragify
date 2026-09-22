import React, { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import LoadingState from './LoadingState';
import { Sparkles, FileText, Search, ShieldCheck, ArrowRight } from 'lucide-react';

export default function ChatWindow({
  messages = [],
  isLoading,
  onSelectPrompt,
  onRegenerate,
  hasDocuments = false
}) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const samplePrompts = [
    "What is the main architecture proposed across the documents?",
    "Summarize the key methodology and performance results.",
    "Explain how the parameters are optimized and trained.",
    "What are the limitations mentioned in the research paper?"
  ];

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        <div className="max-w-3xl mx-auto px-4 py-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto mb-4 text-emerald-400 shadow-xl shadow-emerald-500/10">
            <Sparkles className="w-7 h-7" />
          </div>

          <h2 className="text-xl font-bold text-white mb-2 tracking-tight">
            RAGify Document Intelligence
          </h2>
          <p className="text-slate-400 text-xs max-w-md mx-auto mb-8 leading-relaxed">
            Multi-document retrieval with dense semantic vectors, BM25 keyword matching,
            cross-encoder reranking, and anti-hallucination verification.
          </p>

          {/* Architecture Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8 text-left">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center space-x-2 text-emerald-400 text-xs font-semibold mb-1">
                <Search className="w-4 h-4" />
                <span>Hybrid Search</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Combines FAISS dense cosine similarity (0.7) with BM25 keyword precision (0.3).
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center space-x-2 text-teal-400 text-xs font-semibold mb-1">
                <ShieldCheck className="w-4 h-4" />
                <span>Cross-Reranked</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Evaluates deep cross-attention interactions across top candidates to isolate the best 5 chunks.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center space-x-2 text-indigo-400 text-xs font-semibold mb-1">
                <FileText className="w-4 h-4" />
                <span>Page Citations</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Every generated claim is cited with source document name and exact page numbers.
              </p>
            </div>
          </div>

          {/* Prompt Suggestions */}
          {hasDocuments && (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
                Suggested Prompts
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {samplePrompts.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSelectPrompt?.(p)}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-900/40 hover:bg-slate-800/80 border border-slate-800/80 hover:border-emerald-500/40 text-left text-xs text-slate-300 transition group"
                  >
                    <span className="truncate mr-2">{p}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 shrink-0 transition" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="divide-y divide-slate-900">
          {messages.map((msg, idx) => (
            <ChatMessage
              key={msg.id || idx}
              message={msg}
              onRegenerate={
                idx === messages.length - 1 && msg.role === 'assistant'
                  ? onRegenerate
                  : null
              }
            />
          ))}

          {isLoading && (
            <div className="max-w-4xl mx-auto px-4 md:px-8 py-3">
              <LoadingState />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
