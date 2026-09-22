import React, { useState, useEffect } from 'react';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import ErrorMessage from '../components/ErrorMessage';
import api from '../services/api';

export default function Chat({
  activeConversationId,
  setActiveConversationId,
  onRefreshConversations,
  stats
}) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    if (activeConversationId) {
      loadConversation(activeConversationId);
    } else {
      setMessages([]);
    }
  }, [activeConversationId]);

  const loadConversation = async (id) => {
    try {
      setIsLoading(true);
      const data = await api.getConversation(id);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load conversation:', err);
      setErrorMessage('Could not load conversation history.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (queryText) => {
    if (!queryText.trim()) return;

    setErrorMessage(null);
    const tempUserMsg = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: queryText,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const response = await api.sendChatMessage({
        question: queryText,
        conversation_id: activeConversationId || undefined
      });

      if (!activeConversationId && response.conversation_id) {
        setActiveConversationId(response.conversation_id);
        onRefreshConversations?.();
      }

      const assistantMsg = {
        id: 'resp-' + Date.now(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        metadata: response.retrieval_metadata || {},
        insufficient_context: response.insufficient_context,
        created_at: new Date().toISOString()
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Chat query error:', err);
      const errDetail = err.response?.data?.detail || err.message || 'Failed to generate response.';
      setErrorMessage(errDetail);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerate = () => {
    if (messages.length < 2) return;
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      handleSendMessage(lastUserMsg.content);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950">
      {/* Top Bar */}
      <header className="h-14 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-900/50 backdrop-blur-sm">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <h1 className="text-xs font-semibold text-white tracking-wide uppercase">
              Grounded Chat Interface
            </h1>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-xs text-slate-400">
            {stats?.indexed_documents ?? 0} documents in context
          </span>
        </div>

        {messages.length > 0 && (
          <button
            onClick={() => {
              setActiveConversationId(null);
              setMessages([]);
            }}
            className="text-xs text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-lg hover:bg-slate-800 transition"
          >
            Clear Window
          </button>
        )}
      </header>

      {/* Error notification */}
      {errorMessage && (
        <div className="px-6 pt-2">
          <ErrorMessage message={errorMessage} onDismiss={() => setErrorMessage(null)} />
        </div>
      )}

      {/* Message History Window */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        onSelectPrompt={handleSendMessage}
        onRegenerate={handleRegenerate}
        hasDocuments={(stats?.indexed_documents ?? 0) > 0}
      />

      {/* Input Area */}
      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        disabled={(stats?.indexed_documents ?? 0) === 0}
        documentCount={stats?.indexed_documents ?? 0}
      />
    </div>
  );
}
