"""
Tool registry — maps tool names to their handler functions.
"""
from typing import Callable
from sqlalchemy.orm import Session
from models import User
from tools.handlers import (
    create_event_handler,
    update_event_handler,
    read_emails_handler,
    send_email_handler,
    draft_email_handler, 
    summarize_document_handler,
    list_drive_files_handler,
    create_document_handler,
    analyze_file_handler,
    create_reminder_handler
)

# Registry mapping tool names to handlers
# Handlers now expect (user: User, db: Session, params: dict)
TOOL_REGISTRY: dict[str, Callable] = {
    "create_event": create_event_handler,
    "update_event": update_event_handler,
    "create_document": create_document_handler,
    "read_emails": read_emails_handler,
    "send_email": send_email_handler,
    "draft_email": draft_email_handler,
    "summarize_document": summarize_document_handler,
    "list_drive_files": list_drive_files_handler,
    "analyze_file": analyze_file_handler,
    "create_reminder": create_reminder_handler,
}


def execute_tool(tool_name: str, params: dict, user: User, db: Session) -> dict:
    """Look up a tool by name and execute it with user context."""
    handler = TOOL_REGISTRY.get(tool_name)
    if handler is None:
        return {
            "status": "error",
            "tool": tool_name,
            "result": {"message": f"Unknown tool: {tool_name}"},
        }
    
    try:
        # Check if user has Google tokens for real integrations
        if not user.google_access_token:
            print("TOOL AUTH ERROR: No Google tokens found for user")
            return {
                "status": "auth_error",
                "tool": tool_name,
                "result": {"message": "Please connect your Google account to use this feature."}
            }
            
        print(f"EXECUTING TOOL: {tool_name}")
        return handler(user, db, params)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"TOOL FATAL ERROR in {tool_name}:", str(e))
        return {
            "status": "error",
            "tool": tool_name,
            "result": {"message": f"Tool execution failed: {str(e)}"},
        }


def list_tools() -> list[str]:
    """Return all registered tool names."""
    return list(TOOL_REGISTRY.keys())
