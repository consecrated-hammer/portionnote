"""
Tests for multi-source food lookup service.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.multi_source_lookup_service import MultiSourceFoodLookupService
from app.models.schemas import FoodInfo


@pytest.mark.asyncio
async def TestSearchWithOpenFoodFactsOnly():
    """Test search with OpenFoodFacts only."""
    MockOFFResults = [
        FoodInfo(
            FoodName="Bega Peanut Butter",
            ServingDescription="100g",
            CaloriesPerServing=624,
            ProteinPerServing=23.9,
            Metadata={"source": "openfoodfacts"}
        )
    ]
    
    with patch("app.services.multi_source_lookup_service.OpenFoodFactsService.SearchProducts", new_callable=AsyncMock) as MockSearch:
        MockSearch.return_value = MockOFFResults
        
        Results = await MultiSourceFoodLookupService.Search("bega")
        
        assert "openfoodfacts" in Results
        assert len(Results["openfoodfacts"]) == 1
        assert Results["openfoodfacts"][0].FoodName == "Bega Peanut Butter"
        assert Results["ai_fallback_available"] is True


@pytest.mark.asyncio
async def TestSearchWithErrors():
    """Test search gracefully handles OpenFoodFacts errors."""
    with patch("app.services.multi_source_lookup_service.OpenFoodFactsService.SearchProducts", new_callable=AsyncMock) as MockOFF:
        MockOFF.side_effect = Exception("OpenFoodFacts failed")

        Results = await MultiSourceFoodLookupService.Search("test")

        assert len(Results["openfoodfacts"]) == 0
        assert Results["ai_fallback_available"] is True


@pytest.mark.asyncio
async def TestGetByBarcode():
    """Test barcode lookup."""
    MockResult = FoodInfo(
        FoodName="Test Product",
        ServingDescription="100g",
        CaloriesPerServing=500,
        ProteinPerServing=20.0,
        Metadata={"source": "openfoodfacts", "barcode": "1234567890"}
    )
    
    with patch("app.services.multi_source_lookup_service.OpenFoodFactsService.GetProductByBarcode", new_callable=AsyncMock) as MockBarcode:
        MockBarcode.return_value = MockResult
        
        Result = await MultiSourceFoodLookupService.GetByBarcode("1234567890")
        
        assert Result is not None
        assert Result.FoodName == "Test Product"
        assert Result.Metadata is not None
        assert Result.Metadata.get("barcode") == "1234567890"


@pytest.mark.asyncio
async def TestGetBarcodeNotFound():
    """Test barcode lookup with non-existent product."""
    with patch("app.services.multi_source_lookup_service.OpenFoodFactsService.GetProductByBarcode", new_callable=AsyncMock) as MockBarcode:
        MockBarcode.return_value = None
        
        Result = await MultiSourceFoodLookupService.GetByBarcode("0000000000")
        
        assert Result is None


def TestCacheStats():
    """Test cache statistics."""
    # Clear cache first
    MultiSourceFoodLookupService.ClearCache()
    
    Stats = MultiSourceFoodLookupService.GetCacheStats()
    
    assert "total_entries" in Stats
    assert "valid_entries" in Stats
    assert "expired_entries" in Stats
    assert "ttl_hours" in Stats
    assert Stats["total_entries"] == 0


def TestClearCache():
    """Test clearing cache."""
    MultiSourceFoodLookupService.ClearCache()
    
    Stats = MultiSourceFoodLookupService.GetCacheStats()
    assert Stats["total_entries"] == 0
