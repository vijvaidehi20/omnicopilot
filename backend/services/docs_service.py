"""
Service for interacting with Google Docs API.
Handles document creation and content insertion.
"""
from sqlalchemy.orm import Session
from models import User
from services.google_api_factory import get_docs_service

def create_google_doc(user: User, db: Session, title: str, content: str) -> dict:
    """Creates a new Google Doc and inserts the given content."""
    service = get_docs_service(user, db)
    
    # 1. Create a blank document
    doc_metadata = {"title": title}
    doc = service.documents().create(body=doc_metadata).execute()
    doc_id = doc.get("documentId")
    
    # 2. Insert content
    if content:
        print(f"[DEBUG] Inserting {len(content)} characters into Google Doc: {doc_id}")
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": content
                }
            }
        ]
        try:
            service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests}
            ).execute()
            print(f"[SUCCESS] Content successfully inserted into doc {doc_id}")
        except Exception as e:
            print(f"[ERROR] Failed to insert content into Google Doc {doc_id}: {str(e)}")
            import traceback
            traceback.print_exc()
        
    doc_link = f"https://docs.google.com/document/d/{doc_id}/edit"
    
    return {
        "doc_id": doc_id,
        "doc_link": doc_link,
        "title": title
    }
