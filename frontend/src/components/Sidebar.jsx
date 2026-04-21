import { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';
import { LogOut, Sparkles, MessageSquare, Plus, Trash2, Loader2 } from 'lucide-react';

/**
 * Groups sessions into "Today", "Yesterday", "Previous 7 Days", and "Older".
 */
function groupSessionsByDate(sessions) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  const groups = { Today: [], Yesterday: [], 'Previous 7 Days': [], Older: [] };

  sessions.forEach((s) => {
    const d = new Date(s.created_at);
    if (d >= today) groups.Today.push(s);
    else if (d >= yesterday) groups.Yesterday.push(s);
    else if (d >= weekAgo) groups['Previous 7 Days'].push(s);
    else groups.Older.push(s);
  });

  // Return only non-empty groups
  return Object.entries(groups).filter(([, items]) => items.length > 0);
}

export default function Sidebar({
  onNewChat,
  sessions = [],
  activeSessionId,
  onSelectSession,
  onDeleteSession,
  sessionsLoading,
}) {
  const { isDark } = useTheme();
  const { user, logout } = useAuth();

  const grouped = groupSessionsByDate(sessions);

  return (
    <aside
      className="w-64 h-screen flex flex-col transition-colors duration-300 shrink-0"
      style={{
        background: isDark
          ? 'linear-gradient(180deg, #0d1220 0%, #111827 100%)'
          : 'linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)',
        borderRight: isDark
          ? '1px solid rgba(255,255,255,0.06)'
          : '1px solid rgba(0,0,0,0.08)',
      }}
    >
      {/* Brand */}
      <div className="p-5 flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center animate-pulse-glow"
          style={{
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          }}
        >
          <Sparkles size={18} className="text-white" />
        </div>
        <div>
          <h1 className="font-bold text-base tracking-tight"
            style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}
          >
            OmniCopilot
          </h1>
          <p className="text-[10px] font-medium tracking-widest uppercase"
            style={{ color: isDark ? '#64748b' : '#94a3b8' }}
          >
            AI Assistant
          </p>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-3 mb-2">
        <button
          id="new-chat-btn"
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
          style={{
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            color: '#fff',
            boxShadow: '0 4px 15px rgba(99,102,241,0.3)',
          }}
        >
          <Plus size={16} />
          New Chat
        </button>
      </div>

      {/* Chat history list */}
      <div className="flex-1 overflow-y-auto px-2 py-1 chat-history-scroll">
        {sessionsLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={20} className="animate-spin" style={{ color: '#64748b' }} />
          </div>
        ) : sessions.length === 0 ? (
          <p
            className="text-xs px-3 py-4 flex items-center gap-2"
            style={{ color: isDark ? '#475569' : '#94a3b8' }}
          >
            <MessageSquare size={14} />
            No conversations yet
          </p>
        ) : (
          grouped.map(([groupLabel, items]) => (
            <div key={groupLabel} className="mb-2">
              <p
                className="text-[10px] font-semibold uppercase tracking-wider px-3 py-1.5"
                style={{ color: isDark ? '#475569' : '#94a3b8' }}
              >
                {groupLabel}
              </p>
              {items.map((s) => (
                <SessionItem
                  key={s.id}
                  session={s}
                  isActive={s.id === activeSessionId}
                  isDark={isDark}
                  onSelect={() => onSelectSession(s.id)}
                  onDelete={() => onDeleteSession(s.id)}
                />
              ))}
            </div>
          ))
        )}
      </div>

      {/* Bottom section */}
      <div
        className="p-4 space-y-3"
        style={{
          borderTop: isDark
            ? '1px solid rgba(255,255,255,0.06)'
            : '1px solid rgba(0,0,0,0.06)',
        }}
      >
        {/* Theme toggle */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium" style={{ color: isDark ? '#64748b' : '#94a3b8' }}>
            Theme
          </span>
          <ThemeToggle />
        </div>

        {/* User info + logout */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
              style={{
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff',
              }}
            >
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <span
              className="text-xs truncate"
              style={{ color: isDark ? '#94a3b8' : '#64748b' }}
              title={user?.email}
            >
              {user?.email || 'User'}
            </span>
          </div>
          <button
            id="logout-btn"
            onClick={logout}
            className="p-1.5 rounded-lg transition-all duration-200 hover:scale-110 cursor-pointer"
            style={{
              color: isDark ? '#64748b' : '#94a3b8',
            }}
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}

/**
 * Individual session item in the sidebar.
 */
function SessionItem({ session, isActive, isDark, onSelect, onDelete }) {
  const [hovered, setHovered] = useState(false);

  const bgActive = isDark
    ? 'rgba(99,102,241,0.12)'
    : 'rgba(99,102,241,0.08)';
  const bgHover = isDark
    ? 'rgba(255,255,255,0.04)'
    : 'rgba(0,0,0,0.03)';

  return (
    <button
      className="session-item w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-[13px] transition-all duration-150 cursor-pointer group relative"
      style={{
        background: isActive ? bgActive : hovered ? bgHover : 'transparent',
        color: isActive
          ? (isDark ? '#c7d2fe' : '#4f46e5')
          : (isDark ? '#94a3b8' : '#64748b'),
        borderLeft: isActive ? '2px solid #6366f1' : '2px solid transparent',
      }}
      onClick={onSelect}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      title={session.title}
    >
      <MessageSquare
        size={14}
        className="shrink-0"
        style={{
          color: isActive ? '#818cf8' : isDark ? '#475569' : '#94a3b8',
        }}
      />
      <span className="truncate flex-1">{session.title}</span>

      {/* Delete button — visible on hover */}
      {hovered && (
        <span
          className="session-delete-btn shrink-0 p-1 rounded-md transition-all duration-150"
          style={{
            color: isDark ? '#64748b' : '#94a3b8',
          }}
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          title="Delete chat"
        >
          <Trash2 size={13} />
        </span>
      )}
    </button>
  );
}
