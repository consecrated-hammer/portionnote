from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import RequireUser
from app.models.schemas import CreateFoodInput, Food, UpdateFoodInput, User
from app.services.foods_service import DeleteFood, GetFoods, UpdateFood, UpsertFood

FoodRouter = APIRouter()


class FoodListResponse(BaseModel):
    Foods: list[Food]


class FoodResponse(BaseModel):
    Food: Food


@FoodRouter.get("/", response_model=FoodListResponse, tags=["Foods"])
async def ListFoods(CurrentUser: User = Depends(RequireUser)):
    try:
        Foods = GetFoods(CurrentUser.UserId)
        return FoodListResponse(Foods=Foods)
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to load foods.") from ErrorValue


@FoodRouter.post("/", response_model=FoodResponse, status_code=201, tags=["Foods"])
async def CreateFood(Input: CreateFoodInput, CurrentUser: User = Depends(RequireUser)):
    try:
        FoodItem = UpsertFood(CurrentUser.UserId, Input)
        return FoodResponse(Food=FoodItem)
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to create food.") from ErrorValue


@FoodRouter.patch("/{FoodId}", response_model=FoodResponse, tags=["Foods"])
async def EditFood(FoodId: str, Input: UpdateFoodInput, CurrentUser: User = Depends(RequireUser)):
    try:
        FoodItem = UpdateFood(CurrentUser.UserId, FoodId, Input)
        return FoodResponse(Food=FoodItem)
    except ValueError as ErrorValue:
        raise HTTPException(status_code=404, detail=str(ErrorValue)) from ErrorValue
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to update food.") from ErrorValue


@FoodRouter.delete("/{FoodId}", status_code=204, tags=["Foods"])
async def RemoveFood(FoodId: str, CurrentUser: User = Depends(RequireUser)):
    try:
        DeleteFood(CurrentUser.UserId, FoodId)
    except ValueError as ErrorValue:
        Message = str(ErrorValue)
        if Message == "Food not found":
            raise HTTPException(status_code=404, detail=Message) from ErrorValue
        if Message == "Unauthorized":
            raise HTTPException(status_code=403, detail=Message) from ErrorValue
        raise HTTPException(status_code=400, detail=Message) from ErrorValue
    except Exception as ErrorValue:
        raise HTTPException(status_code=400, detail="Failed to delete food.") from ErrorValue
