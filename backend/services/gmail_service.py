"""
Service for interacting with Gmail API.
"""
import base64
from sqlalchemy.orm import Session
from models import User
from services.google_api_factory import get_gmail_service


def list_messages(user: User, db: Session, count: int = 5):
    """Retrieve latest email snippets from Inbox."""
    service = get_gmail_service(user, db)
    
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=count).execute()
    messages = results.get('messages', [])
    
    email_list = []
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id'], format='minimal').execute()
        
        # Extract headers
        headers = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute().get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        
        email_list.append({
            "from": sender,
            "subject": subject,
            "snippet": m.get('snippet')
        })
        
    return email_list


def _build_raw_message(to: str, subject: str, body: str) -> str:
    """Build RFC 2822 message and return base64url-encoded string."""
    message_body = (
        f"To: {to}\r\n"
        f"Subject: {subject}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"\r\n"
        f"{body}"
    )
    return base64.urlsafe_b64encode(message_body.encode()).decode()


def create_draft_email(user: User, db: Session, to: str, subject: str, body: str):
    """Create a draft email."""
    service = get_gmail_service(user, db)
    
    encoded_message = _build_raw_message(to, subject, body)
    
    draft_body = {
        'message': {
            'raw': encoded_message
        }
    }
    
    draft = service.users().drafts().create(userId='me', body=draft_body).execute()
    
    return {
        "to": to,
        "subject": subject,
        "body": body,
        "draft_id": draft.get('id')
    }


def send_email(user: User, db: Session, to: str, subject: str, body: str):
    """Send an email immediately via Gmail API."""
    service = get_gmail_service(user, db)
    
    encoded_message = _build_raw_message(to, subject, body)
    
    message_body = {
        'raw': encoded_message
    }
    
    sent = service.users().messages().send(userId='me', body=message_body).execute()
    
    return {
        "to": to,
        "subject": subject,
        "body": body,
        "message_id": sent.get('id'),
        "thread_id": sent.get('threadId'),
    }
