import uuid

from app.models.schemas import CreateFoodInput, Food, UpdateFoodInput
from app.utils.database import ExecuteQuery, FetchAll, FetchOne


def GetFoods(UserId: str) -> list[Food]:
    Rows = FetchAll(
        """
        SELECT
            UserId,
            FoodId, FoodName, ServingDescription, ServingQuantity, ServingUnit,
            CaloriesPerServing, ProteinPerServing,
            FibrePerServing, CarbsPerServing, FatPerServing,
            SaturatedFatPerServing, SugarPerServing, SodiumPerServing,
            DataSource, CountryCode, IsFavourite, CreatedAt
        FROM Foods
        ORDER BY FoodName ASC;
        """
    )

    Foods: list[Food] = []
    for Row in Rows:
        Foods.append(
            Food(
                FoodId=Row["FoodId"],
                OwnerUserId=Row["UserId"],
                FoodName=Row["FoodName"],
                ServingDescription=Row["ServingDescription"],
                ServingQuantity=float(Row["ServingQuantity"]) if Row["ServingQuantity"] else 1.0,
                ServingUnit=Row["ServingUnit"] or "serving",
                CaloriesPerServing=int(Row["CaloriesPerServing"]),
                ProteinPerServing=float(Row["ProteinPerServing"]),
                FibrePerServing=float(Row["FibrePerServing"]) if Row["FibrePerServing"] else None,
                CarbsPerServing=float(Row["CarbsPerServing"]) if Row["CarbsPerServing"] else None,
                FatPerServing=float(Row["FatPerServing"]) if Row["FatPerServing"] else None,
                SaturatedFatPerServing=float(Row["SaturatedFatPerServing"]) if Row["SaturatedFatPerServing"] else None,
                SugarPerServing=float(Row["SugarPerServing"]) if Row["SugarPerServing"] else None,
                SodiumPerServing=float(Row["SodiumPerServing"]) if Row["SodiumPerServing"] else None,
                DataSource=Row["DataSource"] or "manual",
                CountryCode=Row["CountryCode"] or "AU",
                IsFavourite=bool(Row["IsFavourite"]),
                CreatedAt=Row["CreatedAt"]
            )
        )
    return Foods


def UpsertFood(UserId: str, Input: CreateFoodInput) -> Food:
    FoodId = str(uuid.uuid4())
    
    # Build serving description from quantity + unit for backwards compatibility
    ServingDescription = f"{Input.ServingQuantity} {Input.ServingUnit}"

    ExecuteQuery(
        """
        INSERT INTO Foods (
            FoodId, UserId, FoodName, ServingDescription,
            ServingQuantity, ServingUnit,
            CaloriesPerServing, ProteinPerServing,
            FibrePerServing, CarbsPerServing, FatPerServing,
            SaturatedFatPerServing, SugarPerServing, SodiumPerServing,
            DataSource, CountryCode, IsFavourite
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (UserId, FoodName)
        DO UPDATE SET
            ServingDescription = excluded.ServingDescription,
            ServingQuantity = excluded.ServingQuantity,
            ServingUnit = excluded.ServingUnit,
            CaloriesPerServing = excluded.CaloriesPerServing,
            ProteinPerServing = excluded.ProteinPerServing,
            FibrePerServing = excluded.FibrePerServing,
            CarbsPerServing = excluded.CarbsPerServing,
            FatPerServing = excluded.FatPerServing,
            SaturatedFatPerServing = excluded.SaturatedFatPerServing,
            SugarPerServing = excluded.SugarPerServing,
            SodiumPerServing = excluded.SodiumPerServing,
            DataSource = excluded.DataSource,
            CountryCode = excluded.CountryCode,
            IsFavourite = excluded.IsFavourite;
        """,
        [
            FoodId, UserId, Input.FoodName, ServingDescription,
            Input.ServingQuantity, Input.ServingUnit,
            Input.CaloriesPerServing, Input.ProteinPerServing,
            Input.FibrePerServing, Input.CarbsPerServing, Input.FatPerServing,
            Input.SaturatedFatPerServing, Input.SugarPerServing, Input.SodiumPerServing,
            Input.DataSource, Input.CountryCode,
            1 if Input.IsFavourite else 0
        ]
    )

    Row = FetchOne(
        """
        SELECT
            FoodId, UserId, FoodName, ServingDescription, ServingQuantity, ServingUnit,
            CaloriesPerServing, ProteinPerServing,
            FibrePerServing, CarbsPerServing, FatPerServing,
            SaturatedFatPerServing, SugarPerServing, SodiumPerServing,
            DataSource, CountryCode, IsFavourite
        FROM Foods
        WHERE FoodName = ? AND UserId = ?;
        """,
        [Input.FoodName, UserId]
    )

    if Row is None:
        raise ValueError("Failed to load created food.")

    return Food(
        FoodId=Row["FoodId"],
        OwnerUserId=Row["UserId"],
        FoodName=Row["FoodName"],
        ServingDescription=Row["ServingDescription"],
        ServingQuantity=float(Row["ServingQuantity"]) if Row["ServingQuantity"] else 1.0,
        ServingUnit=Row["ServingUnit"] or "serving",
        CaloriesPerServing=int(Row["CaloriesPerServing"]),
        ProteinPerServing=float(Row["ProteinPerServing"]),
        FibrePerServing=float(Row["FibrePerServing"]) if Row["FibrePerServing"] else None,
        CarbsPerServing=float(Row["CarbsPerServing"]) if Row["CarbsPerServing"] else None,
        FatPerServing=float(Row["FatPerServing"]) if Row["FatPerServing"] else None,
        SaturatedFatPerServing=float(Row["SaturatedFatPerServing"]) if Row["SaturatedFatPerServing"] else None,
        SugarPerServing=float(Row["SugarPerServing"]) if Row["SugarPerServing"] else None,
        SodiumPerServing=float(Row["SodiumPerServing"]) if Row["SodiumPerServing"] else None,
        DataSource=Row["DataSource"] or "manual",
        CountryCode=Row["CountryCode"] or "AU",
        IsFavourite=bool(Row["IsFavourite"])
    )


def UpdateFood(UserId: str, FoodId: str, Input: UpdateFoodInput, IsAdmin: bool = False) -> Food:
    # Get existing food to verify ownership
    ExistingRow = FetchOne(
        "SELECT UserId FROM Foods WHERE FoodId = ?;",
        [FoodId]
    )
    
    if ExistingRow is None:
        raise ValueError("Food not found")
    
    if ExistingRow["UserId"] != UserId and not IsAdmin:
        raise ValueError("Unauthorized")
    
    # Build update query dynamically based on provided fields
    UpdateFields = []
    Values = []
    
    if Input.FoodName is not None:
        UpdateFields.append("FoodName = ?")
        Values.append(Input.FoodName)
    
    if Input.ServingQuantity is not None or Input.ServingUnit is not None:
        # Need to get current values if only one is being updated
        CurrentRow = FetchOne(
            "SELECT ServingQuantity, ServingUnit FROM Foods WHERE FoodId = ?;",
            [FoodId]
        )
        NewQuantity = Input.ServingQuantity if Input.ServingQuantity is not None else float(CurrentRow["ServingQuantity"])
        NewUnit = Input.ServingUnit if Input.ServingUnit is not None else CurrentRow["ServingUnit"]
        
        UpdateFields.append("ServingQuantity = ?")
        UpdateFields.append("ServingUnit = ?")
        UpdateFields.append("ServingDescription = ?")
        Values.extend([NewQuantity, NewUnit, f"{NewQuantity} {NewUnit}"])
    
    if Input.CaloriesPerServing is not None:
        UpdateFields.append("CaloriesPerServing = ?")
        Values.append(Input.CaloriesPerServing)
    
    if Input.ProteinPerServing is not None:
        UpdateFields.append("ProteinPerServing = ?")
        Values.append(Input.ProteinPerServing)
    
    if Input.FibrePerServing is not None:
        UpdateFields.append("FibrePerServing = ?")
        Values.append(Input.FibrePerServing)
    
    if Input.CarbsPerServing is not None:
        UpdateFields.append("CarbsPerServing = ?")
        Values.append(Input.CarbsPerServing)
    
    if Input.FatPerServing is not None:
        UpdateFields.append("FatPerServing = ?")
        Values.append(Input.FatPerServing)
    
    if Input.SaturatedFatPerServing is not None:
        UpdateFields.append("SaturatedFatPerServing = ?")
        Values.append(Input.SaturatedFatPerServing)
    
    if Input.SugarPerServing is not None:
        UpdateFields.append("SugarPerServing = ?")
        Values.append(Input.SugarPerServing)
    
    if Input.SodiumPerServing is not None:
        UpdateFields.append("SodiumPerServing = ?")
        Values.append(Input.SodiumPerServing)
    
    if Input.IsFavourite is not None:
        UpdateFields.append("IsFavourite = ?")
        Values.append(1 if Input.IsFavourite else 0)
    
    if not UpdateFields:
        # No fields to update, just return current food
        return GetFoodById(UserId, FoodId)
    
    Values.append(FoodId)
    ExecuteQuery(
        f"UPDATE Foods SET {', '.join(UpdateFields)} WHERE FoodId = ?;",
        Values
    )
    
    return GetFoodById(UserId, FoodId)


def GetFoodById(UserId: str, FoodId: str) -> Food:
    Row = FetchOne(
        """
        SELECT
            FoodId, UserId, FoodName, ServingDescription, ServingQuantity, ServingUnit,
            CaloriesPerServing, ProteinPerServing,
            FibrePerServing, CarbsPerServing, FatPerServing,
            SaturatedFatPerServing, SugarPerServing, SodiumPerServing,
            DataSource, CountryCode, IsFavourite
        FROM Foods
        WHERE FoodId = ?;
        """,
        [FoodId]
    )
    
    if Row is None:
        raise ValueError("Food not found")
    
    return Food(
        FoodId=Row["FoodId"],
        OwnerUserId=Row["UserId"],
        FoodName=Row["FoodName"],
        ServingDescription=Row["ServingDescription"],
        ServingQuantity=float(Row["ServingQuantity"]) if Row["ServingQuantity"] else 1.0,
        ServingUnit=Row["ServingUnit"] or "serving",
        CaloriesPerServing=int(Row["CaloriesPerServing"]),
        ProteinPerServing=float(Row["ProteinPerServing"]),
        FibrePerServing=float(Row["FibrePerServing"]) if Row["FibrePerServing"] else None,
        CarbsPerServing=float(Row["CarbsPerServing"]) if Row["CarbsPerServing"] else None,
        FatPerServing=float(Row["FatPerServing"]) if Row["FatPerServing"] else None,
        SaturatedFatPerServing=float(Row["SaturatedFatPerServing"]) if Row["SaturatedFatPerServing"] else None,
        SugarPerServing=float(Row["SugarPerServing"]) if Row["SugarPerServing"] else None,
        SodiumPerServing=float(Row["SodiumPerServing"]) if Row["SodiumPerServing"] else None,
        DataSource=Row["DataSource"] or "manual",
        CountryCode=Row["CountryCode"] or "AU",
        IsFavourite=bool(Row["IsFavourite"])
    )


def DeleteFood(UserId: str, FoodId: str, IsAdmin: bool = False) -> None:
    # Verify ownership
    ExistingRow = FetchOne(
        "SELECT UserId FROM Foods WHERE FoodId = ?;",
        [FoodId]
    )
    
    if ExistingRow is None:
        raise ValueError("Food not found")
    
    if ExistingRow["UserId"] != UserId and not IsAdmin:
        raise ValueError("Unauthorized")

    MealEntryCount = FetchOne(
        "SELECT COUNT(1) AS Count FROM MealEntries WHERE FoodId = ?;",
        [FoodId]
    )["Count"]
    TemplateItemCount = FetchOne(
        "SELECT COUNT(1) AS Count FROM MealTemplateItems WHERE FoodId = ?;",
        [FoodId]
    )["Count"]
    if MealEntryCount > 0 or TemplateItemCount > 0:
        Parts: list[str] = []
        if MealEntryCount > 0:
            Parts.append(f"{MealEntryCount} log entries")
        if TemplateItemCount > 0:
            Parts.append(f"{TemplateItemCount} meal templates")
        Usage = " and ".join(Parts)
        raise ValueError(f"Food is used in {Usage}. Remove it from those items before deleting.")

    ExecuteQuery(
        "DELETE FROM Foods WHERE FoodId = ?;",
        [FoodId]
    )
