from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import RequireAdmin
from app.models.schemas import (
    AdminUserCreateInput,
    AdminUserListResponse,
    AdminUserSummary,
    AdminUserUpdateInput,
    User
)
from app.services.admin_users_service import CreateLocalUser, ListUsers, UpdateUserAdmin
from app.utils.seed import EnsureSettingsForUser, SeedFoodsForUser

AdminUserRouter = APIRouter()


class AdminUserResponse(BaseModel):
    User: AdminUserSummary


@AdminUserRouter.get("/users", response_model=AdminUserListResponse, tags=["AdminUsers"])
async def ListAdminUsers(AdminUser: User = Depends(RequireAdmin)):
    Users = ListUsers()
    return AdminUserListResponse(Users=Users)


@AdminUserRouter.post("/users", response_model=AdminUserResponse, status_code=201, tags=["AdminUsers"])
async def CreateAdminUser(Input: AdminUserCreateInput, AdminUser: User = Depends(RequireAdmin)):
    try:
        Created = CreateLocalUser(
            Email=Input.Email,
            Password=Input.Password,
            FirstName=Input.FirstName,
            LastName=Input.LastName,
            IsAdmin=Input.IsAdmin
        )
        EnsureSettingsForUser(Created.UserId)
        SeedFoodsForUser(Created.UserId)
        return AdminUserResponse(User=Created)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue


@AdminUserRouter.patch("/users/{UserId}", response_model=AdminUserResponse, tags=["AdminUsers"])
async def UpdateAdminUser(UserId: str, Input: AdminUserUpdateInput, AdminUser: User = Depends(RequireAdmin)):
    try:
        Updated = UpdateUserAdmin(UserId, Input.IsAdmin)
        return AdminUserResponse(User=Updated)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue
