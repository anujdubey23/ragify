import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, CornerDownLeft, Paperclip } from 'lucide-react';

export default function ChatInput({
  onSendMessage,
  isLoading,
  disabled,
  documentCount = 0
}) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [query]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim() || isLoading || disabled) return;
    onSendMessage(query.trim());
    setQuery('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4">
      <div className="relative rounded-2xl bg-slate-900/90 border border-slate-700/80 shadow-2xl focus-within:border-emerald-500/60 focus-within:ring-1 focus-within:ring-emerald-500/30 transition-all backdrop-blur-md">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            disabled
              ? "Please upload documents first to start asking questions..."
              : "Ask questions across your documents (Enter to send, Shift+Enter for newline)..."
          }
          disabled={disabled || isLoading}
          rows={1}
          className="w-full bg-transparent px-4 pt-3.5 pb-12 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none font-sans"
        />

        <div className="absolute bottom-2.5 left-3.5 right-3 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-[11px] text-slate-500">
            <span className="flex items-center space-x-1 font-mono">
              <span className={`w-2 h-2 rounded-full ${documentCount > 0 ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
              <span>{documentCount} {documentCount === 1 ? 'doc' : 'docs'} indexed</span>
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleSubmit}
              disabled={!query.trim() || isLoading || disabled}
              className={`p-2 rounded-xl flex items-center justify-center transition-all ${
                query.trim() && !isLoading && !disabled
                  ? 'bg-emerald-500 text-white hover:bg-emerald-600 shadow-md shadow-emerald-500/20 active:scale-95'
                  : 'bg-slate-800 text-slate-600 cursor-not-allowed'
              }`}
              title="Send question"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
