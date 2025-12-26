from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import RequireUser
from app.models.schemas import ScheduleSlotsResponse, ScheduleSlotsUpdateInput, User
from app.services.schedule_service import GetScheduleSlots, UpdateScheduleSlots

ScheduleRouter = APIRouter()


@ScheduleRouter.get("/", response_model=ScheduleSlotsResponse, tags=["Schedule"])
async def ListScheduleSlots(CurrentUser: User = Depends(RequireUser)):
    Slots = GetScheduleSlots(CurrentUser.UserId)
    return ScheduleSlotsResponse(Slots=Slots)


@ScheduleRouter.put("/", response_model=ScheduleSlotsResponse, tags=["Schedule"])
async def UpdateScheduleSlotsRoute(
    Input: ScheduleSlotsUpdateInput,
    CurrentUser: User = Depends(RequireUser)
):
    try:
        Slots = UpdateScheduleSlots(CurrentUser.UserId, Input.Slots)
        return ScheduleSlotsResponse(Slots=Slots)
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to update schedule.") from ErrorValue
