"""
Real tool handler implementations using Google Service layers.
"""
from sqlalchemy.orm import Session
from models import User
from services.calendar_service import create_calendar_event, update_calendar_event
from services.gmail_service import list_messages, create_draft_email, send_email


def create_event_handler(user: User, db: Session, params: dict) -> dict:
    """Handle create_event tool call."""
    title = params.get("title")
    date = params.get("date")
    time = params.get("time", "")
    attendees = params.get("attendees")
    
    result = create_calendar_event(user, db, title, date, time, attendees)
    
    if params.get("generate_invite_email") and attendees:
        meet_link = result.get('meet_link', '')
        date_str = result.get('start_time', '')
        # Simplified parser handles this logic but a raw formatted insert is sufficient here.
        body = f"Hi,\n\nYou're invited to a meeting.\n\n📅 Date: {date_str}\n🔗 Join: {meet_link}\n\nRegards,\nVaidehi"
        result['pending_email'] = {
            'to': ", ".join(attendees),
            'subject': title,
            'body': body
        }
        
    return {
        "status": "success",
        "tool": "create_event",
        "result": result
    }


def update_event_handler(user: User, db: Session, params: dict) -> dict:
    """Handle update_event tool call — PATCH an existing event."""
    event_id = params.get("event_id")
    if not event_id:
        return {
            "status": "error",
            "tool": "update_event",
            "result": {"message": "Missing event_id. Cannot update without knowing which event to modify."}
        }
    
    result = update_calendar_event(
        user, db,
        event_id=event_id,
        title=params.get("title"),
        date_str=params.get("date"),
        time_str=params.get("time"),
        attendees=params.get("attendees")
    )
    return {
        "status": "success",
        "tool": "update_event",
        "result": result
    }


def read_emails_handler(user: User, db: Session, params: dict) -> dict:
    """Handle read_emails tool call."""
    emails = list_messages(user, db, count=5)
    return {
        "status": "success",
        "tool": "read_emails",
        "result": {"emails": emails}
    }


def send_email_handler(user: User, db: Session, params: dict) -> dict:
    from services.gmail_service import send_email
    send_email(
        user, db,
        to_address=params.get("to"),
        subject=params.get("subject"),
        body=params.get("body")
    )
    return {
        "status": "success",
        "tool": "send_email",
        "result": {"message": "Email sent"}
    }


def create_document_handler(user: User, db: Session, params: dict) -> dict:
    from services.docs_service import create_google_doc
    title = params.get("title", "Untitled Document")
    content = params.get("content", "")
    print(f"[DEBUG] create_document_handler: Received content of length {len(content)}")
    result = create_google_doc(
        user, db,
        title=title,
        content=content
    )
    return {
        "status": "success",
        "tool": "create_document",
        "result": result
    }


def draft_email_handler(user: User, db: Session, params: dict) -> dict:
    """Handle draft_email tool call."""
    to = params.get("to")
    subject = params.get("subject")
    body = params.get("body")
    
    result = create_draft_email(user, db, to, subject, body)
    return {
        "status": "success",
        "tool": "draft_email",
        "result": result
    }

def list_drive_files_handler(user: User, db: Session, params: dict) -> dict:
    """Handle list_drive_files tool call."""
    from services.drive_service import list_drive_files
    count = params.get("count", 10)
    files = list_drive_files(user, db, count)
    return {
        "status": "success",
        "tool": "list_drive_files",
        "result": {"files": files}
    }


def summarize_document_handler(user: User, db: Session, params: dict) -> dict:
    """Handle summarize_document tool call."""
    from services.drive_service import fetch_drive_file, extract_text_from_file, list_drive_files
    
    # 1. Fetch file list (already ordered by modifiedTime desc)
    files = list_drive_files(user, db, count=20)

    # 2. Filter files (Google Docs, PDF, text)
    valid_mime_types = [
        'application/vnd.google-apps.document',
        'application/pdf',
        'text/plain',
        'text/csv',
        'application/json',
        'text/markdown'
    ]
    
    valid_files = [f for f in files if f["type"] in valid_mime_types]
    if not valid_files:
        return {
            "status": "error",
            "tool": "summarize_document",
            "result": {"message": "No valid Google Docs, PDFs, or text files found."}
        }

    # 3. Select file
    latest_file = valid_files[0]
    file_id = latest_file["file_id"]

    # 4. Fetch file
    file_stream, name, mime = fetch_drive_file(user, db, file_id)
    
    # 5. Extract text
    content = extract_text_from_file(file_stream, mime)
    
    # 3. Return content for backend to send back to AI for summarization
    return {
        "status": "success",
        "tool": "summarize_document",
        "result": {
            "file_name": name,
            "filename": name, # Kept for backwards compatibility with ai_service
            "content": content,
            "message": f"Retrieved content from '{name}'. Processing summary..."
        }
    }


def analyze_file_handler(user: User, db: Session, params: dict) -> dict:
    from services.file_store import get_file_text
    file_data = get_file_text(user.id)
    if not file_data:
        return {
            "status": "error",
            "tool": "analyze_file",
            "result": {"message": "No file uploaded or recognized. Please upload a file first."}
        }
    
    return {
        "status": "success",
        "tool": "analyze_file",
        "result": {
            "content": file_data["content"],
            "filename": file_data["filename"],
            "message": f"Analyzing local uploaded file: '{file_data['filename']}'"
        }
    }


def create_reminder_handler(user: User, db: Session, params: dict) -> dict:
    from services.reminder_service import schedule_reminder
    from services.calendar_service import create_calendar_event
    from dateutil.parser import parse
    import pytz
    
    msg = params.get("message")
    t_str = params.get("scheduled_time")
    IST = pytz.timezone("Asia/Kolkata")
    
    try:
        t_obj = parse(t_str)
        if not t_obj.tzinfo:
            # If AI didn't provide TZ, assume Asia/Kolkata
            t_obj = IST.localize(t_obj)
        else:
            # Convert to IST
            t_obj = t_obj.astimezone(IST)
            
        print(f"[DEBUG] Reminder parsed and localized to IST: {t_obj}")
            
        # 1. Sync to Google Calendar (Real phone notification)
        cal_date = t_obj.strftime("%Y-%m-%d")
        cal_time = t_obj.strftime("%H:%M:%S")
        create_calendar_event(user, db, f"Reminder: {msg}", cal_date, cal_time)
        
        # 2. Add to internal background scheduler (Bell icon notification)
        rem = schedule_reminder(user, db, msg, t_obj)
        
        return {
            "status": "success",
            "tool": "create_reminder",
            "result": {
                "message": msg,
                "time": t_obj.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "display_time": t_obj.strftime("%I:%M %p, %B %d")
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "tool": "create_reminder",
            "result": {"message": f"Failed to parse time or schedule reminder. {e}"}
        }

