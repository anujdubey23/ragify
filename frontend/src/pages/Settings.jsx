import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, RefreshCw, Sliders, Cpu, Database, Check } from 'lucide-react';
import api from '../services/api';
import ErrorMessage from '../components/ErrorMessage';

export default function Settings() {
  const [config, setConfig] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      const data = await api.getSettings();
      setConfig(data);
    } catch (err) {
      console.error('Failed to load settings:', err);
      setErrorMessage('Could not retrieve settings.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (key, value) => {
    setConfig((prev) => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setErrorMessage(null);
    setSavedSuccess(false);

    try {
      await api.updateSettings(config);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to update settings:', err);
      setErrorMessage('Failed to save settings.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading || !config) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-xs text-slate-500">
        Loading RAG configuration...
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-10 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2.5">
            <SettingsIcon className="w-6 h-6 text-emerald-400" />
            <span>RAG Hyperparameters & Tuning</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Tune chunking size, retrieval fusion weights, cross-encoder reranking, and generation parameters.
          </p>
        </div>

        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center space-x-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-500/20 active:scale-95 transition"
        >
          {savedSuccess ? (
            <>
              <Check className="w-3.5 h-3.5" />
              <span>Saved!</span>
            </>
          ) : (
            <>
              <Save className="w-3.5 h-3.5" />
              <span>{isSaving ? 'Saving...' : 'Save Settings'}</span>
            </>
          )}
        </button>
      </div>

      {errorMessage && (
        <ErrorMessage message={errorMessage} onDismiss={() => setErrorMessage(null)} />
      )}

      <form onSubmit={handleSave} className="space-y-6 text-xs">
        {/* Retrieval & Hybrid Fusion */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
            <Sliders className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Hybrid Retrieval Weights</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                Semantic Weight (FAISS Dense Search): <span className="text-emerald-400 font-mono font-bold">{config.semantic_weight}</span>
              </label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={config.semantic_weight}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  handleChange('semantic_weight', val);
                  handleChange('bm25_weight', parseFloat((1.0 - val).toFixed(2)));
                }}
                className="w-full accent-emerald-500"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Controls the influence of dense sentence-transformers cosine similarity.
              </p>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                BM25 Weight (Lexical Match): <span className="text-teal-400 font-mono font-bold">{config.bm25_weight}</span>
              </label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={config.bm25_weight}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  handleChange('bm25_weight', val);
                  handleChange('semantic_weight', parseFloat((1.0 - val).toFixed(2)));
                }}
                className="w-full accent-teal-500"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Controls the influence of exact keyword and acronym frequencies.
              </p>
            </div>
          </div>
        </div>

        {/* Chunking & Context Window */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
            <Database className="w-4 h-4 text-teal-400" />
            <h2 className="text-sm font-semibold text-white">Chunking & Vector Limits</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                Chunk Size (characters)
              </label>
              <input
                type="number"
                min="200"
                max="3000"
                step="50"
                value={config.chunk_size}
                onChange={(e) => handleChange('chunk_size', parseInt(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Recommended 800 (~180 tokens) for self-contained paragraphs.
              </p>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                Chunk Overlap (characters)
              </label>
              <input
                type="number"
                min="0"
                max="500"
                step="25"
                value={config.chunk_overlap}
                onChange={(e) => handleChange('chunk_overlap', parseInt(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Preserves context across split boundaries.
              </p>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                Top-K Candidate Chunks (Pre-Rerank)
              </label>
              <input
                type="number"
                min="5"
                max="50"
                value={config.top_k_candidates}
                onChange={(e) => handleChange('top_k_candidates', parseInt(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                Final Top-K Context Chunks (Post-Rerank)
              </label>
              <input
                type="number"
                min="1"
                max="15"
                value={config.top_k}
                onChange={(e) => handleChange('top_k', parseInt(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Reranker & Anti-Hallucination */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Reranker & Confidence Threshold</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <p className="font-medium text-slate-200">Cross-Encoder Reranker</p>
                <p className="text-[11px] text-slate-500">
                  Calculates deep query-chunk cross-attention for higher retrieval precision.
                </p>
              </div>
              <input
                type="checkbox"
                checked={config.reranking_enabled}
                onChange={(e) => handleChange('reranking_enabled', e.target.checked)}
                className="w-5 h-5 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                Confidence Threshold: <span className="text-amber-400 font-mono font-bold">{config.confidence_threshold}</span>
              </label>
              <input
                type="range"
                min="0.1"
                max="0.8"
                step="0.05"
                value={config.confidence_threshold}
                onChange={(e) => handleChange('confidence_threshold', parseFloat(e.target.value))}
                className="w-full accent-amber-500"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                If max retrieval score is below this threshold, the model answers "I couldn't find enough relevant information" to reject hallucinations.
              </p>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
