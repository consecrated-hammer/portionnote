from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.dependencies import RequireUser
from app.models.schemas import User, WeeklySummary
from app.services.summary_service import GetWeeklySummary

SummaryRouter = APIRouter()


class WeeklySummaryResponse(BaseModel):
    WeeklySummary: WeeklySummary


@SummaryRouter.get("/weekly", response_model=WeeklySummaryResponse, tags=["Summary"])
async def GetWeeklySummaryRoute(
    StartDate: str = Query(..., min_length=1),
    CurrentUser: User = Depends(RequireUser)
):
    try:
        Summary = GetWeeklySummary(CurrentUser.UserId, StartDate)
        return WeeklySummaryResponse(WeeklySummary=Summary)
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to load weekly summary.") from ErrorValue
