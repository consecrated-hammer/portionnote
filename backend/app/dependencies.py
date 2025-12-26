from fastapi import HTTPException, Request

from app.models.schemas import User
from app.services.auth_service import GetUserFromRequest


def RequireUser(Request: Request) -> User:
    UserItem = GetUserFromRequest(Request)
    if UserItem is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return UserItem


def RequireAdmin(Request: Request) -> User:
    UserItem = RequireUser(Request)
    if not UserItem.IsAdmin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return UserItem
