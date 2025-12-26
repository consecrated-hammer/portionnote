import uuid

import pytest
from starlette.requests import Request

from app.config import Settings
from app.models.schemas import (
    CreateDailyLogInput,
    CreateFoodInput,
    CreateMealEntryInput,
    ApplyMealTemplateInput,
    CreateMealTemplateInput,
    InviteCreateInput,
    LoginInput,
    ScheduleSlotsUpdateInput,
    MealTemplateItemInput,
    MealType,
    RegisterUserInput,
    ScheduleSlotInput,
    StepUpdateInput,
    Suggestion,
    UpdateSettingsInput,
    User
)
from app.routes.ai_suggestions import GetAiSuggestionsRoute
from app.routes.auth import (
    CreateInvite,
    EnsureGoogleConfigured,
    GetCurrentUser,
    GoogleCallback,
    GoogleLogin,
    GooglePending,
    Login,
    Logout,
    Register
)
from app.routes.daily_logs import (
    CreateDailyLogRoute,
    CreateMealEntryRoute,
    DeleteMealEntryRoute,
    GetDailyLog,
    UpdateStepsRoute
)
from app.routes.foods import CreateFood, ListFoods
from app.routes.health import GetHealth
from app.routes.meal_templates import (
    ApplyMealTemplateRoute,
    CreateMealTemplateRoute,
    DeleteMealTemplateRoute,
    ListMealTemplates
)
from app.routes.schedule import ListScheduleSlots, UpdateScheduleSlotsRoute
from app.routes.settings import GetSettingsRoute, UpdateSettingsRoute
from app.routes.summary import GetWeeklySummaryRoute
from app.services.auth_service import CreateInviteForEmail
from app.services.daily_logs_service import UpsertDailyLog
from app.services.foods_service import UpsertFood
from app.utils.auth import HashPassword
from app.utils.database import ExecuteQuery, FetchOne


def CreateUser(Email: str, Password: str | None, IsAdmin: bool) -> str:
    UserId = str(uuid.uuid4())
    ExecuteQuery(
        """
        INSERT INTO Users (
            UserId,
            Email,
            FirstName,
            LastName,
            PasswordHash,
            AuthProvider,
            IsAdmin
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        [
            UserId,
            Email,
            "Test",
            "User",
            HashPassword(Password) if Password else None,
            "Local" if Password else "Google",
            1 if IsAdmin else 0
        ]
    )
    return UserId


def BuildRequest(UserId: str | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "scheme": "http",
        "server": ("testserver", 80),
        "headers": [],
        "session": {"UserId": UserId} if UserId else {}
    }
    return Request(scope)


@pytest.mark.anyio
async def test_health_and_food_routes(temp_db):
    user = User(UserId="User-1", Email="user@example.com", FirstName=None, LastName=None, IsAdmin=False)
    Health = await GetHealth()
    assert Health["Status"] == "ok"

    Food = await CreateFood(
        CreateFoodInput(
            FoodName="Oats",
            ServingDescription="1 bowl",
            CaloriesPerServing=300,
            ProteinPerServing=15,
            IsFavourite=False
        ),
        CurrentUser=user
    )
    assert Food.Food.FoodName == "Oats"

    Foods = await ListFoods(CurrentUser=user)
    assert len(Foods.Foods) == 1


@pytest.mark.anyio
async def test_daily_log_routes(temp_db):
    UserId = CreateUser("loguser@example.com", "Password123", False)
    user = User(UserId=UserId, Email="loguser@example.com", FirstName=None, LastName=None, IsAdmin=False)

    Food = UpsertFood(
        UserId,
        CreateFoodInput(
            FoodName="Salad",
            ServingDescription="1 bowl",
            CaloriesPerServing=250,
            ProteinPerServing=12,
            IsFavourite=False
        )
    )

    LogResponse = await CreateDailyLogRoute(
        CreateDailyLogInput(LogDate="2024-02-01", Steps=1000, StepKcalFactorOverride=None, Notes=None),
        CurrentUser=user
    )
    assert LogResponse.DailyLog.LogDate == "2024-02-01"

    EntryResponse = await CreateMealEntryRoute(
        CreateMealEntryInput(
            DailyLogId=LogResponse.DailyLog.DailyLogId,
            MealType=MealType.Lunch,
            FoodId=Food.FoodId,
            Quantity=1,
            EntryNotes=None,
            SortOrder=0
        ),
        CurrentUser=user
    )
    assert EntryResponse.MealEntry.FoodId == Food.FoodId

    DailyLog = await GetDailyLog("2024-02-01", CurrentUser=user)
    assert DailyLog.Totals.TotalCalories == 250

    Updated = await UpdateStepsRoute(
        "2024-02-01",
        Input=StepUpdateInput(Steps=2500, StepKcalFactorOverride=None),
        CurrentUser=user
    )
    assert Updated.DailyLog.Steps == 2500

    await DeleteMealEntryRoute(EntryResponse.MealEntry.MealEntryId, CurrentUser=user)


@pytest.mark.anyio
async def test_schedule_and_settings_routes(temp_db):
    UserId = CreateUser("settings@example.com", "Password123", False)
    user = User(UserId=UserId, Email="settings@example.com", FirstName=None, LastName=None, IsAdmin=False)

    UpdatedSchedule = await UpdateScheduleSlotsRoute(
        Input=ScheduleSlotsUpdateInput(
            Slots=[
                ScheduleSlotInput(
                    SlotName="Breakfast",
                    SlotTime="07:30",
                    MealType=MealType.Breakfast,
                    SortOrder=0
                )
            ]
        ),
        CurrentUser=user
    )
    assert len(UpdatedSchedule.Slots) == 1

    ListedSchedule = await ListScheduleSlots(CurrentUser=user)
    assert ListedSchedule.Slots[0].SlotName == "Breakfast"

    UpdatedSettings = await UpdateSettingsRoute(
        UpdateSettingsInput(DailyCalorieTarget=1600, StepTarget=9000),
        CurrentUser=user
    )
    assert UpdatedSettings.Targets.StepTarget == 9000

    Loaded = await GetSettingsRoute(CurrentUser=user)
    assert Loaded.Targets.DailyCalorieTarget == 1600


@pytest.mark.anyio
async def test_meal_template_routes(temp_db):
    UserId = CreateUser("meal@example.com", "Password123", False)
    user = User(UserId=UserId, Email="meal@example.com", FirstName=None, LastName=None, IsAdmin=False)

    Food = UpsertFood(
        UserId,
        CreateFoodInput(
            FoodName="Eggs",
            ServingDescription="2 eggs",
            CaloriesPerServing=180,
            ProteinPerServing=12,
            IsFavourite=False
        )
    )

    Template = await CreateMealTemplateRoute(
        Input=CreateMealTemplateInput(
            TemplateName="Test template",
            Items=[
                MealTemplateItemInput(
                    FoodId=Food.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=1,
                    EntryNotes=None,
                    SortOrder=0
                )
            ]
        ),
        CurrentUser=user
    )
    assert Template.Template.Template.TemplateName == "Test template"

    Templates = await ListMealTemplates(CurrentUser=user)
    assert len(Templates.Templates) == 1

    await ApplyMealTemplateRoute(
        Template.Template.Template.MealTemplateId,
        Input=ApplyMealTemplateInput(LogDate="2024-02-02"),
        CurrentUser=user
    )
    await DeleteMealTemplateRoute(Template.Template.Template.MealTemplateId, CurrentUser=user)


@pytest.mark.anyio
async def test_summary_route(temp_db):
    UserId = CreateUser("summary@example.com", "Password123", False)
    user = User(UserId=UserId, Email="summary@example.com", FirstName=None, LastName=None, IsAdmin=False)

    Food = UpsertFood(
        UserId,
        CreateFoodInput(
            FoodName="Wrap",
            ServingDescription="1 wrap",
            CaloriesPerServing=400,
            ProteinPerServing=25,
            IsFavourite=False
        )
    )

    LogOne = UpsertDailyLog(
        UserId,
        CreateDailyLogInput(LogDate="2024-02-03", Steps=1000, StepKcalFactorOverride=None, Notes=None)
    )
    LogTwo = UpsertDailyLog(
        UserId,
        CreateDailyLogInput(LogDate="2024-02-04", Steps=1200, StepKcalFactorOverride=None, Notes=None)
    )

    await CreateMealEntryRoute(
        CreateMealEntryInput(
            DailyLogId=LogOne.DailyLogId,
            MealType=MealType.Lunch,
            FoodId=Food.FoodId,
            Quantity=1,
            EntryNotes=None,
            SortOrder=0
        ),
        CurrentUser=user
    )
    await CreateMealEntryRoute(
        CreateMealEntryInput(
            DailyLogId=LogTwo.DailyLogId,
            MealType=MealType.Dinner,
            FoodId=Food.FoodId,
            Quantity=2,
            EntryNotes=None,
            SortOrder=0
        ),
        CurrentUser=user
    )

    Summary = await GetWeeklySummaryRoute(StartDate="2024-02-03", CurrentUser=user)
    assert Summary.WeeklySummary.Totals["TotalCalories"] == 1200


@pytest.mark.anyio
async def test_auth_routes_basic(temp_db):
    AdminId = CreateUser("admin@example.com", "AdminPassword123", True)
    admin = User(UserId=AdminId, Email="admin@example.com", FirstName=None, LastName=None, IsAdmin=True)
    request = BuildRequest(AdminId)

    Invite = await CreateInvite(
        InviteCreateInput(Email="invitee@gmail.com"),
        RequestValue=request,
        AdminUser=admin
    )
    assert Invite.InviteEmail == "invitee@gmail.com"

    RegisterRequest = BuildRequest()
    UserItem = await Register(
        RegisterUserInput(
            Email="invitee@gmail.com",
            Password="Password123",
            FirstName="Invited",
            LastName="User",
            InviteCode=Invite.InviteCode
        ),
        RequestValue=RegisterRequest
    )
    assert RegisterRequest.session.get("UserId") == UserItem.User.UserId

    LoginRequest = BuildRequest()
    LoggedIn = await Login(
        LoginInput(Email="admin@example.com", Password="AdminPassword123"),
        RequestValue=LoginRequest
    )
    assert LoggedIn.User.UserId == AdminId
    assert LoginRequest.session.get("UserId") == AdminId

    Current = await GetCurrentUser(LoginRequest)
    assert Current.User.Email == "admin@example.com"

    Pending = await GooglePending(BuildRequest())
    assert Pending.HasPending is False

    LogoutRequest = BuildRequest(AdminId)
    await Logout(LogoutRequest)
    assert LogoutRequest.session == {}


@pytest.mark.anyio
async def test_google_flow_routes(temp_db, monkeypatch):
    OriginalClientId = Settings.GoogleClientId
    OriginalClientSecret = Settings.GoogleClientSecret
    OriginalRedirect = Settings.GoogleRedirectUrl
    OriginalOrigin = Settings.WebOrigin
    Settings.GoogleClientId = "test-client"
    Settings.GoogleClientSecret = "test-secret"
    Settings.GoogleRedirectUrl = "http://testserver/api/auth/google/callback"
    Settings.WebOrigin = "http://testserver"

    AdminId = CreateUser("admin2@example.com", "AdminPassword123", True)
    InviteRow = CreateInviteForEmail("googleuser@gmail.com", AdminId)

    class DummyGoogleClient:
        async def authorize_redirect(self, _request, _redirect_url):
            return {"redirect": _redirect_url}

        async def authorize_access_token(self, _request):
            return {
                "userinfo": {
                    "email": "googleuser@gmail.com",
                    "sub": "sub-123",
                    "given_name": "G",
                    "family_name": "User"
                }
            }

        async def parse_id_token(self, _request, _token):
            return {"email": "googleuser@gmail.com", "sub": "sub-123"}

    def DummyRegister(*_args, **_kwargs):
        OAuthClient._registry["google"] = {}

    from app.routes.auth import OAuthClient

    OAuthClient._clients = {}
    OAuthClient._registry = {}
    monkeypatch.setattr(OAuthClient, "register", DummyRegister)
    monkeypatch.setattr(OAuthClient, "create_client", lambda _key: DummyGoogleClient())

    request = BuildRequest()
    request.session["InviteCode"] = InviteRow["InviteCode"]
    EnsureGoogleConfigured()

    await GoogleLogin(request, InviteCode=InviteRow["InviteCode"])

    CallbackRequest = BuildRequest()
    CallbackRequest.session["InviteCode"] = InviteRow["InviteCode"]
    Response = await GoogleCallback(CallbackRequest)
    assert Response.status_code == 307

    Row = FetchOne(
        "SELECT UserId AS UserId FROM Users WHERE Email = ?;",
        ["googleuser@gmail.com"]
    )
    assert Row is not None

    Settings.GoogleClientId = OriginalClientId
    Settings.GoogleClientSecret = OriginalClientSecret
    Settings.GoogleRedirectUrl = OriginalRedirect
    Settings.WebOrigin = OriginalOrigin


@pytest.mark.anyio
async def test_ai_suggestions_route(monkeypatch, temp_db):
    user = User(UserId="User-2", Email="ai@example.com", FirstName=None, LastName=None, IsAdmin=False)

    def DummySuggestions(_user_id, _log_date):
        return [Suggestion(SuggestionType="AiSuggestion", Title="Test", Detail="Detail")], "gpt-5-mini"

    monkeypatch.setattr("app.routes.ai_suggestions.GetAiSuggestions", DummySuggestions)

    Response = await GetAiSuggestionsRoute(LogDate="2024-02-01", CurrentUser=user)
    assert Response.Suggestions[0].Title == "Test"
