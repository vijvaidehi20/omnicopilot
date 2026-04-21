"""
Service for interacting with Google Drive API and processing files.
"""
import io
import pandas as pd
from PyPDF2 import PdfReader
from sqlalchemy.orm import Session
from models import User
from services.google_api_factory import get_drive_service
from googleapiclient.http import MediaIoBaseDownload


def list_drive_files(user: User, db: Session, count: int = 10):
    """Fetch recent files from Google Drive."""
    service = get_drive_service(user, db)
    
    # Get 10 most recent files
    results = service.files().list(
        q="trashed = false",
        orderBy="modifiedTime desc",
        pageSize=count,
        fields="files(id, name, mimeType)"
    ).execute()
    
    files = results.get('files', [])
    return [{"name": f["name"], "file_id": f["id"], "type": f["mimeType"]} for f in files]


def fetch_drive_file(user: User, db: Session, file_id: str):
    """Download file content by file_id."""
    service = get_drive_service(user, db)
    
    # Get file metadata to determine type and name
    file_metadata = service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
    mime_type = file_metadata['mimeType']
    name = file_metadata['name']
    
    # Download content
    if mime_type == 'application/vnd.google-apps.document':
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        mime_type = 'text/plain'
    else:
        request = service.files().get_media(fileId=file_id)
        
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        
    file_stream.seek(0)
    return file_stream, name, mime_type


def extract_text_from_file(file_stream, mime_type):
    """Extract readable text based on mime type."""
    text_content = ""
    
    if mime_type == 'application/pdf':
        reader = PdfReader(file_stream)
        # Limiting to first few pages for context window safety
        for page in reader.pages[:10]:
            text_content += page.extract_text() + "\n"
            
    elif mime_type == 'text/csv':
        df = pd.read_csv(file_stream)
        text_content = df.to_string(index=False)
        
    elif mime_type in ['text/plain', 'application/json', 'text/markdown']:
        text_content = file_stream.read().decode('utf-8', errors='ignore')
        
    else:
        raise Exception(f"Unsupported file type for processing: {mime_type}")
        
    # Standard truncation to fit LLM window (approx 5000 chars for summarization)
    return text_content[:15000] 
