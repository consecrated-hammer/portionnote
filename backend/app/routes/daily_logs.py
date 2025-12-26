from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.dependencies import RequireUser
from app.models.schemas import (
    CreateDailyLogInput,
    CreateMealEntryInput,
    DailyLog,
    DailySummary,
    DailyTotals,
    MealEntry,
    MealEntryWithFood,
    StepUpdateInput,
    Targets,
    User
)
from app.services.calculations_service import BuildDailySummary, CalculateDailyTotals
from app.services.daily_logs_service import (
    CreateMealEntry,
    DeleteMealEntry,
    GetDailyLogByDate,
    GetEntriesForLog,
    GetSettings,
    UpdateSteps,
    UpsertDailyLog
)

DailyLogRouter = APIRouter()


class DailyLogResponse(BaseModel):
    DailyLog: Optional[DailyLog]
    Entries: list[MealEntryWithFood]
    Totals: DailyTotals
    Summary: DailySummary
    Targets: Targets


class DailyLogCreateResponse(BaseModel):
    DailyLog: DailyLog


class MealEntryResponse(BaseModel):
    MealEntry: MealEntry


@DailyLogRouter.post("/", response_model=DailyLogCreateResponse, status_code=201, tags=["DailyLogs"])
async def CreateDailyLogRoute(Input: CreateDailyLogInput, CurrentUser: User = Depends(RequireUser)):
    try:
        DailyLogItem = UpsertDailyLog(CurrentUser.UserId, Input)
        return DailyLogCreateResponse(DailyLog=DailyLogItem)
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to create daily log.") from ErrorValue


@DailyLogRouter.get("/{LogDate}", response_model=DailyLogResponse, tags=["DailyLogs"])
async def GetDailyLog(LogDate: str, CurrentUser: User = Depends(RequireUser)):
    DailyLogItem = GetDailyLogByDate(CurrentUser.UserId, LogDate)
    Settings = GetSettings(CurrentUser.UserId)
    
    if DailyLogItem is None:
        # Return 200 with empty data - no log exists yet for this date
        EmptyTotals = CalculateDailyTotals([], 0, Settings.StepKcalFactor, Settings)
        EmptySummary = BuildDailySummary(LogDate, 0, EmptyTotals)
        return DailyLogResponse(
            DailyLog=None,
            Entries=[],
            Totals=EmptyTotals,
            Summary=EmptySummary,
            Targets=Settings
        )

    Entries = GetEntriesForLog(CurrentUser.UserId, DailyLogItem.DailyLogId)
    StepFactor = (
        DailyLogItem.StepKcalFactorOverride
        if DailyLogItem.StepKcalFactorOverride is not None
        else Settings.StepKcalFactor
    )

    Totals = CalculateDailyTotals(
        Entries,
        DailyLogItem.Steps,
        StepFactor,
        Settings
    )

    Summary = BuildDailySummary(DailyLogItem.LogDate, DailyLogItem.Steps, Totals)

    return DailyLogResponse(
        DailyLog=DailyLogItem,
        Entries=Entries,
        Totals=Totals,
        Summary=Summary,
        Targets=Settings
    )


@DailyLogRouter.patch("/{LogDate}/steps", response_model=DailyLogCreateResponse, tags=["DailyLogs"])
async def UpdateStepsRoute(LogDate: str, Input: StepUpdateInput, CurrentUser: User = Depends(RequireUser)):
    try:
        DailyLogItem = UpdateSteps(
            CurrentUser.UserId,
            LogDate,
            Input.Steps,
            Input.StepKcalFactorOverride,
            Input.WeightKg
        )
        return DailyLogCreateResponse(DailyLog=DailyLogItem)
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to update steps.") from ErrorValue


@DailyLogRouter.post("/meal-entries", response_model=MealEntryResponse, status_code=201, tags=["DailyLogs"])
async def CreateMealEntryRoute(Input: CreateMealEntryInput, CurrentUser: User = Depends(RequireUser)):
    try:
        MealEntryItem = CreateMealEntry(CurrentUser.UserId, Input)
        return MealEntryResponse(MealEntry=MealEntryItem)
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to create meal entry.") from ErrorValue


@DailyLogRouter.delete("/meal-entries/{MealEntryId}", status_code=204, tags=["DailyLogs"])
async def DeleteMealEntryRoute(MealEntryId: str, CurrentUser: User = Depends(RequireUser)):
    try:
        DeleteMealEntry(CurrentUser.UserId, MealEntryId)
        return Response(status_code=204)
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to delete meal entry.") from ErrorValue
