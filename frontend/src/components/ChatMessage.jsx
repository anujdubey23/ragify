import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  User,
  Bot,
  Copy,
  Check,
  RotateCcw,
  Sparkles,
  Clock,
  AlertTriangle
} from 'lucide-react';
import SourceCitation from './SourceCitation';

export default function ChatMessage({ message, onRegenerate }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const metadata = message.metadata || {};
  const sources = message.sources || [];
  const isInsufficient = message.insufficient_context;

  return (
    <div
      className={`py-5 px-4 md:px-8 border-b transition-colors ${
        isUser
          ? 'bg-slate-950/40 border-slate-900'
          : 'bg-slate-900/30 border-slate-850/60'
      }`}
    >
      <div className="max-w-4xl mx-auto flex items-start space-x-3.5">
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
            isUser
              ? 'bg-indigo-600/30 text-indigo-400 border border-indigo-500/30'
              : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4.5 h-4.5" />}
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-hidden">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold tracking-wide text-slate-300">
              {isUser ? 'You' : 'RAGify Engine'}
            </span>

            {!isUser && (
              <div className="flex items-center space-x-2">
                {metadata.total_latency_ms && (
                  <span className="flex items-center space-x-1 text-[10px] text-slate-500 font-mono">
                    <Clock className="w-3 h-3 text-slate-600" />
                    <span>{metadata.total_latency_ms}ms</span>
                  </span>
                )}
                <button
                  onClick={handleCopy}
                  className="p-1 text-slate-500 hover:text-slate-300 rounded hover:bg-slate-800 transition"
                  title="Copy response"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
                {onRegenerate && (
                  <button
                    onClick={onRegenerate}
                    className="p-1 text-slate-500 hover:text-slate-300 rounded hover:bg-slate-800 transition"
                    title="Regenerate answer"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Insufficient context banner if triggered */}
          {isInsufficient && (
            <div className="mb-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
              <span>
                Relevance confidence was below threshold. Unverified facts were rejected to prevent hallucination.
              </span>
            </div>
          )}

          {/* Render Text or Markdown */}
          {isUser ? (
            <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
              {message.content}
            </p>
          ) : (
            <div className="prose-dark font-sans">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Sources Section */}
          {!isUser && sources.length > 0 && (
            <SourceCitation sources={sources} />
          )}
        </div>
      </div>
    </div>
  );
}
