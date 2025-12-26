"""
Tests for OpenFoodFacts service integration.
"""

import pytest
from app.services.openfoodfacts_service import OpenFoodFactsService


@pytest.mark.asyncio
async def TestSearchProducts():
    """Test searching for products on OpenFoodFacts."""
    Results = await OpenFoodFactsService.SearchProducts("bega crunchy", PageSize=5)
    
    assert isinstance(Results, list)
    assert len(Results) > 0
    
    # Check first result has expected fields
    FirstResult = Results[0]
    assert FirstResult.FoodName is not None
    assert FirstResult.ServingDescription is not None
    assert FirstResult.CaloriesPerServing is not None or FirstResult.ProteinPerServing is not None
    
    # Check metadata
    assert FirstResult.Metadata is not None
    assert FirstResult.Metadata.get("source") == "openfoodfacts"
    assert "barcode" in FirstResult.Metadata


@pytest.mark.asyncio
async def TestGetProductByBarcode():
    """Test getting a specific product by barcode."""
    # Bega Peanut Butter Crunchy 470g
    Barcode = "9352042002827"
    
    Result = await OpenFoodFactsService.GetProductByBarcode(Barcode)
    
    assert Result is not None
    assert "Bega" in Result.FoodName or "bega" in Result.FoodName.lower()
    assert Result.CaloriesPerServing is not None
    assert Result.ProteinPerServing is not None
    assert Result.Metadata is not None
    assert Result.Metadata.get("source") == "openfoodfacts"
    assert Result.Metadata.get("barcode") == Barcode


@pytest.mark.asyncio
async def TestGetProductByBarcodeNotFound():
    """Test getting a product with invalid barcode."""
    # Invalid barcode
    Barcode = "0000000000000"
    
    Result = await OpenFoodFactsService.GetProductByBarcode(Barcode)
    
    assert Result is None


@pytest.mark.asyncio
async def TestParseProductWithCompleteData():
    """Test parsing product data with all nutrition fields."""
    ProductData = {
        "code": "1234567890123",
        "product_name": "Test Product",
        "brands": "Test Brand",
        "serving_size": "30g",
        "serving_quantity": 30,
        "image_url": "https://example.com/image.jpg",
        "nutriments": {
            "energy-kcal_100g": 500,
            "proteins_100g": 20,
            "fat_100g": 30,
            "saturated-fat_100g": 10,
            "carbohydrates_100g": 40,
            "sugars_100g": 5,
            "fiber_100g": 10,
            "sodium_100g": 0.5
        }
    }
    
    Result = OpenFoodFactsService._ParseProduct(ProductData)
    
    assert Result is not None
    assert Result.FoodName == "Test Brand Test Product"
    assert Result.ServingDescription == "30g"
    assert Result.CaloriesPerServing == 150  # 500 * 0.3
    assert Result.ProteinPerServing == 6.0  # 20 * 0.3
    assert Result.FatPerServing == 9.0  # 30 * 0.3
    assert Result.Metadata is not None
    assert Result.Metadata.get("barcode") == "1234567890123"


@pytest.mark.asyncio
async def TestParseProductWithMissingNutrition():
    """Test parsing product data with missing nutrition fields."""
    ProductData = {
        "code": "1234567890123",
        "product_name": "Test Product",
        "brands": "Test Brand",
        "nutriments": {
            "energy-kcal_100g": 100
        }
    }
    
    Result = OpenFoodFactsService._ParseProduct(ProductData)
    
    assert Result is not None
    assert Result.FoodName == "Test Brand Test Product"
    assert Result.CaloriesPerServing == 100
    assert Result.ProteinPerServing is None
    assert Result.FatPerServing is None


@pytest.mark.asyncio
async def TestParseProductWithoutName():
    """Test parsing product data without a name returns None."""
    ProductData = {
        "code": "1234567890123",
        "brands": "Test Brand",
        "nutriments": {
            "energy-kcal_100g": 100
        }
    }
    
    Result = OpenFoodFactsService._ParseProduct(ProductData)
    
    assert Result is None
