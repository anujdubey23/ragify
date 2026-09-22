import React, { useEffect, useState } from 'react';
import {
  FileText,
  Layers,
  MessageSquare,
  Search,
  Database,
  ShieldCheck,
  Zap,
  Cpu,
  BarChart3
} from 'lucide-react';
import api from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await api.getStats();
      setStats(data);
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Indexed Documents',
      value: stats?.indexed_documents ?? 0,
      subtext: `Total uploaded: ${stats?.total_documents ?? 0}`,
      icon: FileText,
      color: 'from-emerald-500/20 to-teal-500/10',
      iconColor: 'text-emerald-400',
      borderColor: 'border-emerald-500/30'
    },
    {
      title: 'Vector Embeddings',
      value: stats?.active_vectors ?? 0,
      subtext: `${stats?.embedding_dimension ?? 384}-dim dense representations`,
      icon: Database,
      color: 'from-teal-500/20 to-cyan-500/10',
      iconColor: 'text-teal-400',
      borderColor: 'border-teal-500/30'
    },
    {
      title: 'Total Text Chunks',
      value: stats?.total_chunks ?? 0,
      subtext: `BM25 index count: ${stats?.bm25_indexed_chunks ?? 0}`,
      icon: Layers,
      color: 'from-cyan-500/20 to-blue-500/10',
      iconColor: 'text-cyan-400',
      borderColor: 'border-cyan-500/30'
    },
    {
      title: 'Queries Answered',
      value: stats?.total_questions ?? 0,
      subtext: `Across ${stats?.total_conversations ?? 0} conversations`,
      icon: MessageSquare,
      color: 'from-indigo-500/20 to-violet-500/10',
      iconColor: 'text-indigo-400',
      borderColor: 'border-indigo-500/30'
    }
  ];

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">System Analytics & Pipeline Status</h1>
        <p className="text-xs text-slate-400 mt-1">
          Real-time metrics for FAISS vector storage, BM25 indexing, and retrieval performance.
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className={`p-5 rounded-2xl bg-gradient-to-br ${card.color} border ${card.borderColor} bg-slate-900/60 shadow-lg relative overflow-hidden`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-300">{card.title}</span>
                <div className={`p-2 rounded-xl bg-slate-900/80 border border-slate-800 ${card.iconColor}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="font-mono text-3xl font-bold text-white tracking-tight mb-1">
                {loading ? '...' : card.value}
              </div>
              <p className="text-[11px] text-slate-400">{card.subtext}</p>
            </div>
          );
        })}
      </div>

      {/* Architecture Pipeline Flow Summary */}
      <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Active RAG Pipeline Architecture</h2>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            Operational
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
            <div className="text-[10px] uppercase font-semibold text-slate-500">Stage 1</div>
            <div className="font-semibold text-slate-200">Ingest & Chunk</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              PyMuPDF / python-docx with recursive 800-char splitting and 150-char overlap.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
            <div className="text-[10px] uppercase font-semibold text-slate-500">Stage 2</div>
            <div className="font-semibold text-slate-200">Dense Embed</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              sentence-transformers/all-MiniLM-L6-v2 mapped into FAISS IndexFlatIP.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
            <div className="text-[10px] uppercase font-semibold text-slate-500">Stage 3</div>
            <div className="font-semibold text-slate-200">Hybrid Match</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Fused ranking: 0.7 Semantic Cosine + 0.3 BM25 lexical token frequencies.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
            <div className="text-[10px] uppercase font-semibold text-slate-500">Stage 4</div>
            <div className="font-semibold text-slate-200">Cross-Rerank</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Top 15 candidates evaluated via CrossEncoder attention into final top-5.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1.5">
            <div className="text-[10px] uppercase font-semibold text-slate-500">Stage 5</div>
            <div className="font-semibold text-slate-200">Anti-Hallucination</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Strict document grounding with automated fallback and page citation links.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
