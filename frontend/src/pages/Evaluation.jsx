import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  Play,
  RotateCcw,
  Clock,
  Target,
  ShieldCheck,
  FileCheck,
  Zap,
  ChevronDown,
  ChevronUp,
  HelpCircle
} from 'lucide-react';
import api from '../services/api';
import ErrorMessage from '../components/ErrorMessage';

export default function Evaluation() {
  const [isRunning, setIsRunning] = useState(false);
  const [currentRun, setCurrentRun] = useState(null);
  const [history, setHistory] = useState([]);
  const [expandedQ, setExpandedQ] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await api.getEvaluationHistory();
      setHistory(data);
      if (data.length > 0 && !currentRun) {
        setCurrentRun(data[0]);
      }
    } catch (err) {
      console.error('Failed to load evaluation history:', err);
    }
  };

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    setErrorMessage(null);
    try {
      const result = await api.runEvaluation();
      setCurrentRun(result);
      await loadHistory();
    } catch (err) {
      console.error('Evaluation failed:', err);
      const detail = err.response?.data?.detail || err.message || 'Evaluation run failed.';
      setErrorMessage(detail);
    } finally {
      setIsRunning(false);
    }
  };

  const metricCards = currentRun
    ? [
        {
          title: 'Precision@K',
          val: `${Math.round((currentRun.avg_precision_at_k ?? currentRun.precision_at_k ?? 0) * 100)}%`,
          desc: 'Retrieved sources matching expected',
          icon: Target,
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10'
        },
        {
          title: 'Recall@K',
          val: `${Math.round((currentRun.avg_recall_at_k ?? currentRun.recall_at_k ?? 0) * 100)}%`,
          desc: 'Expected sources captured in top-K',
          icon: FileCheck,
          color: 'text-teal-400',
          bg: 'bg-teal-500/10'
        },
        {
          title: 'Context Relevance',
          val: `${Math.round((currentRun.avg_context_relevance ?? currentRun.context_relevance ?? 0) * 100)}%`,
          desc: 'Overlap between query and chunks',
          icon: Zap,
          color: 'text-cyan-400',
          bg: 'bg-cyan-500/10'
        },
        {
          title: 'Answer Faithfulness',
          val: `${Math.round((currentRun.avg_faithfulness ?? currentRun.faithfulness ?? 0) * 100)}%`,
          desc: 'Claims verified by retrieved facts',
          icon: ShieldCheck,
          color: 'text-indigo-400',
          bg: 'bg-indigo-500/10'
        },
        {
          title: 'Answer Relevance',
          val: `${Math.round((currentRun.avg_answer_relevance ?? currentRun.answer_relevance ?? 0) * 100)}%`,
          desc: 'Semantic agreement with ground truth',
          icon: CheckCircle2,
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10'
        },
        {
          title: 'Avg Latency',
          val: `${currentRun.avg_latency_ms ?? 0}ms`,
          desc: 'End-to-end RAG response time',
          icon: Clock,
          color: 'text-amber-400',
          bg: 'bg-amber-500/10'
        }
      ]
    : [];

  const questionsList = currentRun?.questions_evaluated || currentRun?.details || [];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-10 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2.5">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            <span>RAG Evaluation & Quality Metrics</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Empirical benchmark assessing Precision, Recall, Groundedness, and Latency.
          </p>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={isRunning}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-xs shadow-lg transition ${
            isRunning
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-500/20 active:scale-95'
          }`}
        >
          <Play className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Running Benchmark...' : 'Run Benchmark'}</span>
        </button>
      </div>

      {errorMessage && (
        <ErrorMessage message={errorMessage} onDismiss={() => setErrorMessage(null)} />
      )}

      {/* Metrics Grid */}
      {metricCards.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {metricCards.map((m, idx) => {
            const Icon = m.icon;
            return (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-semibold text-slate-400">{m.title}</span>
                  <div className={`p-1.5 rounded-lg ${m.bg} ${m.color}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                </div>
                <div>
                  <div className={`font-mono text-2xl font-bold text-white mb-0.5`}>
                    {m.val}
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">{m.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center">
          <HelpCircle className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-xs font-semibold text-slate-300">No evaluation runs yet</p>
          <p className="text-[11px] text-slate-500 mt-1">
            Click "Run Benchmark" to execute the evaluation dataset against the active RAG pipeline.
          </p>
        </div>
      )}

      {/* Breakdown per Question */}
      {questionsList.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Per-Question Evaluation Breakdown ({questionsList.length})
          </h2>

          <div className="space-y-2">
            {questionsList.map((q, idx) => {
              const isExp = expandedQ === idx;
              return (
                <div
                  key={idx}
                  className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden text-xs"
                >
                  <div
                    onClick={() => setExpandedQ(isExp ? null : idx)}
                    className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-850/50 transition select-none"
                  >
                    <div className="flex items-center space-x-3 truncate">
                      <span className="font-mono text-[10px] text-slate-500 shrink-0 font-bold">
                        #{idx + 1}
                      </span>
                      <span className="font-medium text-slate-200 truncate">{q.question}</span>
                    </div>

                    <div className="flex items-center space-x-4 shrink-0 font-mono text-[11px]">
                      <span className="text-emerald-400">
                        P: {Math.round((q.precision_at_k || 0) * 100)}%
                      </span>
                      <span className="text-teal-400">
                        R: {Math.round((q.recall_at_k || 0) * 100)}%
                      </span>
                      <span className="text-indigo-400">
                        Faith: {Math.round((q.faithfulness || 0) * 100)}%
                      </span>
                      <span className="text-slate-400">{q.latency_ms}ms</span>
                      {isExp ? (
                        <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {isExp && (
                    <div className="p-4 bg-slate-950/70 border-t border-slate-800/80 space-y-3">
                      <div>
                        <span className="text-[10px] font-mono text-slate-500 uppercase">
                          Retrieved Sources:
                        </span>
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {q.retrieved_sources && q.retrieved_sources.length > 0 ? (
                            q.retrieved_sources.map((s, si) => (
                              <span
                                key={si}
                                className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]"
                              >
                                {s}
                              </span>
                            ))
                          ) : (
                            <span className="text-slate-500 text-[10px]">None</span>
                          )}
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] font-mono text-slate-500 uppercase">
                          Generated Answer:
                        </span>
                        <p className="mt-1 text-slate-300 bg-slate-900/90 p-2.5 rounded border border-slate-800 leading-relaxed font-sans">
                          {q.generated_answer}
                        </p>
                      </div>

                      {q.expected_answer && (
                        <div>
                          <span className="text-[10px] font-mono text-slate-500 uppercase">
                            Expected Ground Truth:
                          </span>
                          <p className="mt-1 text-slate-400 italic bg-slate-900/40 p-2 rounded border border-slate-850">
                            {q.expected_answer}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
