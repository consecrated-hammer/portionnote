from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import RequireUser
from app.models.schemas import SuggestionsResponse, User
from app.services.ai_suggestions_service import GetAiSuggestions

AiSuggestionRouter = APIRouter()


@AiSuggestionRouter.get("/ai", response_model=SuggestionsResponse, tags=["Suggestions"])
async def GetAiSuggestionsRoute(LogDate: str | None = None, CurrentUser: User = Depends(RequireUser)):
    try:
        TargetDate = LogDate or date.today().isoformat()
        Suggestions, ModelUsed = GetAiSuggestions(CurrentUser.UserId, TargetDate)
        return SuggestionsResponse(Suggestions=Suggestions, ModelUsed=ModelUsed)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue
    except Exception as ErrorValue:
        raise HTTPException(status_code=502, detail="AI suggestions failed.") from ErrorValue
