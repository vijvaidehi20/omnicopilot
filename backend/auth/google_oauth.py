"""
Google OAuth 2.0 routes for OmniCopilot.
Handles redirect to Google and the code exchange in the callback.
"""
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from database import get_db
from models import User
from auth.utils import create_access_token

from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/auth/google", tags=["Google OAuth"])

# Scopes required for Phase 2 + Docs
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents"
]

# Google credentials from .env
# Important: Redirect URI must match what's in Google Console
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")


@router.get("/login")
def login_google():
    """Start the Google OAuth flow."""
    if not CLIENT_CONFIG["web"]["client_id"] or CLIENT_CONFIG["web"]["client_id"] == "your_client_id":
        raise HTTPException(status_code=500, detail="Google Client ID not configured. Please add a valid GOOGLE_CLIENT_ID to .env")
        
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    # access_type='offline' is required to get a refresh_token
    # prompt='consent' ensures a refresh_token is returned during development
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def callback_google(request: Request, db: Session = Depends(get_db)):
    """Handle Callback from Google after authorization."""
    try:
        print("AUTH RESPONSE URL:", request.url)
        
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # Exchange code for tokens using full URL to handle errors gracefully
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials
        
        # Verify the ID token to get user info (email, sub)
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            CLIENT_CONFIG["web"]["client_id"]
        )
        
        email = id_info.get("email")
        google_id = id_info.get("sub")
        
        if not email:
            raise HTTPException(status_code=400, detail="Could not retrieve email from Google")

        # Find or create user
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            # Check if user with same email exists
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(email=email, google_id=google_id)
                db.add(user)
            else:
                user.google_id = google_id
                
        # Update tokens
        user.google_access_token = credentials.token
        if credentials.refresh_token:
            user.google_refresh_token = credentials.refresh_token
        
        # Ensure expiry is timezone-aware if possible, here we convert to UTC datetime
        user.google_token_expiry = credentials.expiry

        db.commit()
        db.refresh(user)

        # Issue OmniCopilot JWT
        token = create_access_token(user_id=user.id, email=user.email)
        
        # Redirect back to frontend with the token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/auth/success?token={token}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
