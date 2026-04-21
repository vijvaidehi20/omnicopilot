"""
Reminder Service with APScheduler.
"""
from datetime import datetime
import pytz
IST = pytz.timezone("Asia/Kolkata")

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Reminder, User

# We don't technically need a persistent JobStore if our polling script checks the DB explicitly, 
# but a polling script is simpler and doesn't require complex DB migrations for job stores.

"""
Reminder Service with APScheduler.
"""
from datetime import datetime
import pytz
IST = pytz.timezone("Asia/Kolkata")

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from models import Reminder, User

scheduler = BackgroundScheduler(timezone=IST)

def start_scheduler():
    """Start the background scheduler."""
    scheduler.start()
    print("[INFO] Background reminder scheduler started.")

def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown()
    print("[INFO] Background reminder scheduler stopped.")

def send_reminder(user_id: int, message: str, reminder_id: int):
    from database import SessionLocal
    from services.gmail_service import send_email
    from models import Notification
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Create notification record
            notification = Notification(
                user_id=user.id,
                message=message
            )
            db.add(notification)
            
            # Send email
            send_email(user, db, user.email, "OmniCopilot Reminder", message)
            print(f"⏰ [REMINDER ALARM] Created notification and sent email to {user.email}: {message}")
            
        rem = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if rem:
            rem.is_sent = 1
            db.commit()
    except Exception as e:
        print(f"Error executing reminder: {e}")
    finally:
        db.close()

def schedule_reminder(user: User, db: Session, message: str, scheduled_time: datetime):
    """Inserts a new reminder into the database and schedules an exact trigger email."""
    rem = Reminder(
        user_id=user.id,
        message=message,
        scheduled_time=scheduled_time,
        is_sent=0
    )
    db.add(rem)
    db.commit()
    db.refresh(rem)
    
    scheduler.add_job(
        send_reminder,
        'date',
        run_date=scheduled_time,
        args=[user.id, message, rem.id],
        id=f"rem_{rem.id}"
    )
    
    print(f"[INFO] New Reminder Scheduled: {message} at {scheduled_time}")
    return rem
