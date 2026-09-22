import React, { useState } from 'react';
import {
  FileText,
  Trash2,
  CheckCircle2,
  Clock,
  AlertCircle,
  Eye,
  Layers,
  X
} from 'lucide-react';
import api from '../services/api';

export default function DocumentList({
  documents = [],
  onDeleteDocument,
  isLoading
}) {
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docChunks, setDocChunks] = useState([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  const viewDocumentChunks = async (doc) => {
    setSelectedDoc(doc);
    setLoadingChunks(true);
    try {
      const data = await api.getDocument(doc.id);
      setDocChunks(data.chunks || []);
    } catch (err) {
      console.error("Failed to load chunks:", err);
      setDocChunks([]);
    } finally {
      setLoadingChunks(false);
    }
  };

  const getFormatBadge = (type) => {
    const t = type.toLowerCase();
    if (t === 'pdf') {
      return <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/20 text-[10px] font-mono uppercase font-semibold">PDF</span>;
    } else if (t === 'docx') {
      return <span className="px-2 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/20 text-[10px] font-mono uppercase font-semibold">DOCX</span>;
    }
    return <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20 text-[10px] font-mono uppercase font-semibold">TXT</span>;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'indexed':
        return (
          <span className="flex items-center space-x-1 text-emerald-400 text-xs">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Indexed</span>
          </span>
        );
      case 'processing':
        return (
          <span className="flex items-center space-x-1 text-teal-400 text-xs animate-pulse">
            <Clock className="w-3.5 h-3.5" />
            <span>Processing</span>
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center space-x-1 text-red-400 text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 text-slate-400 text-xs">
            <Clock className="w-3.5 h-3.5" />
            <span>{status}</span>
          </span>
        );
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
          <span>Active Corpus</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
            {documents.length}
          </span>
        </h3>
      </div>

      {documents.length === 0 ? (
        <div className="p-8 rounded-2xl bg-slate-900/30 border border-slate-800 text-center">
          <FileText className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-xs font-medium text-slate-300">No documents indexed yet</p>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Upload PDF, DOCX, or TXT documents above to begin retrieval.
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/50">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-slate-400 text-[11px] uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Document</th>
                  <th className="py-3 px-3">Type</th>
                  <th className="py-3 px-3">Size</th>
                  <th className="py-3 px-3">Chunks</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-850/50 transition">
                    <td className="py-3 px-4 font-medium text-slate-100 flex items-center space-x-2.5 truncate max-w-xs">
                      <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span className="truncate">{doc.filename}</span>
                    </td>
                    <td className="py-3 px-3">{getFormatBadge(doc.file_type)}</td>
                    <td className="py-3 px-3 font-mono text-slate-400">{formatBytes(doc.file_size)}</td>
                    <td className="py-3 px-3 font-mono font-semibold text-emerald-400">
                      {doc.chunk_count}
                    </td>
                    <td className="py-3 px-3">{getStatusBadge(doc.status)}</td>
                    <td className="py-3 px-4 text-right space-x-1 whitespace-nowrap">
                      <button
                        onClick={() => viewDocumentChunks(doc)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
                        title="Inspect Chunks"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => onDeleteDocument?.(doc.id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition"
                        title="Delete Document"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Chunk Inspection Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2 truncate">
                <Layers className="w-4 h-4 text-emerald-400" />
                <h4 className="text-sm font-semibold text-white truncate">
                  Chunks for: {selectedDoc.filename}
                </h4>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {loadingChunks ? (
                <div className="py-8 text-center text-xs text-slate-400">
                  Loading chunk data...
                </div>
              ) : docChunks.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-400">
                  No chunk details available.
                </div>
              ) : (
                docChunks.map((chunk, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                      <span className="text-emerald-400 font-semibold">Chunk #{chunk.chunk_index}</span>
                      {chunk.page_number && (
                        <span className="bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                          Page {chunk.page_number}
                        </span>
                      )}
                    </div>
                    <p className="text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                      {chunk.text_preview}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
