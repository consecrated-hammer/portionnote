from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import Settings
from app.dependencies import RequireAdmin
from app.models.schemas import (
    InviteCompleteInput,
    InviteCreateInput,
    InviteResponse,
    LoginInput,
    PendingGoogleInviteResponse,
    RegisterUserInput,
    UpdateProfileInput,
    User
)
from app.services.auth_service import (
    AuthenticateUser,
    CreateInviteForEmail,
    GetUserFromRequest,
    RegisterGoogleUser,
    RegisterLocalUser
)
from app.utils.seed import EnsureSettingsForUser, SeedFoodsForUser

AuthRouter = APIRouter()
OAuthClient = OAuth()


class UserResponse(BaseModel):
    User: User


def EnsureGoogleConfigured() -> None:
    if not Settings.GoogleClientId or not Settings.GoogleClientSecret:
        raise HTTPException(status_code=400, detail="Google auth not configured.")

    Clients = getattr(OAuthClient, "_clients", {})
    if "google" not in Clients:
        OAuthClient.register(
            name="google",
            client_id=Settings.GoogleClientId,
            client_secret=Settings.GoogleClientSecret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"}
        )


@AuthRouter.get("/me", response_model=UserResponse, tags=["Auth"])
async def GetCurrentUser(RequestValue: Request):
    UserItem = GetUserFromRequest(RequestValue)
    if UserItem is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return UserResponse(User=UserItem)


@AuthRouter.post("/register", response_model=UserResponse, status_code=201, tags=["Auth"])
async def Register(Input: RegisterUserInput, RequestValue: Request):
    try:
        UserItem, Created = RegisterLocalUser(
            Email=Input.Email,
            Password=Input.Password,
            FirstName=Input.FirstName,
            LastName=Input.LastName,
            InviteCode=Input.InviteCode
        )
        if Created:
            EnsureSettingsForUser(UserItem.UserId)
            SeedFoodsForUser(UserItem.UserId)
        RequestValue.session["UserId"] = UserItem.UserId
        return UserResponse(User=UserItem)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue


@AuthRouter.post("/login", response_model=UserResponse, tags=["Auth"])
async def Login(Input: LoginInput, RequestValue: Request):
    try:
        UserItem = AuthenticateUser(Input.Email, Input.Password)
        RequestValue.session["UserId"] = UserItem.UserId
        return UserResponse(User=UserItem)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue


@AuthRouter.post("/logout", tags=["Auth"])
async def Logout(RequestValue: Request):
    RequestValue.session.clear()
    return {"Status": "ok"}


@AuthRouter.post("/invites", response_model=InviteResponse, status_code=201, tags=["Auth"])
async def CreateInvite(
    Input: InviteCreateInput,
    RequestValue: Request,
    AdminUser: User = Depends(RequireAdmin)
):
    try:
        InviteRow = CreateInviteForEmail(Input.Email, AdminUser.UserId)
        BaseUrl = str(RequestValue.base_url).rstrip("/")
        InviteUrl = f"{BaseUrl}/api/auth/google/login?InviteCode={InviteRow['InviteCode']}"
        return InviteResponse(
            InviteCode=InviteRow["InviteCode"],
            InviteEmail=InviteRow["InviteEmail"],
            InviteUrl=InviteUrl,
            CreatedAt=InviteRow.get("CreatedAt")
        )
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue


@AuthRouter.get("/google/pending", response_model=PendingGoogleInviteResponse, tags=["Auth"])
async def GooglePending(RequestValue: Request):
    Pending = RequestValue.session.get("PendingGoogle")
    if Pending is None:
        RequestValue.session.pop("PendingGoogleError", None)
        return PendingGoogleInviteResponse(HasPending=False)

    return PendingGoogleInviteResponse(
        HasPending=True,
        Email=Pending.get("Email"),
        Error=RequestValue.session.get("PendingGoogleError")
    )


@AuthRouter.post("/google/complete", response_model=UserResponse, tags=["Auth"])
async def GoogleComplete(Input: InviteCompleteInput, RequestValue: Request):
    Pending = RequestValue.session.get("PendingGoogle")
    if Pending is None:
        raise HTTPException(status_code=400, detail="Google session expired.")

    try:
        UserItem, Created = RegisterGoogleUser(
            Email=Pending["Email"],
            FirstName=Pending.get("FirstName"),
            LastName=Pending.get("LastName"),
            GoogleSubject=Pending["Subject"],
            InviteCode=Input.InviteCode
        )
        if Created:
            EnsureSettingsForUser(UserItem.UserId)
            SeedFoodsForUser(UserItem.UserId)
        RequestValue.session["UserId"] = UserItem.UserId
        RequestValue.session.pop("PendingGoogle", None)
        RequestValue.session.pop("PendingGoogleError", None)
        return UserResponse(User=UserItem)
    except ValueError as ErrorValue:
        RequestValue.session["PendingGoogleError"] = str(ErrorValue)
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue


@AuthRouter.get("/google/login", tags=["Auth"])
async def GoogleLogin(RequestValue: Request, InviteCode: str | None = None):
    EnsureGoogleConfigured()
    if InviteCode and InviteCode.strip():
        RequestValue.session["InviteCode"] = InviteCode.strip()
    else:
        RequestValue.session.pop("InviteCode", None)

    RedirectUrl = Settings.GoogleRedirectUrl
    if not RedirectUrl:
        RedirectUrl = str(RequestValue.url_for("GoogleCallback"))

    return await OAuthClient.google.authorize_redirect(RequestValue, RedirectUrl)


@AuthRouter.get("/google/callback", tags=["Auth"], name="GoogleCallback")
async def GoogleCallback(RequestValue: Request):
    EnsureGoogleConfigured()
    try:
        Token = await OAuthClient.google.authorize_access_token(RequestValue)
    except OAuthError as ErrorValue:
        raise HTTPException(status_code=400, detail="Google authentication failed.") from ErrorValue

    UserInfo = Token.get("userinfo")
    if UserInfo is None:
        UserInfo = await OAuthClient.google.parse_id_token(RequestValue, Token)

    Email = UserInfo.get("email") if UserInfo else None
    Subject = UserInfo.get("sub") if UserInfo else None

    if not Email or not Subject:
        raise HTTPException(status_code=400, detail="Google authentication failed.")

    InviteCode = RequestValue.session.pop("InviteCode", None)

    try:
        UserItem, Created = RegisterGoogleUser(
            Email=Email,
            FirstName=UserInfo.get("given_name") if UserInfo else None,
            LastName=UserInfo.get("family_name") if UserInfo else None,
            GoogleSubject=Subject,
            InviteCode=InviteCode
        )
        if Created:
            EnsureSettingsForUser(UserItem.UserId)
            SeedFoodsForUser(UserItem.UserId)
        RequestValue.session["UserId"] = UserItem.UserId
        RequestValue.session.pop("PendingGoogle", None)
        RequestValue.session.pop("PendingGoogleError", None)
    except ValueError as ErrorValue:
        ErrorMessage = str(ErrorValue)
        if "Invite" in ErrorMessage:
            RequestValue.session["PendingGoogle"] = {
                "Email": Email,
                "FirstName": UserInfo.get("given_name") if UserInfo else None,
                "LastName": UserInfo.get("family_name") if UserInfo else None,
                "Subject": Subject
            }
            RequestValue.session["PendingGoogleError"] = ErrorMessage
            Target = f"{Settings.WebOrigin}/auth?invite=1"
            return RedirectResponse(url=Target)

        RequestValue.session["PendingGoogleError"] = ErrorMessage
        Target = f"{Settings.WebOrigin}/auth?error=1"
        return RedirectResponse(url=Target)

    Target = f"{Settings.WebOrigin}/today"
    return RedirectResponse(url=Target)


@AuthRouter.patch("/profile", response_model=UserResponse, tags=["Auth"])
async def UpdateProfile(Input: UpdateProfileInput, RequestValue: Request):
    """Update user profile information (name, birthdate, height, weight)."""
    UserItem = GetUserFromRequest(RequestValue)
    if UserItem is None:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    
    from app.utils.database import GetConnection
    
    UpdateFields = []
    Params: dict = {"UserId": UserItem.UserId}
    
    if Input.FirstName is not None:
        UpdateFields.append("FirstName = :FirstName")
        Params["FirstName"] = Input.FirstName
    if Input.LastName is not None:
        UpdateFields.append("LastName = :LastName")
        Params["LastName"] = Input.LastName
    if Input.BirthDate is not None:
        UpdateFields.append("BirthDate = :BirthDate")
        Params["BirthDate"] = Input.BirthDate
    if Input.HeightCm is not None:
        UpdateFields.append("HeightCm = :HeightCm")
        Params["HeightCm"] = Input.HeightCm
    if Input.WeightKg is not None:
        UpdateFields.append("WeightKg = :WeightKg")
        Params["WeightKg"] = Input.WeightKg
    if Input.ActivityLevel is not None:
        UpdateFields.append("ActivityLevel = :ActivityLevel")
        Params["ActivityLevel"] = Input.ActivityLevel
    
    if not UpdateFields:
        return UserResponse(User=UserItem)
    
    Query = f"UPDATE Users SET {', '.join(UpdateFields)} WHERE UserId = :UserId"
    
    Db = GetConnection()
    Cursor = Db.cursor()
    try:
        Cursor.execute(Query, Params)
        Db.commit()
        
        # Fetch updated user
        Row = Cursor.execute(
            "SELECT UserId, Email, FirstName, LastName, BirthDate, HeightCm, WeightKg, ActivityLevel, IsAdmin FROM Users WHERE UserId = ?",
            [UserItem.UserId]
        ).fetchone()
        
        if not Row:
            raise HTTPException(status_code=404, detail="User not found after update.")
        
        UpdatedUser = User(
            UserId=Row[0],
            Email=Row[1],
            FirstName=Row[2],
            LastName=Row[3],
            BirthDate=Row[4],
            HeightCm=Row[5],
            WeightKg=Row[6],
            ActivityLevel=Row[7],
            IsAdmin=bool(Row[8])
        )
        
        return UserResponse(User=UpdatedUser)
    finally:
        Cursor.close()

