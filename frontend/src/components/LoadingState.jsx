import React from 'react';
import { Loader2, Sparkles } from 'lucide-react';

export default function LoadingState({ message = "Searching and generating grounded answer..." }) {
  return (
    <div className="flex items-start space-x-3 p-4 rounded-xl bg-slate-900/40 border border-slate-800/80 animate-pulse my-3">
      <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
        <Sparkles className="w-4 h-4 animate-spin" />
      </div>
      <div className="space-y-2 flex-1">
        <div className="flex items-center space-x-2 text-xs font-medium text-emerald-400">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span>{message}</span>
        </div>
        <div className="h-3.5 bg-slate-800 rounded w-5/6"></div>
        <div className="h-3.5 bg-slate-800 rounded w-3/4"></div>
      </div>
    </div>
  );
}
