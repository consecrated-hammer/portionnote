"""Tests for food lookup service (AI text, image, barcode)."""
import json
from unittest.mock import Mock, patch

import pytest

from app.config import Settings
from app.services.food_lookup_service import (
    FoodLookupResult,
    LookupFoodByBarcode,
    LookupFoodByImage,
    LookupFoodByText,
    LookupFoodByTextOptions
)


def test_food_lookup_result_to_dict():
    """Test FoodLookupResult.ToDict() method."""
    Result = FoodLookupResult(
        FoodName="Banana",
        ServingQuantity=1.0,
        ServingUnit="medium",
        CaloriesPerServing=105,
        ProteinPerServing=1.3,
        FibrePerServing=3.1,
        CarbsPerServing=27.0,
        Source="Test",
        Confidence="High"
    )
    
    Dict = Result.ToDict()
    assert Dict["FoodName"] == "Banana"
    assert Dict["CaloriesPerServing"] == 105
    assert Dict["ProteinPerServing"] == 1.3
    assert Dict["FibrePerServing"] == 3.1
    assert Dict["Source"] == "Test"
    assert Dict["Confidence"] == "High"


def test_lookup_food_by_text_no_api_key():
    """Test that LookupFoodByText raises error when API key not configured."""
    OriginalKey = Settings.OpenAiApiKey
    Settings.OpenAiApiKey = None
    
    try:
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            LookupFoodByText("banana")
    finally:
        Settings.OpenAiApiKey = OriginalKey


@patch("app.services.food_lookup_service.httpx.post")
def test_lookup_food_by_text_success(MockPost):
    """Test successful text-based food lookup."""
    # Mock OpenAI API response
    MockResponse = Mock()
    MockResponse.status_code = 200
    MockResponse.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "FoodName": "Weet-Bix",
                    "ServingQuantity": 2.0,
                    "ServingUnit": "biscuits",
                    "CaloriesPerServing": 136,
                    "ProteinPerServing": 4.6,
                    "FibrePerServing": 3.6,
                    "CarbsPerServing": 24.0,
                    "FatPerServing": 1.2,
                    "SaturatedFatPerServing": 0.3,
                    "SugarPerServing": 3.8,
                    "SodiumPerServing": 75.0,
                    "Confidence": "High"
                })
            }
        }]
    }
    MockPost.return_value = MockResponse
    
    Result = LookupFoodByText("weet-bix")
    
    assert Result.FoodName == "Weet-Bix"
    assert Result.CaloriesPerServing == 136
    assert Result.ProteinPerServing == 4.6
    assert Result.ServingUnit == "biscuits"
    assert Result.Source == "AI-Text"
    assert Result.Confidence == "High"


@patch("app.services.food_lookup_service.httpx.post")
def test_lookup_food_by_text_with_markdown_response(MockPost):
    """Test text lookup handles markdown code blocks in AI response."""
    MockResponse = Mock()
    MockResponse.status_code = 200
    MockResponse.json.return_value = {
        "choices": [{
            "message": {
                "content": "```json\n" + json.dumps({
                    "FoodName": "Banana",
                    "ServingQuantity": 1.0,
                    "ServingUnit": "medium",
                    "CaloriesPerServing": 105,
                    "ProteinPerServing": 1.3,
                    "Confidence": "High"
                }) + "\n```"
            }
        }]
    }
    MockPost.return_value = MockResponse
    
    Result = LookupFoodByText("banana")
    
    assert Result.FoodName == "Banana"
    assert Result.CaloriesPerServing == 105


@patch("app.services.food_lookup_service.httpx.post")
def test_lookup_food_by_text_options_success(MockPost):
    """Test multiple AI options for text lookup."""
    MockResponse = Mock()
    MockResponse.status_code = 200
    MockResponse.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps([
                    {
                        "FoodName": "Mocha Coffee Small",
                        "ServingQuantity": 1.0,
                        "ServingUnit": "small",
                        "CaloriesPerServing": 180,
                        "ProteinPerServing": 6.0,
                        "Confidence": "Medium"
                    },
                    {
                        "FoodName": "Mocha Coffee Medium",
                        "ServingQuantity": 1.0,
                        "ServingUnit": "medium",
                        "CaloriesPerServing": 240,
                        "ProteinPerServing": 8.0,
                        "Confidence": "Medium"
                    },
                    {
                        "FoodName": "Mocha Coffee Large",
                        "ServingQuantity": 1.0,
                        "ServingUnit": "large",
                        "CaloriesPerServing": 300,
                        "ProteinPerServing": 10.0,
                        "Confidence": "Medium"
                    }
                ])
            }
        }]
    }
    MockPost.return_value = MockResponse

    Results = LookupFoodByTextOptions("mocha coffee")

    assert len(Results) == 3
    assert Results[0].ServingUnit == "small"
    assert Results[1].ServingUnit == "medium"
    assert Results[2].ServingUnit == "large"


def test_lookup_food_by_image_no_api_key():
    """Test that LookupFoodByImage raises error when API key not configured."""
    OriginalKey = Settings.OpenAiApiKey
    Settings.OpenAiApiKey = None
    
    try:
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            LookupFoodByImage("base64imagedata")
    finally:
        Settings.OpenAiApiKey = OriginalKey


@patch("app.services.food_lookup_service.httpx.post")
def test_lookup_food_by_image_success(MockPost):
    """Test successful image-based food lookup."""
    MockResponse = Mock()
    MockResponse.status_code = 200
    MockResponse.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps([
                    {
                        "FoodName": "Grilled Chicken Breast",
                        "ServingQuantity": 150.0,
                        "ServingUnit": "g",
                        "CaloriesPerServing": 165,
                        "ProteinPerServing": 31.0,
                        "FatPerServing": 3.6,
                        "Confidence": "High"
                    },
                    {
                        "FoodName": "Steamed Rice",
                        "ServingQuantity": 1.0,
                        "ServingUnit": "cup",
                        "CaloriesPerServing": 205,
                        "ProteinPerServing": 4.3,
                        "CarbsPerServing": 45.0,
                        "Confidence": "Medium"
                    }
                ])
            }
        }]
    }
    MockPost.return_value = MockResponse
    
    Results = LookupFoodByImage("fake_base64_image_data")
    
    assert len(Results) == 2
    assert Results[0].FoodName == "Grilled Chicken Breast"
    assert Results[0].CaloriesPerServing == 165
    assert Results[0].ProteinPerServing == 31.0
    assert Results[0].Source == "AI-Vision"
    assert Results[1].FoodName == "Steamed Rice"
    assert Results[1].CaloriesPerServing == 205


@patch("app.services.food_lookup_service.httpx.get")
def test_lookup_food_by_barcode_success(MockGet):
    """Test successful barcode lookup via Open Food Facts."""
    MockResponse = Mock()
    MockResponse.status_code = 200
    MockResponse.json.return_value = {
        "status": 1,
        "product": {
            "product_name": "Weet-Bix Breakfast Cereal",
            "serving_size": "30g",
            "nutriments": {
                "energy-kcal_100g": 365,
                "proteins_100g": 12.5,
                "fiber_100g": 11.4,
                "carbohydrates_100g": 66.7,
                "fat_100g": 2.7,
                "saturated-fat_100g": 0.6,
                "sugars_100g": 3.3,
                "sodium_100g": 0.125
            }
        }
    }
    MockGet.return_value = MockResponse
    
    Result = LookupFoodByBarcode("9310015241054")
    
    assert Result is not None
    assert Result.FoodName == "Weet-Bix Breakfast Cereal"
    assert Result.ServingQuantity == 30.0
    assert Result.ServingUnit == "g"
    # Values adjusted for 30g serving
    assert Result.CaloriesPerServing == int(365 * 0.3)  # 109
    assert Result.ProteinPerServing == round(12.5 * 0.3, 1)  # 3.8
    assert Result.Source == "OpenFoodFacts"
    assert Result.Confidence == "High"


@patch("app.services.food_lookup_service.httpx.get")
def test_lookup_food_by_barcode_not_found(MockGet):
    """Test barcode lookup when product not found."""
    MockResponse = Mock()
    MockResponse.status_code = 200
    MockResponse.json.return_value = {"status": 0}
    MockGet.return_value = MockResponse
    
    Result = LookupFoodByBarcode("0000000000000")
    
    assert Result is None


@patch("app.services.food_lookup_service.httpx.get")
def test_lookup_food_by_barcode_http_error(MockGet):
    """Test barcode lookup handles HTTP errors gracefully."""
    MockGet.side_effect = Exception("Network error")
    
    Result = LookupFoodByBarcode("1234567890")
    
    assert Result is None
