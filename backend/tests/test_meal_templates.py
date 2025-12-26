from app.models.schemas import CreateFoodInput, CreateMealTemplateInput, UpdateMealTemplateInput, MealTemplateItemInput, MealType
from app.services.daily_logs_service import GetDailyLogByDate, GetEntriesForLog
from app.services.foods_service import UpsertFood
from app.services.meal_templates_service import ApplyMealTemplate, CreateMealTemplate, UpdateMealTemplate, DeleteMealTemplate, GetMealTemplates


def test_create_apply_delete_template(test_user_id):
    FoodOne = UpsertFood(
        test_user_id,
        CreateFoodInput(
            FoodName="Weet-Bix",
            ServingDescription="1 biscuit",
            CaloriesPerServing=64,
            ProteinPerServing=2.7,
            IsFavourite=False
        )
    )
    FoodTwo = UpsertFood(
        test_user_id,
        CreateFoodInput(
            FoodName="Light Milk",
            ServingDescription="1/2 cup",
            CaloriesPerServing=44,
            ProteinPerServing=4.3,
            IsFavourite=False
        )
    )

    Template = CreateMealTemplate(
        test_user_id,
        CreateMealTemplateInput(
            TemplateName="Monday breakfast",
            Items=[
                MealTemplateItemInput(
                    FoodId=FoodOne.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=3,
                    EntryNotes="",
                    SortOrder=0
                ),
                MealTemplateItemInput(
                    FoodId=FoodTwo.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=1,
                    EntryNotes=None,
                    SortOrder=1
                )
            ]
        )
    )

    assert Template.Template.TemplateName == "Monday breakfast"
    assert len(Template.Items) == 2

    Templates = GetMealTemplates(test_user_id)
    assert len(Templates) == 1

    ApplyResult = ApplyMealTemplate(test_user_id, Template.Template.MealTemplateId, "2024-01-05")
    assert ApplyResult.CreatedCount == 2

    LogItem = GetDailyLogByDate(test_user_id, "2024-01-05")
    assert LogItem is not None

    Entries = GetEntriesForLog(test_user_id, LogItem.DailyLogId)
    assert len(Entries) == 2

    DeleteMealTemplate(test_user_id, Template.Template.MealTemplateId)
    TemplatesAfter = GetMealTemplates(test_user_id)
    assert TemplatesAfter == []


def test_update_meal_template(test_user_id):
    """Test updating meal template name and items"""
    FoodOne = UpsertFood(
        test_user_id,
        CreateFoodInput(
            FoodName="Banana",
            ServingQuantity=1.0,
            ServingUnit="medium",
            CaloriesPerServing=105,
            ProteinPerServing=1.3,
            IsFavourite=False
        )
    )
    FoodTwo = UpsertFood(
        test_user_id,
        CreateFoodInput(
            FoodName="Yogurt",
            ServingQuantity=1.0,
            ServingUnit="cup",
            CaloriesPerServing=100,
            ProteinPerServing=10.0,
            IsFavourite=False
        )
    )
    FoodThree = UpsertFood(
        test_user_id,
        CreateFoodInput(
            FoodName="Granola",
            ServingQuantity=0.5,
            ServingUnit="cup",
            CaloriesPerServing=150,
            ProteinPerServing=4.0,
            IsFavourite=False
        )
    )

    # Create initial template
    Template = CreateMealTemplate(
        test_user_id,
        CreateMealTemplateInput(
            TemplateName="Simple breakfast",
            Items=[
                MealTemplateItemInput(
                    FoodId=FoodOne.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=1,
                    EntryNotes=None,
                    SortOrder=0
                )
            ]
        )
    )

    assert Template.Template.TemplateName == "Simple breakfast"
    assert len(Template.Items) == 1

    # Update template name only
    UpdatedTemplate = UpdateMealTemplate(
        test_user_id,
        Template.Template.MealTemplateId,
        UpdateMealTemplateInput(TemplateName="Better breakfast")
    )
    assert UpdatedTemplate.Template.TemplateName == "Better breakfast"
    assert len(UpdatedTemplate.Items) == 1

    # Update template items
    UpdatedTemplate2 = UpdateMealTemplate(
        test_user_id,
        Template.Template.MealTemplateId,
        UpdateMealTemplateInput(
            Items=[
                MealTemplateItemInput(
                    FoodId=FoodTwo.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=1,
                    EntryNotes=None,
                    SortOrder=0
                ),
                MealTemplateItemInput(
                    FoodId=FoodThree.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=1,
                    EntryNotes=None,
                    SortOrder=1
                )
            ]
        )
    )
    assert len(UpdatedTemplate2.Items) == 2
    assert UpdatedTemplate2.Items[0].FoodName == "Yogurt"
    assert UpdatedTemplate2.Items[1].FoodName == "Granola"

    # Update both name and items
    UpdatedTemplate3 = UpdateMealTemplate(
        test_user_id,
        Template.Template.MealTemplateId,
        UpdateMealTemplateInput(
            TemplateName="Complete breakfast",
            Items=[
                MealTemplateItemInput(
                    FoodId=FoodOne.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=2,
                    EntryNotes=None,
                    SortOrder=0
                ),
                MealTemplateItemInput(
                    FoodId=FoodTwo.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=1,
                    EntryNotes=None,
                    SortOrder=1
                ),
                MealTemplateItemInput(
                    FoodId=FoodThree.FoodId,
                    MealType=MealType.Breakfast,
                    Quantity=0.5,
                    EntryNotes=None,
                    SortOrder=2
                )
            ]
        )
    )
    assert UpdatedTemplate3.Template.TemplateName == "Complete breakfast"
    assert len(UpdatedTemplate3.Items) == 3

