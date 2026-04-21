import { useState, useRef, useEffect, useCallback } from 'react';
import { useTheme } from '../context/ThemeContext';
import { sendMessage, fetchSessions, fetchSessionMessages, deleteSession, uploadFile, fetchNotifications, markNotificationsRead } from '../services/api';
import Sidebar from '../components/Sidebar';
import ChatMessage from '../components/ChatMessage';
import { Send, Loader2, Sparkles, Zap, Calendar, Mail, FileText, StickyNote, Mic, Paperclip, Volume2, VolumeX, Bell, Trash2, Check } from 'lucide-react';

const SUGGESTIONS = [
  { icon: Calendar, text: 'Create a meeting for tomorrow at 3 PM', color: '#818cf8' },
  { icon: Mail, text: 'Check my recent emails', color: '#22d3ee' },
  { icon: FileText, text: 'Summarize my project report', color: '#f472b6' },
  { icon: StickyNote, text: 'Save a note about today\'s ideas', color: '#34d399' },
];

export default function ChatPage() {
  const { isDark } = useTheme();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Advanced Feature Hooks
  const [isListening, setIsListening] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [voiceMode, setVoiceMode] = useState(true);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const fileInputRef = useRef(null);

  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Load sessions on mount
  const loadSessions = useCallback(async () => {
    try {
      const data = await fetchSessions();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const loadNotifications = useCallback(async () => {
    try {
      const data = await fetchNotifications();
      setNotifications(data);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    }
  }, []);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 15000);
    return () => clearInterval(interval);
  }, [loadNotifications]);

  const handleMarkAllRead = async () => {
    try {
      await markNotificationsRead();
      setNotifications([]);
      setShowNotifications(false);
    } catch (err) {
      console.error('Failed to mark notifications read:', err);
    }
  };

  // Load a specific session's messages
  const handleSelectSession = async (sessionId) => {
    if (sessionId === activeSessionId) return;
    setActiveSessionId(sessionId);
    setMessages([]);
    setLoading(true);

    try {
      const msgs = await fetchSessionMessages(sessionId);
      setMessages(msgs.map((m) => ({
        role: m.role,
        content: m.content,
        tool_used: m.tool_used || null,
        tool_result: m.tool_result || null,
      })));
    } catch (err) {
      console.error('Failed to load messages:', err);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  // Delete a session
  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleSend = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    const userMsg = { role: 'user', content: msg };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const data = await sendMessage(msg, history, activeSessionId);

      if (data.session_id) {
        setActiveSessionId(data.session_id);
      }

      const assistantMsg = {
        role: 'assistant',
        content: data.response,
        tool_used: data.tool_used,
        tool_result: data.tool_result,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      
      // Execute TTS
      if (ttsEnabled && data.response && window.speechSynthesis) {
        const utterance = new SpeechSynthesisUtterance(data.response);
        window.speechSynthesis.speak(utterance);
      }

      loadSessions();
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: `Sorry, something went wrong: ${err.response?.data?.detail || err.message}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setUploadLoading(true);
    try {
      await uploadFile(file);
      setMessages((prev) => [...prev, { role: 'assistant', content: `✅ Uploaded ${file.name} successfully.` }]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { role: 'assistant', content: `❌ Failed to upload ${file.name}.` }]);
    } finally {
      setUploadLoading(false);
    }
  };

  const toggleListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support Speech Recognition.");
      return;
    }
    
    if (isListening) {
       setIsListening(false);
       return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput((prev) => prev + (prev.length > 0 ? ' ' : '') + transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setInput('');
    setActiveSessionId(null);
    inputRef.current?.focus();
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        onNewChat={handleNewChat}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        sessionsLoading={sessionsLoading}
      />

      {/* Main chat area */}
      <main className="flex-1 flex flex-col min-w-0">
        
        {/* Top Bar for Advanced Settings */}
        <div 
          className="flex justify-end items-center gap-3 p-3 shrink-0 relative"
          style={{ borderBottom: isDark ? '1px solid rgba(255,255,255,0.06)' : '1px solid rgba(0,0,0,0.06)' }}
        >
          {/* Notifications */}
          <div className="relative">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95"
              style={{
                background: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                color: notifications.length > 0 ? '#f59e0b' : (isDark ? '#94a3b8' : '#64748b'),
              }}
            >
              <Bell size={18} />
              {notifications.length > 0 && (
                <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[10px] flex items-center justify-center rounded-full font-bold">
                  {notifications.length}
                </span>
              )}
            </button>

            {showNotifications && (
              <div 
                className="absolute right-0 mt-2 w-64 rounded-2xl shadow-xl z-50 overflow-hidden animate-slide-in"
                style={{
                  background: isDark ? '#1a1f2e' : '#fff',
                  border: isDark ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.1)',
                }}
              >
                <div className="p-3 border-b flex justify-between items-center"
                     style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
                  <span className="text-xs font-bold uppercase tracking-wider" style={{ color: isDark ? '#64748b' : '#94a3b8' }}>Notifications</span>
                  {notifications.length > 0 && (
                    <button onClick={handleMarkAllRead} className="text-[10px] text-indigo-500 font-bold hover:underline">Clear all</button>
                  )}
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-8 text-center text-xs" style={{ color: isDark ? '#475569' : '#94a3b8' }}>No new notifications</div>
                  ) : (
                    notifications.map(n => (
                      <div key={n.id} className="p-3 border-b text-sm last:border-0"
                           style={{ borderColor: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }}>
                        <p style={{ color: isDark ? '#cbd5e1' : '#334155' }}>{n.message}</p>
                        <span className="text-[10px] mt-1 block" style={{ color: isDark ? '#475569' : '#94a3b8' }}>
                          {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <button 
            onClick={() => setTtsEnabled(!ttsEnabled)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all duration-200"
            style={{
              background: ttsEnabled 
                ? (isDark ? 'rgba(99, 102, 241, 0.15)' : 'rgba(99, 102, 241, 0.1)')
                : (isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'),
              color: ttsEnabled ? '#6366f1' : (isDark ? '#94a3b8' : '#64748b'),
              border: `1px solid ${ttsEnabled ? 'rgba(99, 102, 241, 0.3)' : 'transparent'}`
            }}
          >
            {ttsEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
            Voice: {ttsEnabled ? 'ON' : 'OFF'}
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 && !loading ? (
            <EmptyState isDark={isDark} onSuggestion={handleSend} />
          ) : (
            <div className="py-6 space-y-1">
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} onAction={handleSend} />
              ))}

              {/* Typing indicator */}
              {loading && messages.length > 0 && (
                <div className="flex gap-3 px-4 py-3 max-w-3xl mx-auto animate-fade-in">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                    style={{
                      background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    }}
                  >
                    <Sparkles size={15} className="text-white" />
                  </div>
                  <div className="flex items-center gap-1 pt-2">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="w-2 h-2 rounded-full"
                        style={{
                          background: '#818cf8',
                          animation: `typing-dot 1.4s ease-in-out infinite`,
                          animationDelay: `${i * 0.2}s`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div
          className="shrink-0 p-4"
          style={{
            borderTop: isDark
              ? '1px solid rgba(255,255,255,0.06)'
              : '1px solid rgba(0,0,0,0.06)',
          }}
        >
          <div className="max-w-3xl mx-auto">
            <div
              className="flex items-end gap-2 rounded-2xl p-2 transition-all duration-300"
              style={{
                background: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)',
                border: isDark
                  ? '1px solid rgba(255,255,255,0.08)'
                  : '1px solid rgba(0,0,0,0.08)',
                boxShadow: isDark
                  ? '0 5px 30px rgba(0,0,0,0.3)'
                  : '0 5px 30px rgba(0,0,0,0.06)',
              }}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                onChange={handleFileUpload}
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2.5 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer shrink-0"
                style={{
                  background: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                  color: isDark ? '#94a3b8' : '#64748b',
                }}
                title="Attach a file or image"
              >
                 {uploadLoading ? <Loader2 size={18} className="animate-spin" /> : <Paperclip size={18} />}
              </button>
              
              {/* Voice Output Toggle removed from here, now in Top Bar */}

              <textarea
                id="chat-input"
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask OmniCopilot anything..."
                rows={1}
                disabled={loading}
                className="flex-1 resize-none bg-transparent outline-none text-sm px-3 py-2.5 max-h-32 placeholder-opacity-50"
                style={{
                  color: isDark ? '#e2e8f0' : '#1e293b',
                }}
              />

              <button
                onClick={toggleListening}
                className="p-2.5 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer shrink-0"
                style={{
                  background: isListening ? '#f43f5e' : (isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'),
                  color: isListening ? '#fff' : (isDark ? '#94a3b8' : '#64748b'),
                }}
                title="Voice Dictation"
              >
                  <Mic size={18} className={isListening ? 'animate-pulse' : ''} />
              </button>

              <button
                id="send-btn"
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className="p-2.5 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 disabled:opacity-30 disabled:hover:scale-100 cursor-pointer shrink-0"
                style={{
                  background: input.trim()
                    ? 'linear-gradient(135deg, #6366f1, #4f46e5)'
                    : isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                  color: input.trim() ? '#fff' : isDark ? '#475569' : '#94a3b8',
                }}
              >
                {loading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Send size={18} />
                )}
              </button>
            </div>

            <p
              className="text-center text-[11px] mt-2"
              style={{ color: isDark ? '#374151' : '#cbd5e1' }}
            >
              OmniCopilot may make mistakes. Verify important information.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

function EmptyState({ isDark, onSuggestion }) {
  return (
    <div className="h-full flex flex-col items-center justify-center px-4 animate-fade-in">
      <div
        className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6 animate-pulse-glow"
        style={{
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
        }}
      >
        <Zap size={30} className="text-white" />
      </div>

      <h2
        className="text-xl font-bold mb-2"
        style={{ color: isDark ? '#f1f5f9' : '#1e293b' }}
      >
        How can I help you today?
      </h2>
      <p
        className="text-sm mb-8 max-w-md text-center"
        style={{ color: isDark ? '#64748b' : '#94a3b8' }}
      >
        I can create events, read emails, summarize files, save notes, and answer any question.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            onClick={() => onSuggestion(s.text)}
            className="flex items-center gap-3 text-left px-4 py-3.5 rounded-xl text-sm transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            style={{
              background: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
              border: isDark
                ? '1px solid rgba(255,255,255,0.06)'
                : '1px solid rgba(0,0,0,0.06)',
              color: isDark ? '#cbd5e1' : '#475569',
            }}
          >
            <s.icon size={18} style={{ color: s.color, shrink: 0 }} />
            <span>{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
