"""
Chat route — protected endpoint that accepts user messages and returns AI responses.
Supports persistent chat sessions with message history.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Any
import io
import PyPDF2
from PIL import Image
import pytesseract

from auth.utils import get_current_user
from models import User, ChatSession, ChatMessage
from services.ai_service import generate_response
from services.file_store import store_file_text

from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(tags=["Chat"])

# --------------- Schemas ---------------

class MessageIn(BaseModel):
    message: str
    session_id: Optional[int] = None
    history: list[dict] = []  # [{role: "user"|"assistant", content: "..."}]


class MessageOut(BaseModel):
    response: str
    session_id: int
    type: str = "text"
    tool_used: str | None = None
    tool_result: dict | None = None


class SessionOut(BaseModel):
    id: int
    title: str
    created_at: str


class SessionMessageOut(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str
    tool_used: str | None = None
    tool_result: dict | None = None


class EmailActionRequest(BaseModel):
    to: str
    subject: str
    body: str


class NotificationOut(BaseModel):
    id: int
    message: str
    is_read: bool
    timestamp: str


# --------------- Direct Email Endpoints ---------------

@router.post("/send-email")
def api_send_email(
    req: EmailActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Directly send an email, bypassing the LLM."""
    from services.gmail_service import send_email
    return send_email(current_user, db, req.to, req.subject, req.body)

@router.post("/draft-email")
def api_draft_email(
    req: EmailActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Directly draft an email, bypassing the LLM."""
    from services.gmail_service import create_draft_email
    return create_draft_email(current_user, db, req.to, req.subject, req.body)


# --------------- Chat Endpoint (modified) ---------------

@router.post("/chat", response_model=MessageOut)
async def chat(
    body: MessageIn, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get an AI response (with optional tool execution)."""
    import traceback
    
    print(f"\n[DEBUG] --- NEW CHAT REQUEST ---")
    print(f"[DEBUG] User: {current_user.email} (ID: {current_user.id})")
    print(f"[DEBUG] Message: {body.message}")
    print(f"[DEBUG] Session ID: {body.session_id}")
    print(f"[DEBUG] History Length: {len(body.history)}")

    # Resolve or create session
    session = None
    if body.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == body.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

    if not session:
        # Auto-generate title from first message (truncated)
        title = body.message[:80].strip()
        if len(body.message) > 80:
            title += "…"
        session = ChatSession(user_id=current_user.id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"[DEBUG] Created new session: {session.id} — \"{session.title}\"")

    # Save user message to DB
    user_msg = ChatMessage(session_id=session.id, role="user", content=body.message)
    db.add(user_msg)
    db.commit()

    # Build full conversation with the new message appended
    conversation = list(body.history)
    conversation.append({"role": "user", "content": body.message})

    try:
        print("USER INPUT:", body.message)
        result = generate_response(conversation, current_user, db)

        # Save assistant message to DB (with tool metadata for persistence)
        tool_meta = None
        if result.get("tool_used") and result.get("tool_result"):
            tool_meta = json.dumps({
                "tool_used": result["tool_used"],
                "tool_result": result["tool_result"]
            })
        
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=result.get("response", ""),
            tool_metadata=tool_meta
        )
        db.add(assistant_msg)
        db.commit()

        return MessageOut(session_id=session.id, **result)
    except Exception as e:
        traceback.print_exc()
        print("FULL ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# --------------- Session Endpoints ---------------

@router.get("/chat/sessions", response_model=list[SessionOut])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return all chat sessions for the current user, newest first."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return [
        SessionOut(
            id=s.id,
            title=s.title,
            created_at=s.created_at.isoformat() if s.created_at else ""
        )
        for s in sessions
    ]


@router.get("/chat/sessions/{session_id}/messages", response_model=list[SessionMessageOut])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return all messages for a given session (ownership-verified)."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    result = []
    for m in messages:
        tool_used = None
        tool_result = None
        if m.tool_metadata:
            try:
                meta = json.loads(m.tool_metadata)
                tool_used = meta.get("tool_used")
                tool_result = meta.get("tool_result")
            except (json.JSONDecodeError, TypeError):
                pass
        result.append(SessionMessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            timestamp=m.timestamp.isoformat() if m.timestamp else "",
            tool_used=tool_used,
            tool_result=tool_result
        ))
    return result


@router.delete("/chat/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a session and all its messages."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()
    return {"status": "deleted", "session_id": session_id}

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Uploads a file and extracts its text to memory cache."""
    try:
        content_bytes = await file.read()
        extracted_text = ""
        filename = file.filename.lower()

        if filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            try:
                img = Image.open(io.BytesIO(content_bytes))
                extracted_text = pytesseract.image_to_string(img)
            except Exception as e:
                extracted_text = f"[OCR Failed: Ensure Tesseract is installed. Error: {e}]"
        else:
            extracted_text = content_bytes.decode("utf-8", errors="ignore")
            
        if not extracted_text.strip():
            extracted_text = "[No readable text found]"

        # Store in internal memory map
        store_file_text(current_user.id, file.filename, extracted_text)

        return {"status": "success", "filename": file.filename, "message": "File processed and ready for analysis."}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

# --------------- Notification Endpoints ---------------

@router.get("/notifications", response_model=list[NotificationOut])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch unread notifications for the user."""
    from models import Notification
    
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .order_by(Notification.timestamp.desc())
        .limit(10)
        .all()
    )
    
    return [
        NotificationOut(
            id=n.id,
            message=n.message,
            is_read=n.is_read,
            timestamp=n.timestamp.isoformat() if n.timestamp else ""
        )
        for n in notifications
    ]

@router.post("/notifications/read")
async def mark_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all unread notifications as read."""
    from models import Notification
    
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    return {"status": "success"}

