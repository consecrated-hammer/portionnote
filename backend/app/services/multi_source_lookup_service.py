"""
Multi-source food lookup service.

Prioritizes data sources:
1. OpenFoodFacts (free, open, comprehensive)
2. Coles/Woolworths scrapers (official product data)
3. AI fallback (for items not in databases)

Results are cached to minimize repeated scraping.
"""

from typing import List, Optional, Dict, Any, Union
import asyncio
from datetime import datetime, timedelta
import json

from app.models.schemas import FoodInfo
from app.services.openfoodfacts_service import OpenFoodFactsService
from app.services.supermarket_scraper_service import SupermarketScraperService
from app.services.food_lookup_service import LookupFoodByText
from app.utils.logger import GetLogger


# Simple in-memory cache (should be Redis in production)
_CACHE: Dict[str, tuple[Any, datetime]] = {}
_CACHE_TTL = timedelta(hours=24)
Logger = GetLogger("multi_source_lookup_service")


class MultiSourceFoodLookupService:
    """Unified food lookup service across multiple data sources."""
    
    @classmethod
    async def Search(cls, Query: str, IncludeScraping: bool = True) -> Dict[str, List[FoodInfo]]:
        """
        Search for food across all sources.
        
        Args:
            Query: Search term (e.g., "bega crunchy")
            IncludeScraping: Whether to include supermarket scraping (can be slow)
            
        Returns:
            Dict with results grouped by source:
            {
                "openfoodfacts": [FoodInfo, ...],
                "coles": [FoodInfo, ...],
                "woolworths": [FoodInfo, ...],
                "ai_fallback_available": True/False
            }
        """
        # Check cache first
        CacheKey = f"search:{Query}:{IncludeScraping}"
        if CacheKey in _CACHE:
            CachedResults, CachedTime = _CACHE[CacheKey]
            if datetime.now() - CachedTime < _CACHE_TTL:
                return CachedResults
        
        Results = {
            "openfoodfacts": [],
            "coles": [],
            "woolworths": [],
            "ai_fallback_available": True
        }
        
        # Parallel fetch from OpenFoodFacts (fast)
        try:
            OFFResults = await OpenFoodFactsService.SearchProducts(Query, PageSize=10)
            Results["openfoodfacts"] = OFFResults
        except Exception as E:
            Logger.warning(f"OpenFoodFacts search error: {E}", exc_info=True)
        
        # Conditionally fetch from supermarkets (slow)
        if IncludeScraping:
            try:
                # Run both scrapers in parallel
                ColesTask = SupermarketScraperService.SearchColes(Query, Limit=5)
                WoolworthsTask = SupermarketScraperService.SearchWoolworths(Query, Limit=5)
                
                ColesResults, WoolworthsResults = await asyncio.gather(
                    ColesTask,
                    WoolworthsTask,
                    return_exceptions=True
                )
                
                if not isinstance(ColesResults, Exception):
                    Results["coles"] = ColesResults
                if not isinstance(WoolworthsResults, Exception):
                    Results["woolworths"] = WoolworthsResults
            
            except Exception as E:
                Logger.warning(f"Supermarket scraping error: {E}", exc_info=True)
        
        # Cache results
        _CACHE[CacheKey] = (Results, datetime.now())
        
        return Results
    
    @classmethod
    async def GetProductDetails(cls, Source: str, ProductUrl: str) -> Optional[FoodInfo]:
        """
        Get detailed nutrition information for a specific product.
        
        Args:
            Source: "coles" or "woolworths"
            ProductUrl: Full URL to product page
            
        Returns:
            FoodInfo with complete nutrition data
        """
        # Check cache
        CacheKey = f"details:{Source}:{ProductUrl}"
        if CacheKey in _CACHE:
            CachedResult, CachedTime = _CACHE[CacheKey]
            if datetime.now() - CachedTime < _CACHE_TTL:
                return CachedResult
        
        try:
            if Source == "coles":
                Result = await SupermarketScraperService.GetColesProductDetails(ProductUrl)
            elif Source == "woolworths":
                Result = await SupermarketScraperService.GetWoolworthsProductDetails(ProductUrl)
            else:
                return None
            
            # Cache result
            if Result:
                _CACHE[CacheKey] = (Result, datetime.now())
            
            return Result
        
        except Exception as E:
            Logger.warning(f"Product details fetch error: {E}", exc_info=True)
            return None
    
    @classmethod
    async def GetByBarcode(cls, Barcode: str) -> Optional[FoodInfo]:
        """
        Look up product by barcode (OpenFoodFacts only).
        
        Args:
            Barcode: Product barcode
            
        Returns:
            FoodInfo or None if not found
        """
        # Check cache
        CacheKey = f"barcode:{Barcode}"
        if CacheKey in _CACHE:
            CachedResult, CachedTime = _CACHE[CacheKey]
            if datetime.now() - CachedTime < _CACHE_TTL:
                return CachedResult
        
        try:
            Result = await OpenFoodFactsService.GetProductByBarcode(Barcode)
            
            # Cache result
            if Result:
                _CACHE[CacheKey] = (Result, datetime.now())
            
            return Result
        
        except Exception as E:
            Logger.warning(f"Barcode lookup error: {E}", exc_info=True)
            return None
    
    @classmethod
    def GetAIFallback(cls, Query: str) -> FoodInfo:
        """
        Get AI-generated food information as fallback.
        
        Args:
            Query: Food description
            
        Returns:
            FoodInfo from AI
        """
        # Use existing AI lookup service (synchronous)
        Result = LookupFoodByText(Query)
        
        # Convert to FoodInfo format
        return FoodInfo(
            FoodName=Result.FoodName,
            ServingDescription=f"{Result.ServingQuantity} {Result.ServingUnit}",
            CaloriesPerServing=Result.CaloriesPerServing,
            ProteinPerServing=Result.ProteinPerServing,
            FatPerServing=Result.FatPerServing,
            SaturatedFatPerServing=Result.SaturatedFatPerServing,
            CarbohydratesPerServing=Result.CarbsPerServing,
            SugarPerServing=Result.SugarPerServing,
            FiberPerServing=Result.FibrePerServing,
            SodiumPerServing=Result.SodiumPerServing,
            Metadata={
                "source": "ai",
                "confidence": Result.Confidence
            }
        )
    
    @classmethod
    def ClearCache(cls):
        """Clear all cached results."""
        global _CACHE
        _CACHE = {}
    
    @classmethod
    def GetCacheStats(cls) -> Dict[str, Any]:
        """Get cache statistics."""
        Now = datetime.now()
        ValidEntries = sum(1 for _, (_, CachedTime) in _CACHE.items() if Now - CachedTime < _CACHE_TTL)
        
        return {
            "total_entries": len(_CACHE),
            "valid_entries": ValidEntries,
            "expired_entries": len(_CACHE) - ValidEntries,
            "ttl_hours": _CACHE_TTL.total_seconds() / 3600
        }
