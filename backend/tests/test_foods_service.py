"""
Test suite for foods_service.py
Focus on UpdateFood and GetFoodById functions to improve coverage from 31% to 80%+
"""

import pytest
import uuid
from app.models.schemas import CreateFoodInput, UpdateFoodInput
from app.services.foods_service import (
    GetFoods,
    UpsertFood,
    UpdateFood,
    GetFoodById,
    DeleteFood
)
from app.utils.database import ExecuteQuery
from app.utils.auth import HashPassword


def CreateSecondUser(test_user_id) -> str:
    """Helper to create a second user for unauthorized access tests"""
    User2Id = str(uuid.uuid4())
    ExecuteQuery(
        """
        INSERT INTO Users (
            UserId, Email, FirstName, LastName, PasswordHash, AuthProvider, IsAdmin
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        [User2Id, "user2@example.com", "Test", "User2", HashPassword("Password123"), "Local", 0]
    )
    return User2Id


def test_GetFoods_EmptyList(test_user_id):
    """Test getting foods when none exist"""
    Result = GetFoods(test_user_id)
    assert Result == []


def test_UpsertFood_NewFood(test_user_id):
    """Test creating a new food item"""
    Input = CreateFoodInput(
        FoodName="Apple",
        ServingQuantity=1.0,
        ServingUnit="medium",
        CaloriesPerServing=95,
        ProteinPerServing=0.5,
        IsFavourite=False
    )
    
    Result = UpsertFood(test_user_id, Input)
    
    assert Result.FoodName == "Apple"
    assert Result.ServingQuantity == 1.0
    assert Result.ServingUnit == "medium"
    assert Result.CaloriesPerServing == 95
    assert Result.ProteinPerServing == 0.5
    assert Result.IsFavourite is False
    assert Result.FoodId is not None


def test_UpsertFood_UpdateExisting(test_user_id):
    """Test updating an existing food via upsert"""
    # Create initial food
    Input1 = CreateFoodInput(
        FoodName="Banana",
        ServingQuantity=1.0,
        ServingUnit="large",
        CaloriesPerServing=105,
        ProteinPerServing=1.3,
        IsFavourite=False
    )
    Food1 = UpsertFood(test_user_id, Input1)
    
    # Update with same name
    Input2 = CreateFoodInput(
        FoodName="Banana",
        ServingQuantity=1.0,
        ServingUnit="medium",
        CaloriesPerServing=100,
        ProteinPerServing=1.2,
        IsFavourite=True
    )
    Food2 = UpsertFood(test_user_id, Input2)
    
    # Should update, not create new
    assert Food2.FoodName == "Banana"
    assert Food2.CaloriesPerServing == 100
    assert Food2.IsFavourite is True
    
    # Verify only one exists
    AllFoods = GetFoods(test_user_id)
    assert len(AllFoods) == 1


def test_GetFoodById_Success(test_user_id):
    """Test retrieving a food by ID"""
    Input = CreateFoodInput(
        FoodName="Orange",
        ServingQuantity=1.0,
        ServingUnit="medium",
        CaloriesPerServing=62,
        ProteinPerServing=1.2,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    Retrieved = GetFoodById(test_user_id, Created.FoodId)
    
    assert Retrieved.FoodId == Created.FoodId
    assert Retrieved.FoodName == "Orange"
    assert Retrieved.CaloriesPerServing == 62


def test_GetFoodById_NotFound(test_user_id):
    """Test getting non-existent food raises error"""
    with pytest.raises(ValueError, match="Food not found"):
        GetFoodById(test_user_id, "NonExistentId")


def test_GetFoodById_SharedAccess(test_user_id):
    """Test getting food from different user still returns the food"""
    Input = CreateFoodInput(
        FoodName="Grape",
        ServingQuantity=1.0,
        ServingUnit="cup",
        CaloriesPerServing=104,
        ProteinPerServing=1.1,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    OtherUser = CreateSecondUser(test_user_id)
    Retrieved = GetFoodById(OtherUser, Created.FoodId)
    assert Retrieved.FoodId == Created.FoodId
    assert Retrieved.FoodName == "Grape"


def test_UpdateFood_AllFields(test_user_id):
    """Test updating all fields of a food"""
    # Create initial food
    Input = CreateFoodInput(
        FoodName="Chicken Breast",
        ServingQuantity=100.0,
        ServingUnit="g",
        CaloriesPerServing=165,
        ProteinPerServing=31.0,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    # Update all fields
    UpdateInput = UpdateFoodInput(
        FoodName="Grilled Chicken Breast",
        ServingQuantity=150.0,
        ServingUnit="g",
        CaloriesPerServing=248,
        ProteinPerServing=46.5,
        IsFavourite=True
    )
    Updated = UpdateFood(test_user_id, Created.FoodId, UpdateInput)
    
    assert Updated.FoodName == "Grilled Chicken Breast"
    assert Updated.ServingQuantity == 150.0
    assert Updated.ServingUnit == "g"
    assert Updated.CaloriesPerServing == 248
    assert Updated.ProteinPerServing == 46.5
    assert Updated.IsFavourite is True


def test_UpdateFood_PartialFields(test_user_id):
    """Test updating only some fields"""
    # Create initial food
    Input = CreateFoodInput(
        FoodName="Salmon",
        ServingQuantity=100.0,
        ServingUnit="g",
        CaloriesPerServing=208,
        ProteinPerServing=20.0,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    # Update only calories
    UpdateInput = UpdateFoodInput(
        CaloriesPerServing=220
    )
    Updated = UpdateFood(test_user_id, Created.FoodId, UpdateInput)
    
    # Other fields unchanged
    assert Updated.FoodName == "Salmon"
    assert Updated.ServingQuantity == 100.0
    assert Updated.ServingUnit == "g"
    assert Updated.CaloriesPerServing == 220
    assert Updated.ProteinPerServing == 20.0


def test_UpdateFood_OnlyServingQuantity(test_user_id):
    """Test updating only serving quantity, unit preserved"""
    Input = CreateFoodInput(
        FoodName="Rice",
        ServingQuantity=100.0,
        ServingUnit="g",
        CaloriesPerServing=130,
        ProteinPerServing=2.7,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    UpdateInput = UpdateFoodInput(
        ServingQuantity=150.0
    )
    Updated = UpdateFood(test_user_id, Created.FoodId, UpdateInput)
    
    assert Updated.ServingQuantity == 150.0
    assert Updated.ServingUnit == "g"
    assert Updated.ServingDescription == "150.0 g"


def test_UpdateFood_OnlyServingUnit(test_user_id):
    """Test updating only serving unit, quantity preserved"""
    Input = CreateFoodInput(
        FoodName="Pasta",
        ServingQuantity=2.0,
        ServingUnit="cups",
        CaloriesPerServing=400,
        ProteinPerServing=14.0,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    UpdateInput = UpdateFoodInput(
        ServingUnit="oz"
    )
    Updated = UpdateFood(test_user_id, Created.FoodId, UpdateInput)
    
    assert Updated.ServingQuantity == 2.0
    assert Updated.ServingUnit == "oz"
    assert Updated.ServingDescription == "2.0 oz"


def test_UpdateFood_NoFields(test_user_id):
    """Test update with no fields returns current food"""
    Input = CreateFoodInput(
        FoodName="Bread",
        ServingQuantity=1.0,
        ServingUnit="slice",
        CaloriesPerServing=80,
        ProteinPerServing=2.7,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    UpdateInput = UpdateFoodInput()
    Updated = UpdateFood(test_user_id, Created.FoodId, UpdateInput)
    
    # All fields unchanged
    assert Updated.FoodName == "Bread"
    assert Updated.CaloriesPerServing == 80


def test_UpdateFood_NotFound(test_user_id):
    """Test updating non-existent food raises error"""
    UpdateInput = UpdateFoodInput(
        CaloriesPerServing=100
    )
    
    with pytest.raises(ValueError, match="Food not found"):
        UpdateFood(test_user_id, "NonExistentId", UpdateInput)


def test_UpdateFood_Unauthorized(test_user_id):
    """Test updating food from different user raises error"""
    Input = CreateFoodInput(
        FoodName="Milk",
        ServingQuantity=1.0,
        ServingUnit="cup",
        CaloriesPerServing=149,
        ProteinPerServing=7.7,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    UpdateInput = UpdateFoodInput(
        CaloriesPerServing=150
    )
    
    with pytest.raises(ValueError, match="Unauthorized"):
        UpdateFood(CreateSecondUser(test_user_id), Created.FoodId, UpdateInput)


def test_UpdateFood_ToggleFavourite(test_user_id):
    """Test toggling favourite status"""
    Input = CreateFoodInput(
        FoodName="Yogurt",
        ServingQuantity=1.0,
        ServingUnit="cup",
        CaloriesPerServing=100,
        ProteinPerServing=10.0,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    # Toggle to true
    UpdateInput1 = UpdateFoodInput(IsFavourite=True)
    Updated1 = UpdateFood(test_user_id, Created.FoodId, UpdateInput1)
    assert Updated1.IsFavourite is True
    
    # Toggle back to false
    UpdateInput2 = UpdateFoodInput(IsFavourite=False)
    Updated2 = UpdateFood(test_user_id, Created.FoodId, UpdateInput2)
    assert Updated2.IsFavourite is False


def test_DeleteFood_Success(test_user_id):
    """Test deleting a food"""
    Input = CreateFoodInput(
        FoodName="Cheese",
        ServingQuantity=30.0,
        ServingUnit="g",
        CaloriesPerServing=120,
        ProteinPerServing=7.0,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    DeleteFood(test_user_id, Created.FoodId)
    
    # Verify deleted
    with pytest.raises(ValueError, match="Food not found"):
        GetFoodById(test_user_id, Created.FoodId)


def test_DeleteFood_NotFound(test_user_id):
    """Test deleting non-existent food raises error"""
    with pytest.raises(ValueError, match="Food not found"):
        DeleteFood(test_user_id, "NonExistentId")


def test_DeleteFood_Unauthorized(test_user_id):
    """Test deleting food from different user raises error"""
    Input = CreateFoodInput(
        FoodName="Butter",
        ServingQuantity=1.0,
        ServingUnit="tbsp",
        CaloriesPerServing=102,
        ProteinPerServing=0.1,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    with pytest.raises(ValueError, match="Unauthorized"):
        DeleteFood(CreateSecondUser(test_user_id), Created.FoodId)


def test_GetFoods_MultipleItems(test_user_id):
    """Test getting multiple foods in sorted order"""
    Foods = [
        CreateFoodInput(FoodName="Zebra Cakes", ServingQuantity=1.0, ServingUnit="cake",
                       CaloriesPerServing=320, ProteinPerServing=2.0, IsFavourite=False),
        CreateFoodInput(FoodName="Apple Pie", ServingQuantity=1.0, ServingUnit="slice",
                       CaloriesPerServing=411, ProteinPerServing=4.0, IsFavourite=False),
        CreateFoodInput(FoodName="Mango", ServingQuantity=1.0, ServingUnit="medium",
                       CaloriesPerServing=202, ProteinPerServing=2.8, IsFavourite=True)
    ]
    
    for FoodInput in Foods:
        UpsertFood(test_user_id, FoodInput)
    
    Result = GetFoods(test_user_id)
    
    # Should be sorted by name
    assert len(Result) == 3
    assert Result[0].FoodName == "Apple Pie"
    assert Result[1].FoodName == "Mango"
    assert Result[2].FoodName == "Zebra Cakes"


def test_UpdateFood_ServingDescriptionSync(test_user_id):
    """Test that ServingDescription updates when quantity/unit change"""
    Input = CreateFoodInput(
        FoodName="Oats",
        ServingQuantity=0.5,
        ServingUnit="cup",
        CaloriesPerServing=150,
        ProteinPerServing=5.0,
        IsFavourite=False
    )
    Created = UpsertFood(test_user_id, Input)
    
    # Update both quantity and unit
    UpdateInput = UpdateFoodInput(
        ServingQuantity=1.0,
        ServingUnit="oz"
    )
    Updated = UpdateFood(test_user_id, Created.FoodId, UpdateInput)
    
    assert Updated.ServingDescription == "1.0 oz"
