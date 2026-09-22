import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, ExternalLink, Percent } from 'lucide-react';

export default function SourceCitation({ sources = [] }) {
  const [expandedIndex, setExpandedIndex] = useState(null);

  if (!sources || sources.length === 0) return null;

  const toggleExpand = (idx) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div className="mt-4 pt-3 border-t border-slate-800/80">
      <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 mb-2.5">
        <FileText className="w-3.5 h-3.5 text-emerald-400" />
        <span>Grounded Sources ({sources.length})</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {sources.map((src, idx) => {
          const isExpanded = expandedIndex === idx;
          const scorePercent = Math.round((src.score || 0) * 100);

          return (
            <div
              key={idx}
              className={`text-xs rounded-lg border transition-all ${
                isExpanded
                  ? 'bg-slate-800/90 border-emerald-500/40 shadow-sm'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div
                onClick={() => toggleExpand(idx)}
                className="p-2.5 flex items-center justify-between cursor-pointer select-none"
              >
                <div className="flex items-center space-x-2 truncate">
                  <span className="w-5 h-5 rounded bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-mono text-[10px] shrink-0 font-bold">
                    {idx + 1}
                  </span>
                  <div className="truncate text-left">
                    <p className="font-medium text-slate-200 truncate">
                      {src.document}
                    </p>
                    <div className="flex items-center space-x-2 text-[10px] text-slate-400">
                      {src.page ? (
                        <span className="bg-slate-800 px-1 rounded text-slate-300">
                          Page {src.page}
                        </span>
                      ) : (
                        <span className="text-slate-500">Document</span>
                      )}
                      <span>•</span>
                      <span className="text-emerald-400 font-mono font-medium">
                        {scorePercent}% match
                      </span>
                    </div>
                  </div>
                </div>

                <button className="text-slate-400 hover:text-white p-1">
                  {isExpanded ? (
                    <ChevronUp className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>

              {/* Expandable Preview */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-1 border-t border-slate-800/60 text-slate-300">
                  <div className="flex items-center justify-between text-[10px] text-slate-500 pb-1.5 font-mono">
                    <span>CHUNK ID: {src.chunk_id || 'N/A'}</span>
                    <span>SCORE: {src.score}</span>
                  </div>
                  <p className="text-[11px] leading-relaxed bg-slate-950/60 p-2 rounded border border-slate-800 font-sans text-slate-300 whitespace-pre-wrap">
                    {src.full_text || src.preview}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
