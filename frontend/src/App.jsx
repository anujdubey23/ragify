import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Chat from './pages/Chat';
import Documents from './pages/Documents';
import Dashboard from './pages/Dashboard';
import Evaluation from './pages/Evaluation';
import Settings from './pages/Settings';
import api from './services/api';

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadConversations();
    loadStats();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await api.getConversations();
      setConversations(data);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const loadStats = async () => {
    try {
      const data = await api.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleNewChat = () => {
    setActiveConversationId(null);
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConversationId === id) {
        setActiveConversationId(null);
      }
      loadStats();
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  return (
    <Router>
      <div className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans text-slate-100">
        <Sidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={(id) => setActiveConversationId(id)}
          onNewChat={handleNewChat}
          onDeleteConversation={handleDeleteConversation}
          stats={stats}
        />

        <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950">
          <Routes>
            <Route
              path="/"
              element={
                <Chat
                  activeConversationId={activeConversationId}
                  setActiveConversationId={setActiveConversationId}
                  onRefreshConversations={loadConversations}
                  stats={stats}
                />
              }
            />
            <Route
              path="/documents"
              element={<Documents onUpdateStats={loadStats} />}
            />
            <Route
              path="/dashboard"
              element={<Dashboard />}
            />
            <Route
              path="/evaluation"
              element={<Evaluation />}
            />
            <Route
              path="/settings"
              element={<Settings />}
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
