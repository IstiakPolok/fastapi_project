import random
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.config import settings
from app.models.otp import OTP
from app.models.user import User


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


async def send_otp_email(email: str, otp_code: str):
    """Send OTP to user's email"""
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Password Reset OTP"
    message["From"] = settings.FROM_EMAIL
    message["To"] = email
    
    # Create the HTML content
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4CAF50;">Password Reset OTP</h2>
            <p>You requested to reset your password. Use the OTP below to proceed:</p>
            <div style="background-color: #f4f4f4; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <h1 style="color: #333; letter-spacing: 5px; text-align: center;">{otp_code}</h1>
            </div>
            <p>This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes.</p>
            <p style="color: #666;">If you didn't request this, please ignore this email.</p>
        </body>
    </html>
    """
    
    html_part = MIMEText(html, "html")
    message.attach(html_part)
    
    # Send email
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True
        )
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")


def create_otp(db: Session, user_id: int) -> str:
    """Create and store OTP in database"""
    # Delete any existing unused OTPs for this user
    db.query(OTP).filter(OTP.user_id == user_id, OTP.is_used == False).delete()
    
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    db_otp = OTP(
        user_id=user_id,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False
    )
    db.add(db_otp)
    db.commit()
    
    return otp_code


def verify_otp(db: Session, user: User, otp_code: str) -> bool:
    """Verify OTP for a user"""
    otp = db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.otp_code == otp_code,
        OTP.is_used == False
    ).first()
    
    if not otp:
        return False
    
    # Check if OTP is expired
    if datetime.utcnow() > otp.expires_at:
        return False
    
    # Mark OTP as used
    otp.is_used = True
    db.commit()
    
    return True
