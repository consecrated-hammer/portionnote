"""
Tests for multi-source food lookup service.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.multi_source_lookup_service import MultiSourceFoodLookupService
from app.models.schemas import FoodInfo


@pytest.mark.asyncio
async def TestSearchWithOpenFoodFactsOnly():
    """Test search with scraping disabled (OpenFoodFacts only)."""
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
        
        Results = await MultiSourceFoodLookupService.Search("bega", IncludeScraping=False)
        
        assert "openfoodfacts" in Results
        assert len(Results["openfoodfacts"]) == 1
        assert Results["openfoodfacts"][0].FoodName == "Bega Peanut Butter"
        assert len(Results["coles"]) == 0
        assert len(Results["woolworths"]) == 0
        assert Results["ai_fallback_available"] is True


@pytest.mark.asyncio
async def TestSearchWithAllSources():
    """Test search with all sources enabled."""
    MockOFFResults = [FoodInfo(FoodName="OFF Result", ServingDescription="100g", CaloriesPerServing=100, ProteinPerServing=10.0, Metadata={"source": "openfoodfacts"})]
    MockColesResults = [FoodInfo(FoodName="Coles Result", ServingDescription="100g", CaloriesPerServing=200, ProteinPerServing=20.0, Metadata={"source": "coles"})]
    MockWoolworthsResults = [FoodInfo(FoodName="Woolworths Result", ServingDescription="100g", CaloriesPerServing=300, ProteinPerServing=30.0, Metadata={"source": "woolworths"})]
    
    with patch("app.services.multi_source_lookup_service.OpenFoodFactsService.SearchProducts", new_callable=AsyncMock) as MockOFF, \
         patch("app.services.multi_source_lookup_service.SupermarketScraperService.SearchColes", new_callable=AsyncMock) as MockColes, \
         patch("app.services.multi_source_lookup_service.SupermarketScraperService.SearchWoolworths", new_callable=AsyncMock) as MockWoolworths:
        
        MockOFF.return_value = MockOFFResults
        MockColes.return_value = MockColesResults
        MockWoolworths.return_value = MockWoolworthsResults
        
        Results = await MultiSourceFoodLookupService.Search("test", IncludeScraping=True)
        
        assert len(Results["openfoodfacts"]) == 1
        assert len(Results["coles"]) == 1
        assert len(Results["woolworths"]) == 1
        assert Results["openfoodfacts"][0].FoodName == "OFF Result"
        assert Results["coles"][0].FoodName == "Coles Result"
        assert Results["woolworths"][0].FoodName == "Woolworths Result"


@pytest.mark.asyncio
async def TestSearchWithScraperErrors():
    """Test search gracefully handles scraper errors."""
    MockOFFResults = [FoodInfo(FoodName="OFF Result", ServingDescription="100g", CaloriesPerServing=100, ProteinPerServing=10.0, Metadata={"source": "openfoodfacts"})]
    
    with patch("app.services.multi_source_lookup_service.OpenFoodFactsService.SearchProducts", new_callable=AsyncMock) as MockOFF, \
         patch("app.services.multi_source_lookup_service.SupermarketScraperService.SearchColes", new_callable=AsyncMock) as MockColes, \
         patch("app.services.multi_source_lookup_service.SupermarketScraperService.SearchWoolworths", new_callable=AsyncMock) as MockWoolworths:
        
        MockOFF.return_value = MockOFFResults
        MockColes.side_effect = Exception("Scraping failed")
        MockWoolworths.side_effect = Exception("Scraping failed")
        
        Results = await MultiSourceFoodLookupService.Search("test", IncludeScraping=True)
        
        # Should still return OpenFoodFacts results
        assert len(Results["openfoodfacts"]) == 1
        assert len(Results["coles"]) == 0
        assert len(Results["woolworths"]) == 0


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
