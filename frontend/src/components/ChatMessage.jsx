import { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import {
  User, Sparkles, Wrench, Calendar, Mail, FileText, StickyNote,
  ExternalLink, Video, Clock, Send, PenLine, Settings2, ChevronDown, ChevronUp
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { sendDirectEmail, draftDirectEmail } from '../services/api';
const TOOL_ICONS = {
  create_event: Calendar,
  read_emails: Mail,
  draft_email: Mail,
  summarize_document: FileText,
  summarize_file: FileText,
  list_drive_files: FileText,
  create_document: FileText,
  analyze_file: FileText,
  create_reminder: Clock,
  save_note: StickyNote,
};

export default function ChatMessage({ message, onAction }) {
  const { isDark } = useTheme();
  const isUser = message.role === 'user';

  return (
    <div
      className="animate-fade-in flex gap-3 px-4 py-3 max-w-3xl mx-auto"
      style={{ animationDelay: '0.05s' }}
    >
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
        style={{
          background: isUser
            ? (isDark ? 'linear-gradient(135deg, #1e2538, #2a3247)' : 'linear-gradient(135deg, #e2e8f0, #cbd5e1)')
            : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          border: isUser
            ? (isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid rgba(0,0,0,0.08)')
            : 'none',
        }}
      >
        {isUser ? (
          <User size={15} style={{ color: isDark ? '#94a3b8' : '#64748b' }} />
        ) : (
          <Sparkles size={15} className="text-white" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-2">
        <p className="text-xs font-semibold tracking-wide"
          style={{ color: isDark ? '#64748b' : '#94a3b8' }}
        >
          {isUser ? 'You' : 'OmniCopilot'}
        </p>

        {/* Tool result card — specialized by tool type */}
        {message.tool_used && message.tool_result && (
          <ToolCard
            toolName={message.tool_used}
            result={message.tool_result}
            isDark={isDark}
            onAction={onAction}
          />
        )}

        {/* Message text */}
        {message.content && (
          <div
            className="text-sm leading-relaxed prose prose-sm max-w-none"
            style={{ color: isDark ? '#cbd5e1' : '#334155' }}
          >
            {isUser ? (
              <p>{message.content}</p>
            ) : (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Routes to the correct specialized card based on tool name.
 */
function ToolCard({ toolName, result, isDark, onAction }) {
  if (result.status === 'auth_error') {
    return null; // Auth errors are shown in the message text
  }

  switch (toolName) {
    case 'create_event':
    case 'update_event':
      return <MeetingCard toolName={toolName} result={result} isDark={isDark} onAction={onAction} />
    case 'draft_email':
      return <DraftEmailCard result={result} isDark={isDark} />;
    case 'read_emails':
      return <EmailListCard result={result} isDark={isDark} />;
    case 'create_document':
      return <DocumentCard result={result} isDark={isDark} />;
    default:
      return <GenericToolCard toolName={toolName} result={result} isDark={isDark} />;
  }
}

// ─────────────────────────────────────────────
//  Document Card
// ─────────────────────────────────────────────

function DocumentCard({ result, isDark }) {
  const res = result.result || {};
  const title = res.title || 'Untitled Document';
  const docLink = res.doc_link || '';

  return (
    <div className="tool-card doc-card animate-slide-in" data-dark={isDark}>
      <div className="tool-card-header">
        <div className="flex items-center gap-2">
          <FileText size={15} style={{ color: '#f472b6' }} />
          <span className="tool-card-label">Document Created</span>
        </div>
        <StatusBadge status={result.status} />
      </div>

      <div className="meeting-card-body pb-0">
        <h4 className="meeting-title">{title}</h4>
      </div>

      {docLink && (
        <div className="meeting-links mt-3">
          <a
            href={docLink}
            target="_blank"
            rel="noopener noreferrer"
            className="meeting-link-btn primary"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <ExternalLink size={14} />
            Open Document
          </a>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
//  Meeting Card
// ─────────────────────────────────────────────

function MeetingCard({ toolName, result, isDark, onAction }) {
  const res = result.result || {};
  const title = res.title || 'Meeting';
  const startTime = res.start_time || '';
  const meetLink = res.meet_link || '';
  const calendarLink = res.html_link || '';

  // Format the date/time nicely
  const formattedTime = formatDateTime(startTime);

  return (
    <div className="tool-card meeting-card animate-slide-in" data-dark={isDark}>
      {/* Header */}
      <div className="tool-card-header">
        <div className="flex items-center gap-2">
          <Calendar size={15} style={{ color: '#818cf8' }} />
          <span className="tool-card-label">
            {toolName === 'update_event' ? 'Meeting Updated' : 'Meeting Created'}
          </span>
        </div>
        <StatusBadge status={result.status} />
      </div>

      {/* Content */}
      <div className="meeting-card-body">
        <h4 className="meeting-title">{title}</h4>
        {formattedTime && (
          <div className="meeting-detail">
            <Clock size={13} />
            <span>{formattedTime}</span>
          </div>
        )}
        {res.attendees && res.attendees.length > 0 && (
          <div className="meeting-detail mt-1">
            <User size={13} />
            <span>{res.attendees.length} Attendees</span>
          </div>
        )}
      </div>

      {/* Links */}
      <div className="meeting-links">
        {meetLink && (
          <a
            href={meetLink}
            target="_blank"
            rel="noopener noreferrer"
            className="meeting-link-btn primary"
          >
            <Video size={14} />
            Join Meeting
            <ExternalLink size={11} />
          </a>
        )}
        {calendarLink && (
          <a
            href={calendarLink}
            target="_blank"
            rel="noopener noreferrer"
            className="meeting-link-btn secondary"
          >
            <Calendar size={14} />
            Open Calendar
            <ExternalLink size={11} />
          </a>
        )}
      </div>
      {res.pending_email && (
        <InlineEmailEditor initialData={res.pending_email} isDark={isDark} />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
//  Inline Email Editor
// ─────────────────────────────────────────────

function InlineEmailEditor({ initialData, isDark }) {
  const [to, setTo] = useState(initialData.to || '');
  const [subject, setSubject] = useState(initialData.subject || '');
  const [body, setBody] = useState(initialData.body || '');
  const [status, setStatus] = useState('editing');

  const handleSend = async () => {
    setStatus('sending');
    try {
      await sendDirectEmail(to, subject, body);
      setStatus('sent');
    } catch (e) {
      console.error(e);
      setStatus('editing');
      alert("Failed to send email");
    }
  };

  const handleDraft = async () => {
    setStatus('sending');
    try {
      await draftDirectEmail(to, subject, body);
      setStatus('sent_draft');
    } catch (e) {
      console.error(e);
      setStatus('editing');
      alert("Failed to save draft");
    }
  };

  if (status === 'sent' || status === 'sent_draft') {
    return (
      <div className="mt-3 p-3 rounded-lg border flex flex-col gap-2 animate-fade-in" style={{ borderColor: 'rgba(52,211,153,0.3)', background: 'rgba(52,211,153,0.05)' }}>
        <div className="flex items-center gap-2">
           <Mail size={14} style={{ color: '#34d399' }} />
           <span style={{ fontSize: '13px', color: '#34d399', fontWeight: 500 }}>
             {status === 'sent' ? 'Email sent successfully.' : 'Email saved to drafts.'}
           </span>
        </div>
      </div>
    );
  }

  return (
    <div className="email-card mt-3 animate-fade-in" style={{ opacity: status === 'sending' ? 0.6 : 1 }}>
      <div className="email-header">
        <span className="email-field-label w-12 shrink-0">To:</span>
        <input 
          className="bg-transparent outline-none flex-1 font-medium text-[13px]" 
          style={{ color: isDark ? '#e2e8f0' : '#1e293b' }}
          value={to} 
          onChange={e=>setTo(e.target.value)} 
        />
      </div>
      <div className="email-header border-t-0 pt-1 mt-1">
        <span className="email-field-label w-12 shrink-0">Subject:</span>
        <input 
          className="bg-transparent outline-none flex-1 font-semibold text-[13px]" 
          style={{ color: isDark ? '#f8fafc' : '#0f172a' }}
          value={subject} 
          onChange={e=>setSubject(e.target.value)} 
        />
      </div>
      <div className="email-body mt-2">
        <textarea 
          className="w-full bg-transparent outline-none resize-y text-[13px] leading-relaxed" 
          rows={6} 
          style={{ color: isDark ? '#cbd5e1' : '#475569' }}
          value={body} 
          onChange={e=>setBody(e.target.value)} 
        />
      </div>
      <div className="tool-action-row pt-2 mt-2" style={{ borderTop: isDark ? '1px solid rgba(255,255,255,0.05)' : '1px solid rgba(0,0,0,0.05)' }}>
        <button 
          className="tool-action-btn" 
          onClick={handleSend} 
          disabled={status === 'sending'}
          style={{ background: 'linear-gradient(135deg, #6366f1, #4f46e5)', color: 'white', borderColor: 'transparent' }}
        >
          <Send size={13}/>
          {status === 'sending' ? 'Sending...' : 'Send'}
        </button>
        <button 
          className="tool-action-btn" 
          onClick={handleDraft} 
          disabled={status === 'sending'}
        >
          <PenLine size={13}/>
          Save Draft
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
//  Draft Email Card
// ─────────────────────────────────────────────

function DraftEmailCard({ result, isDark }) {
  const res = result.result || {};
  const to = res.to || '';
  const subject = res.subject || '';
  const body = res.body || '';
  const draftId = res.draft_id || '';

  return (
    <div className="tool-card email-card animate-slide-in" data-dark={isDark}>
      {/* Header */}
      <div className="tool-card-header">
        <div className="flex items-center gap-2">
          <Mail size={15} style={{ color: '#22d3ee' }} />
          <span className="tool-card-label" style={{ color: '#22d3ee' }}>Email Drafted</span>
        </div>
        <StatusBadge status={result.status} />
      </div>

      {/* Content */}
      <div className="email-card-body">
        {to && (
          <div className="email-field">
            <span className="email-field-label">To</span>
            <span className="email-field-value">{to}</span>
          </div>
        )}
        {subject && (
          <div className="email-field">
            <span className="email-field-label">Subject</span>
            <span className="email-field-value">{subject}</span>
          </div>
        )}
        {body && (
          <div className="email-field">
            <span className="email-field-label">Body</span>
            <span className="email-field-value email-body-preview">{body}</span>
          </div>
        )}
      </div>

      {/* Open in Gmail */}
      {draftId && (
        <div className="meeting-links">
          <a
            href="https://mail.google.com/mail/u/0/#drafts"
            target="_blank"
            rel="noopener noreferrer"
            className="meeting-link-btn secondary"
            style={{ borderColor: 'rgba(34,211,238,0.2)' }}
          >
            <Mail size={14} />
            Open in Gmail
            <ExternalLink size={11} />
          </a>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
//  Email List Card
// ─────────────────────────────────────────────

function EmailListCard({ result, isDark }) {
  const emails = result.result?.emails || [];

  if (emails.length === 0) return null;

  return (
    <div className="tool-card email-list-card animate-slide-in" data-dark={isDark}>
      {/* Header */}
      <div className="tool-card-header">
        <div className="flex items-center gap-2">
          <Mail size={15} style={{ color: '#22d3ee' }} />
          <span className="tool-card-label" style={{ color: '#22d3ee' }}>
            Inbox ({emails.length} emails)
          </span>
        </div>
        <StatusBadge status={result.status} />
      </div>

      {/* Email list */}
      <div className="email-list-body">
        {emails.map((email, i) => (
          <div key={i} className="email-list-item">
            <div className="email-list-sender">{email.from?.split('<')[0]?.trim() || 'Unknown'}</div>
            <div className="email-list-subject">{email.subject || 'No Subject'}</div>
            {email.snippet && (
              <div className="email-list-snippet">{email.snippet}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
//  Generic Tool Card (fallback)
// ─────────────────────────────────────────────

function GenericToolCard({ toolName, result, isDark }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = TOOL_ICONS[toolName] || Wrench;

  return (
    <div className="tool-card generic-card animate-slide-in" data-dark={isDark}>
      <div className="tool-card-header">
        <div className="flex items-center gap-2">
          <Icon size={15} style={{ color: '#818cf8' }} />
          <span className="tool-card-label">{toolName.replace(/_/g, ' ')}</span>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={result.status} />
          <button
            className="tool-expand-btn"
            onClick={() => setExpanded(!expanded)}
            title={expanded ? 'Hide details' : 'Show details'}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {expanded && (
        <pre
          className="text-[11px] overflow-x-auto rounded-lg p-2 mt-2"
          style={{
            background: isDark ? 'rgba(0,0,0,0.3)' : 'rgba(0,0,0,0.03)',
            color: isDark ? '#94a3b8' : '#64748b',
          }}
        >
          {JSON.stringify(result.result, null, 2)}
        </pre>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
//  Shared Components
// ─────────────────────────────────────────────

function StatusBadge({ status }) {
  const isSuccess = status === 'success';
  return (
    <span
      className="text-[10px] px-2 py-0.5 rounded-full font-medium"
      style={{
        background: isSuccess ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
        color: isSuccess ? '#22c55e' : '#ef4444',
      }}
    >
      {status}
    </span>
  );
}

// ─────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────

function formatDateTime(isoString) {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return isoString;
  }
}
