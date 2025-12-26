from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.dependencies import RequireUser
from app.models.schemas import (
    ApplyMealTemplateInput,
    ApplyMealTemplateResponse,
    CreateMealTemplateInput,
    UpdateMealTemplateInput,
    MealTemplateListResponse,
    MealTemplateWithItems,
    MealTextParseInput,
    MealTextParseResponse,
    User
)
from app.services.meal_templates_service import (
    ApplyMealTemplate,
    CreateMealTemplate,
    DeleteMealTemplate,
    UpdateMealTemplate,
    GetMealTemplates
)
from app.services.meal_text_parse_service import ParseMealText

MealTemplateRouter = APIRouter()


class MealTemplateResponse(BaseModel):
    Template: MealTemplateWithItems


@MealTemplateRouter.get("", response_model=MealTemplateListResponse, tags=["MealTemplates"])
@MealTemplateRouter.get("/", response_model=MealTemplateListResponse, tags=["MealTemplates"])
async def ListMealTemplates(CurrentUser: User = Depends(RequireUser)):
    Templates = GetMealTemplates(CurrentUser.UserId)
    return MealTemplateListResponse(Templates=Templates)


@MealTemplateRouter.post("/ai-parse", response_model=MealTextParseResponse, tags=["MealTemplates"])
async def ParseMealTextRoute(Input: MealTextParseInput, CurrentUser: User = Depends(RequireUser)):
    try:
        Totals = ParseMealText(Input.Text, Input.KnownFoods)
        return MealTextParseResponse(**Totals)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to parse meal entry.") from ErrorValue


@MealTemplateRouter.post("", response_model=MealTemplateResponse, status_code=201, tags=["MealTemplates"])
@MealTemplateRouter.post("/", response_model=MealTemplateResponse, status_code=201, tags=["MealTemplates"])
async def CreateMealTemplateRoute(
    Input: CreateMealTemplateInput,
    CurrentUser: User = Depends(RequireUser)
):
    try:
        Template = CreateMealTemplate(CurrentUser.UserId, Input)
        return MealTemplateResponse(Template=Template)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue


@MealTemplateRouter.delete("/{MealTemplateId}", status_code=204, tags=["MealTemplates"])
async def DeleteMealTemplateRoute(
    MealTemplateId: str,
    CurrentUser: User = Depends(RequireUser)
):
    try:
        DeleteMealTemplate(CurrentUser.UserId, MealTemplateId, IsAdmin=CurrentUser.IsAdmin)
        return Response(status_code=204)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue


@MealTemplateRouter.patch("/{MealTemplateId}", response_model=MealTemplateResponse, tags=["MealTemplates"])
async def UpdateMealTemplateRoute(
    MealTemplateId: str,
    Input: UpdateMealTemplateInput,
    CurrentUser: User = Depends(RequireUser)
):
    try:
        Template = UpdateMealTemplate(CurrentUser.UserId, MealTemplateId, Input, IsAdmin=CurrentUser.IsAdmin)
        return MealTemplateResponse(Template=Template)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue


@MealTemplateRouter.post("/{MealTemplateId}/apply", response_model=ApplyMealTemplateResponse, tags=["MealTemplates"])
async def ApplyMealTemplateRoute(
    MealTemplateId: str,
    Input: ApplyMealTemplateInput,
    CurrentUser: User = Depends(RequireUser)
):
    try:
        return ApplyMealTemplate(CurrentUser.UserId, MealTemplateId, Input.LogDate)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue
