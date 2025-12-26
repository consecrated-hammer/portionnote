"""
Food lookup service.

Sources:
1. OpenFoodFacts (free, open, comprehensive)
2. AI fallback (for items not in databases)

Results are cached to minimize repeated calls.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.schemas import FoodInfo
from app.services.openfoodfacts_service import OpenFoodFactsService
from app.utils.logger import GetLogger


# Simple in-memory cache (should be Redis in production)
_CACHE: Dict[str, tuple[Any, datetime]] = {}
_CACHE_TTL = timedelta(hours=24)
Logger = GetLogger("multi_source_lookup_service")


class MultiSourceFoodLookupService:
    """Food lookup service for OpenFoodFacts with caching."""
    
    @classmethod
    async def Search(cls, Query: str) -> Dict[str, List[FoodInfo]]:
        """
        Search for food across OpenFoodFacts.
        
        Args:
            Query: Search term (e.g., "bega crunchy")
            
        Returns:
            Dict with results grouped by source:
            {
                "openfoodfacts": [FoodInfo, ...],
                "ai_fallback_available": True/False
            }
        """
        # Check cache first
        CacheKey = f"search:{Query}"
        if CacheKey in _CACHE:
            CachedResults, CachedTime = _CACHE[CacheKey]
            if datetime.now() - CachedTime < _CACHE_TTL:
                return CachedResults
        
        Results = {
            "openfoodfacts": [],
            "ai_fallback_available": True
        }
        
        # Parallel fetch from OpenFoodFacts (fast)
        try:
            OFFResults = await OpenFoodFactsService.SearchProducts(Query, PageSize=10)
            Results["openfoodfacts"] = OFFResults
        except Exception as E:
            Logger.warning(f"OpenFoodFacts search error: {E}", exc_info=True)
        
        # Cache results
        _CACHE[CacheKey] = (Results, datetime.now())
        
        return Results
    
    @classmethod
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
