from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from backend.database import SessionLocal
from backend.models import User, SessionRecord
from backend.schemas.auth import LoginRequest, AuthMeResponse
from backend.core.password import verify_password
from backend.core.config import settings
from backend.core.security import get_current_user
from backend.core.auth_provider import AuthenticatedUser
from itsdangerous import URLSafeTimedSerializer

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger(__name__)

    # 1. Find user
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        logger.warning(f"Failed login attempt for unknown user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 2. Verify password
    if not verify_password(request.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 3. Check active
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # 4. Create session record
    session_id = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(hours=settings.session_expiry_hours)
    
    session_record = SessionRecord(
        id=session_id,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(session_record)
    db.commit()
    
    # 5. Sign session ID and set cookie
    signer = URLSafeTimedSerializer(settings.session_secret_key)
    signed_session = signer.dumps(session_id)
    
    response.set_cookie(
        key="aaroh_session",
        value=signed_session,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.session_expiry_hours * 3600,
        path="/"
    )
    
    # 6. CSRF token for double submit
    csrf_token = secrets.token_hex(32)
    response.set_cookie(
        key="aaroh_csrf_token",
        value=csrf_token,
        httponly=False,  # So JS can read it for the header
        secure=settings.secure_cookies,
        samesite="strict",
        path="/"
    )
    
    return {"user": {"username": user.username, "role": user.role}}


@router.get("/me", response_model=AuthMeResponse)
def get_me(user: AuthenticatedUser = Depends(get_current_user)):
    return user


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    cookie = request.cookies.get("aaroh_session")
    if cookie:
        signer = URLSafeTimedSerializer(settings.session_secret_key)
        try:
            session_id = signer.loads(cookie, max_age=settings.session_expiry_hours * 3600)
            session_record = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
            if session_record:
                session_record.is_active = False
                db.commit()
        except Exception:
            pass # Invalid cookie, just clear it
    
    response.delete_cookie("aaroh_session", path="/")
    response.delete_cookie("aaroh_csrf_token", path="/")
    
    return {"status": "ok"}
