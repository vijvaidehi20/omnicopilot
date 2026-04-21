"""
Service for interacting with Google Calendar API.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import User
from services.google_api_factory import get_calendar_service
import dateparser
import pytz

IST = pytz.timezone("Asia/Kolkata")


def create_calendar_event(user: User, db: Session, title: str, date_str: str, time_str: str = "", attendees: list = None):
    """Create a real event in Google Calendar with a Meet link."""
    service = get_calendar_service(user, db)
    
    # Parse date/time
    full_input = f"{date_str} {time_str}".strip()
    parsed_dt = dateparser.parse(
        full_input, 
        settings={
            'PREFER_DATES_FROM': 'future', 
            'RELATIVE_BASE': datetime.now(IST),
            'TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True
        }
    )
    
    if not parsed_dt:
        raise Exception(f"Could not parse date/time: {full_input}")

    # Set duration to 1 hour by default
    start_time = parsed_dt.isoformat()
    end_time = (parsed_dt + timedelta(hours=1)).isoformat()

    event_body = {
        'summary': title,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Kolkata',
        },
        'conferenceData': {
            'createRequest': {
                'requestId': f"meet-{int(datetime.now().timestamp())}"
            }
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 0},
                {'method': 'email', 'minutes': 5},
            ],
        }
    }

    # Add attendees if provided
    if attendees:
        event_body['attendees'] = [{"email": email.strip()} for email in attendees if email.strip()]

    event = service.events().insert(
        calendarId='primary', 
        body=event_body,
        conferenceDataVersion=1,
        sendUpdates='all' if attendees else 'none'
    ).execute()

    return {
        "event_id": event.get("id"),
        "html_link": event.get("htmlLink"),
        "meet_link": event.get("hangoutLink"),
        "start_time": start_time,
        "title": title,
        "attendees": [a.get("email") for a in event.get("attendees", [])]
    }


def update_calendar_event(user: User, db: Session, event_id: str, title: str = None, 
                          date_str: str = None, time_str: str = None, attendees: list = None):
    """Update an existing Google Calendar event using PATCH (not recreate)."""
    service = get_calendar_service(user, db)
    
    # Fetch current event to merge data
    current_event = service.events().get(calendarId='primary', eventId=event_id).execute()
    
    patch_body = {}
    
    # Update title if provided
    if title:
        patch_body['summary'] = title
    
    # Update time if provided
    if date_str or time_str:
        full_input = f"{date_str or ''} {time_str or ''}".strip()
        if full_input:
            parsed_dt = dateparser.parse(
                full_input,
                settings={
                    'PREFER_DATES_FROM': 'future', 
                    'RELATIVE_BASE': datetime.now(IST),
                    'TIMEZONE': 'Asia/Kolkata',
                    'RETURN_AS_TIMEZONE_AWARE': True
                }
            )
            if parsed_dt:
                patch_body['start'] = {
                    'dateTime': parsed_dt.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                }
                patch_body['end'] = {
                    'dateTime': (parsed_dt + timedelta(hours=1)).isoformat(),
                    'timeZone': 'Asia/Kolkata',
                }
    
    # Merge attendees (add new ones to existing)
    if attendees:
        existing_attendees = current_event.get('attendees', [])
        existing_emails = {a.get('email') for a in existing_attendees}
        for email in attendees:
            email = email.strip()
            if email and email not in existing_emails:
                existing_attendees.append({"email": email})
                existing_emails.add(email)
        patch_body['attendees'] = existing_attendees
    
    if not patch_body:
        return {
            "event_id": event_id,
            "message": "No changes to apply.",
            "title": current_event.get("summary", ""),
            "start_time": current_event.get("start", {}).get("dateTime", ""),
            "meet_link": current_event.get("hangoutLink", ""),
            "html_link": current_event.get("htmlLink", ""),
            "attendees": [a.get("email") for a in current_event.get("attendees", [])]
        }
    
    updated_event = service.events().patch(
        calendarId='primary',
        eventId=event_id,
        body=patch_body,
        conferenceDataVersion=1,
        sendUpdates='all' if attendees else 'none'
    ).execute()
    
    return {
        "event_id": updated_event.get("id"),
        "html_link": updated_event.get("htmlLink"),
        "meet_link": updated_event.get("hangoutLink"),
        "start_time": updated_event.get("start", {}).get("dateTime", ""),
        "title": updated_event.get("summary", ""),
        "attendees": [a.get("email") for a in updated_event.get("attendees", [])]
    }
