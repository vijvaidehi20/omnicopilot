"""
Factory service for creating authorized Google API clients.
Handles token refresh if the access token has expired.
"""
import os
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from sqlalchemy.orm import Session
from models import User

# Google client info
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_google_credentials(user: User, db: Session) -> Credentials:
    """Get authorized Google Credentials for a user, refreshing if needed."""
    if not user.google_access_token:
        raise Exception("User has not connected their Google account.")

    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        expiry=user.google_token_expiry
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
        # Save updated tokens back to DB
        user.google_access_token = creds.token
        user.google_token_expiry = creds.expiry
        db.commit()
        db.refresh(user)

    return creds


def build_google_service(user: User, db: Session, service_name: str, version: str):
    """Build and return a Google API discovery service."""
    creds = get_google_credentials(user, db)
    return build(service_name, version, credentials=creds)


def get_calendar_service(user: User, db: Session):
    return build_google_service(user, db, 'calendar', 'v3')


def get_gmail_service(user: User, db: Session):
    return build_google_service(user, db, 'gmail', 'v1')


def get_drive_service(user: User, db: Session):
    return build_google_service(user, db, 'drive', 'v3')


def get_docs_service(user: User, db: Session):
    return build_google_service(user, db, 'docs', 'v1')
