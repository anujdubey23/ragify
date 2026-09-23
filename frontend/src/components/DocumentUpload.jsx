import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle, CheckCircle2, Loader2, X } from 'lucide-react';
import api from '../services/api';

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20 MB
const ALLOWED_TYPES = ['.pdf', '.docx', '.txt'];

export default function DocumentUpload({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadQueue, setUploadQueue] = useState([]);
  const [errorMessage, setErrorMessage] = useState(null);
  const fileInputRef = useRef(null);

  const handleFiles = async (files) => {
    setErrorMessage(null);
    const validFiles = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = '.' + file.name.split('.').pop().toLowerCase();

      if (!ALLOWED_TYPES.includes(ext)) {
        setErrorMessage(`File "${file.name}" has unsupported format. Only PDF, DOCX, and TXT are accepted.`);
        return;
      }

      if (file.size > MAX_FILE_SIZE) {
        setErrorMessage(`File "${file.name}" exceeds maximum allowed size of 20MB.`);
        return;
      }

      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    for (const file of validFiles) {
      const queueItem = {
        name: file.name,
        size: (file.size / 1024).toFixed(1) + ' KB',
        progress: 0,
        status: 'uploading' // uploading, processing, indexed, failed
      };

      setUploadQueue((prev) => [queueItem, ...prev]);

      try {
        const res = await api.uploadDocument(file, (progress) => {
          setUploadQueue((prev) =>
            prev.map((item) =>
              item.name === file.name ? { ...item, progress: Math.min(progress, 95), status: 'uploading' } : item
            )
          );
        });

        // Upload succeeded, document is being indexed in background
        setUploadQueue((prev) =>
          prev.map((item) =>
            item.name === file.name ? { ...item, status: res.document?.status === 'indexed' ? 'indexed' : 'processing', progress: 100 } : item
          )
        );

        onUploadSuccess?.();
      } catch (err) {
        const errorDetail = err.response?.data?.detail || err.message || 'Upload failed.';
        setUploadQueue((prev) =>
          prev.map((item) =>
            item.name === file.name ? { ...item, status: 'failed', error: errorDetail } : item
          )
        );
      }
    }
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drag and Drop Zone */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-emerald-500 bg-emerald-500/10 scale-[1.01]'
            : 'border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/70'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          multiple
          accept=".pdf,.docx,.txt"
          className="hidden"
        />

        <div className="w-12 h-12 rounded-xl bg-slate-800/80 text-emerald-400 flex items-center justify-center mx-auto mb-3 shadow-inner">
          <UploadCloud className="w-6 h-6" />
        </div>

        <h3 className="text-sm font-semibold text-white mb-1">
          Drop your PDF, DOCX, or TXT documents here
        </h3>
        <p className="text-xs text-slate-400 mb-3">
          or <span className="text-emerald-400 font-medium">browse from your computer</span> (Up to 20MB per file)
        </p>

        <div className="flex items-center justify-center space-x-2 text-[11px] text-slate-500 font-mono">
          <span className="bg-slate-800 px-2 py-0.5 rounded">PDF</span>
          <span className="bg-slate-800 px-2 py-0.5 rounded">DOCX</span>
          <span className="bg-slate-800 px-2 py-0.5 rounded">TXT</span>
        </div>
      </div>

      {/* Validation Error */}
      {errorMessage && (
        <div className="p-3 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="p-1 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Upload Queue Progress */}
      {uploadQueue.length > 0 && (
        <div className="space-y-2">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Upload Progress
          </p>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {uploadQueue.map((item, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 truncate">
                    <File className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span className="font-medium text-slate-200 truncate">{item.name}</span>
                    <span className="text-[10px] text-slate-500 font-mono">({item.size})</span>
                  </div>
                  <div className="flex items-center space-x-1.5 shrink-0">
                    {item.status === 'uploading' && (
                      <span className="text-[10px] text-emerald-400 font-mono">{item.progress}%</span>
                    )}
                    {item.status === 'processing' && (
                      <span className="flex items-center space-x-1 text-[10px] text-teal-400 font-mono">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Chunking & Embedding...</span>
                      </span>
                    )}
                    {item.status === 'indexed' && (
                      <span className="flex items-center space-x-1 text-[10px] text-emerald-400 font-mono">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Indexed</span>
                      </span>
                    )}
                    {item.status === 'failed' && (
                      <span className="flex items-center space-x-1 text-[10px] text-red-400 font-mono">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>Failed</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                {item.status === 'uploading' && (
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full transition-all duration-300 rounded-full"
                      style={{ width: `${item.progress}%` }}
                    ></div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
