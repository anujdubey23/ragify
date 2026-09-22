import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Files,
  BarChart3,
  CheckCircle2,
  Settings,
  Plus,
  Trash2,
  Layers,
  Sparkles,
  Database
} from 'lucide-react';

export default function Sidebar({
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  stats
}) {
  const navigate = useNavigate();

  const navItems = [
    { to: '/', label: 'Chat Area', icon: MessageSquare },
    { to: '/documents', label: 'Documents', icon: Files, badge: stats?.indexed_documents },
    { to: '/dashboard', label: 'Analytics', icon: BarChart3 },
    { to: '/evaluation', label: 'RAG Evaluation', icon: CheckCircle2 },
    { to: '/settings', label: 'RAG Tuning', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-base tracking-tight text-white">RAGify</span>
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                PROD
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Intelligent Doc AI</p>
          </div>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-500/15 text-emerald-400 font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center space-x-2.5">
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300 font-mono">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Action: New Conversation */}
      <div className="px-3 pt-2">
        <button
          onClick={() => {
            navigate('/');
            onNewChat?.();
          }}
          className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700/60 rounded-lg text-xs font-medium transition shadow-sm hover:border-slate-600"
        >
          <Plus className="w-3.5 h-3.5 text-emerald-400" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Recent Conversations List */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
        <div className="px-2 pb-1.5 flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            History
          </span>
          <span className="text-[10px] text-slate-500 font-mono">{conversations.length}</span>
        </div>

        {conversations.length === 0 ? (
          <div className="px-2 py-4 text-center text-xs text-slate-500 italic">
            No past conversations
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => {
                navigate('/');
                onSelectConversation?.(conv.id);
              }}
              className={`group flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition ${
                activeConversationId === conv.id
                  ? 'bg-slate-800 text-white font-medium'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <div className="flex items-center space-x-2 truncate">
                <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-500 group-hover:text-emerald-400" />
                <span className="truncate">{conv.title || 'Untitled Chat'}</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteConversation?.(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-slate-500 transition"
                title="Delete Chat"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Footer System Status */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/60">
        <div className="bg-slate-950/80 rounded-lg p-2.5 border border-slate-800/80 space-y-1.5">
          <div className="flex items-center justify-between text-[11px]">
            <div className="flex items-center space-x-1.5 text-slate-400">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>FAISS Store</span>
            </div>
            <span className="font-mono text-xs font-semibold text-emerald-400">
              {stats?.active_vectors ?? 0} vecs
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <div className="flex items-center space-x-1.5 text-slate-400">
              <Layers className="w-3.5 h-3.5 text-teal-400" />
              <span>Chunks</span>
            </div>
            <span className="font-mono text-xs text-slate-300">
              {stats?.total_chunks ?? 0}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
