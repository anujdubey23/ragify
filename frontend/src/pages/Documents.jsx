import React, { useState, useEffect } from 'react';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';
import ErrorMessage from '../components/ErrorMessage';
import api from '../services/api';
import { Files, RefreshCw } from 'lucide-react';

export default function Documents({ onUpdateStats }) {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    fetchDocuments();
    // Poll every 3 seconds if any document is still processing
    const interval = setInterval(() => {
      fetchDocuments(false);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchDocuments = async (showLoading = true) => {
    try {
      if (showLoading) setIsLoading(true);
      const data = await api.getDocuments();
      setDocuments(data);
      onUpdateStats?.();
    } catch (err) {
      console.error('Failed to load documents:', err);
      if (showLoading) setErrorMessage('Could not retrieve uploaded documents list.');
    } finally {
      if (showLoading) setIsLoading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document and its vector embeddings?')) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      onUpdateStats?.();
    } catch (err) {
      console.error('Failed to delete document:', err);
      setErrorMessage('Could not delete document.');
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-10 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2.5">
            <Files className="w-6 h-6 text-emerald-400" />
            <span>Document Corpus Hub</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Upload, chunk, embed, and manage PDF, DOCX, and TXT sources.
          </p>
        </div>

        <button
          onClick={fetchDocuments}
          className="flex items-center space-x-2 px-3 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-xl text-xs text-slate-300 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {errorMessage && (
        <ErrorMessage message={errorMessage} onDismiss={() => setErrorMessage(null)} />
      )}

      {/* Upload Zone */}
      <section className="space-y-3">
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Upload & Index New Files
        </h2>
        <DocumentUpload onUploadSuccess={fetchDocuments} />
      </section>

      {/* Document List */}
      <section className="space-y-3 pt-4">
        <DocumentList
          documents={documents}
          onDeleteDocument={handleDelete}
          isLoading={isLoading}
        />
      </section>
    </div>
  );
}
