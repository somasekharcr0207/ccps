import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer),
                     db: Session = Depends(get_db)) -> User:
    """Validates the JWT issued by the Django service."""
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing token",
                                 headers={"WWW-Authenticate": "Bearer"})
    if creds is None:
        raise unauthorized
    try:
        payload = jwt.decode(creds.credentials, settings.JWT_SIGNING_KEY,
                             algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise unauthorized
    if payload.get("token_type") != "access" or "user_id" not in payload:
        raise unauthorized
    user = db.scalar(select(User).where(User.id == int(payload["user_id"])))
    if user is None or not user.is_active:
        raise unauthorized
    return user
