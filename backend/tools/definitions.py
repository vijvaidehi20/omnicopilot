"""
Tool definitions — schemas used in the Gemini system prompt so the model
knows which tools are available and what parameters they accept.
"""

TOOL_DEFINITIONS = [
    {
        "name": "create_event",
        "description": "Create a new event in the user's Google Calendar. Includes a Meet link.",
        "parameters": {
            "title": {"type": "string", "description": "Title of the event", "required": True},
            "date": {"type": "string", "description": "Date (e.g., 'today', '2026-05-20')", "required": True},
            "time": {"type": "string", "description": "Time (e.g., '3 PM', '14:00')", "required": False},
            "attendees": {"type": "array", "description": "List of attendee email addresses", "required": False},
            "generate_invite_email": {"type": "boolean", "description": "Set to true if user asks to send or draft an invite email", "required": False},
        },
    },
    {
        "name": "update_event",
        "description": "Update an EXISTING Google Calendar event. Use this to add attendees, change time, or change title. Do NOT use create_event to modify an existing event.",
        "parameters": {
            "event_id": {"type": "string", "description": "The event ID to update (from [CONTEXT] last event)", "required": True},
            "title": {"type": "string", "description": "New title (only if changing)", "required": False},
            "date": {"type": "string", "description": "New date (only if changing)", "required": False},
            "time": {"type": "string", "description": "New time (only if changing)", "required": False},
            "attendees": {"type": "array", "description": "Email addresses to ADD as attendees", "required": False},
        },
    },
    {
        "name": "send_email",
        "description": "Send an email IMMEDIATELY via Gmail. Use this when user says 'send', 'send invite', or 'send email'. This SENDS the email, not drafts it.",
        "parameters": {
            "to": {"type": "string", "description": "Recipient email address", "required": True},
            "subject": {"type": "string", "description": "Email subject line", "required": True},
            "body": {"type": "string", "description": "Full email body text", "required": True},
        },
    },
    {
        "name": "read_emails",
        "description": "Fetch the 5 most recent emails from the user's Gmail inbox.",
        "parameters": {
            "query": {"type": "string", "description": "Optional search query", "required": False},
        },
    },
    {
        "name": "draft_email",
        "description": "Create a DRAFT email in Gmail (does NOT send). Use this ONLY when user explicitly says 'draft'.",
        "parameters": {
            "to": {"type": "string", "description": "The recipient's email address", "required": True},
            "subject": {"type": "string", "description": "The subject of the email", "required": True},
            "body": {"type": "string", "description": "The full body of the email. Use your AI intelligence to generate this.", "required": True},
        },
    },
    {
        "name": "summarize_document",
        "description": "Extract text from the latest Google Drive file and summarize its content.",
    },
    {
        "name": "list_drive_files",
        "description": "Fetch the 10 most recent files from the user's Google Drive. Returns name, file_id, and mimeType.",
        "parameters": {
            "count": {"type": "integer", "description": "Number of files to retrieve (default 10)", "required": False},
        },
    },
    {
        "name": "create_document",
        "description": "Creates a new Google Doc and inserts the given content inside.",
        "parameters": {
            "title": {"type": "string", "description": "Title of the document", "required": True},
            "content": {"type": "string", "description": "Formatted text/paragraphs to insert into the document", "required": True}
        }
    },
    {
        "name": "create_reminder",
        "description": "Creates a scheduled reminder that alerts the user.",
        "parameters": {
            "message": {"type": "string", "description": "What to remind the user about.", "required": True},
            "scheduled_time": {"type": "string", "description": "ISO 8601 formatted datetime string indicating when the reminder should sound (e.g. 2026-04-19T18:00:00). MUST BE LOCAL TIME.", "required": True}
        }
    },
    {
        "name": "analyze_file",
        "description": "Answers questions based on a recently uploaded file.",
        "parameters": {
            "question": {"type": "string", "description": "The user's question or instruction about the uploaded file.", "required": True}
        }
    }
]


def get_tools_prompt_section() -> str:
    """Format tool definitions into a string for the system prompt."""
    lines = ["You have access to the following tools:\n"]
    for tool in TOOL_DEFINITIONS:
        lines.append(f"### {tool['name']}")
        lines.append(f"Description: {tool['description']}")
        if "parameters" in tool and tool["parameters"]:
            lines.append("Parameters:")
            for pname, pinfo in tool["parameters"].items():
                req = " (required)" if pinfo.get("required") else " (optional)"
                lines.append(f"  - {pname} ({pinfo['type']}): {pinfo['description']}{req}")
        else:
            lines.append("Parameters: None")
        lines.append("")
    return "\n".join(lines)
