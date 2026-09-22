import React from 'react';
import { AlertCircle, X } from 'lucide-react';

export default function ErrorMessage({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-red-950/40 border border-red-800/60 text-red-300 text-xs my-2">
      <div className="flex items-center space-x-2">
        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
        <span>{message}</span>
      </div>
      {onDismiss && (
        <button onClick={onDismiss} className="text-red-400 hover:text-red-200 p-1">
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}
