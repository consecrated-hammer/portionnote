from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any

from app.dependencies import RequireUser
from app.models.schemas import User, FoodInfo
from app.services.food_lookup_service import (
    LookupFoodByBarcode,
    LookupFoodByImage,
    LookupFoodByText,
    LookupFoodByTextOptions,
    SearchAustralianFoodSuggestions
)
from app.services.multi_source_lookup_service import MultiSourceFoodLookupService
from app.services.rate_limiter import OpenFoodFactsRateLimiter

FoodLookupRouter = APIRouter()


class TextLookupInput(BaseModel):
    Query: str


class ImageLookupInput(BaseModel):
    ImageBase64: str


class BarcodeLookupInput(BaseModel):
    Barcode: str


class FoodLookupResponse(BaseModel):
    FoodName: str
    ServingQuantity: float
    ServingUnit: str
    CaloriesPerServing: int
    ProteinPerServing: float
    FibrePerServing: float | None = None
    CarbsPerServing: float | None = None
    FatPerServing: float | None = None
    SaturatedFatPerServing: float | None = None
    SugarPerServing: float | None = None
    SodiumPerServing: float | None = None
    Source: str
    Confidence: str


class TextLookupResponse(BaseModel):
    Result: FoodLookupResponse


class TextLookupOptionsResponse(BaseModel):
    Results: list[FoodLookupResponse]


class ImageLookupResponse(BaseModel):
    Results: list[FoodLookupResponse]


class BarcodeLookupResponse(BaseModel):
    Result: FoodLookupResponse | None


@FoodLookupRouter.post("/text", response_model=TextLookupResponse, tags=["Food Lookup"])
async def LookupByText(Input: TextLookupInput, CurrentUser: User = Depends(RequireUser)):
    """
    Look up food nutritional information by text query using AI.
    Example: "weet-bix", "banana", "chicken breast"
    """
    try:
        Result = LookupFoodByText(Input.Query)
        return TextLookupResponse(
            Result=FoodLookupResponse(**Result.ToDict())
        )
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to lookup food.") from ErrorValue


@FoodLookupRouter.post("/text-options", response_model=TextLookupOptionsResponse, tags=["Food Lookup"])
async def LookupByTextOptions(Input: TextLookupInput, CurrentUser: User = Depends(RequireUser)):
    """
    Look up food nutritional information by text query using AI.
    Returns multiple size options when available.
    """
    try:
        Results = LookupFoodByTextOptions(Input.Query)
        return TextLookupOptionsResponse(
            Results=[FoodLookupResponse(**Result.ToDict()) for Result in Results]
        )
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to lookup food.") from ErrorValue


@FoodLookupRouter.post("/image", response_model=ImageLookupResponse, tags=["Food Lookup"])
async def LookupByImage(Input: ImageLookupInput, CurrentUser: User = Depends(RequireUser)):
    """
    Analyze a food/meal image and return nutritional information for each ingredient.
    Expects base64-encoded image string (without data:image prefix).
    """
    try:
        Results = LookupFoodByImage(Input.ImageBase64)
        return ImageLookupResponse(
            Results=[FoodLookupResponse(**R.ToDict()) for R in Results]
        )
    except ValueError as ErrorValue:
        raise HTTPException(status_code=400, detail=str(ErrorValue)) from ErrorValue
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to analyze image.") from ErrorValue


@FoodLookupRouter.post("/barcode", response_model=BarcodeLookupResponse, tags=["Food Lookup"])
async def LookupByBarcode(Input: BarcodeLookupInput, CurrentUser: User = Depends(RequireUser)):
    """
    Look up food by barcode using Open Food Facts API (free).
    Returns None if product not found.
    """
    try:
        Result = LookupFoodByBarcode(Input.Barcode)
        if Result is None:
            return BarcodeLookupResponse(Result=None)
        return BarcodeLookupResponse(
            Result=FoodLookupResponse(**Result.ToDict())
        )
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to lookup barcode.") from ErrorValue


class FoodSuggestionsResponse(BaseModel):
    Suggestions: list[str]


@FoodLookupRouter.get("/suggestions", response_model=FoodSuggestionsResponse, tags=["Food Lookup"])
async def GetFoodSuggestions(
    Q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    Limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    CurrentUser: User = Depends(RequireUser)
):
    """
    Get food name autocomplete suggestions prioritizing Australian brands and products.
    Requires minimum 2-3 characters to start returning suggestions.
    """
    try:
        Suggestions = SearchAustralianFoodSuggestions(Q, Limit)
        return FoodSuggestionsResponse(Suggestions=Suggestions)
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail="Failed to get suggestions.") from ErrorValue


class MultiSourceSearchInput(BaseModel):
    Query: str
    IncludeScraping: bool = True  # Set to False for faster results (OpenFoodFacts only)


class MultiSourceSearchResponse(BaseModel):
    Openfoodfacts: List[FoodInfo]
    Coles: List[FoodInfo]
    Woolworths: List[FoodInfo]
    AiFallbackAvailable: bool


class ProductDetailsInput(BaseModel):
    Source: str  # "coles" or "woolworths"
    ProductUrl: str


class ProductDetailsResponse(BaseModel):
    Result: FoodInfo | None


@FoodLookupRouter.post("/multi-source/search", response_model=MultiSourceSearchResponse, tags=["Food Lookup"])
async def MultiSourceSearch(Input: MultiSourceSearchInput, CurrentUser: User = Depends(RequireUser)):
    """
    Search for food across multiple sources: OpenFoodFacts, Coles, Woolworths.
    
    Priority order:
    1. OpenFoodFacts (free, open database - always searched)
    2. Coles/Woolworths (official product data - only if IncludeScraping=True)
    3. AI fallback available if no results found
    
    Set IncludeScraping=False for faster results (OpenFoodFacts only).
    """
    try:
        Results = await MultiSourceFoodLookupService.Search(
            Input.Query, 
            IncludeScraping=Input.IncludeScraping
        )
        
        return MultiSourceSearchResponse(
            Openfoodfacts=Results.get("openfoodfacts", []),
            Coles=Results.get("coles", []),
            Woolworths=Results.get("woolworths", []),
            AiFallbackAvailable=Results.get("ai_fallback_available", True)
        )
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail=f"Multi-source search failed: {str(ErrorValue)}") from ErrorValue


@FoodLookupRouter.post("/multi-source/details", response_model=ProductDetailsResponse, tags=["Food Lookup"])
async def GetProductDetails(Input: ProductDetailsInput, CurrentUser: User = Depends(RequireUser)):
    """
    Get detailed nutrition information for a specific Coles or Woolworths product.
    
    Use this to fetch full nutrition data after selecting a product from search results.
    """
    try:
        Result = await MultiSourceFoodLookupService.GetProductDetails(
            Input.Source,
            Input.ProductUrl
        )
        
        return ProductDetailsResponse(Result=Result)
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail=f"Failed to fetch product details: {str(ErrorValue)}") from ErrorValue


@FoodLookupRouter.post("/multi-source/ai-fallback", response_model=TextLookupResponse, tags=["Food Lookup"])
async def GetAIFallback(Input: TextLookupInput, CurrentUser: User = Depends(RequireUser)):
    """
    Get AI-generated food information as fallback when no results found in databases.
    """
    try:
        Result = MultiSourceFoodLookupService.GetAIFallback(Input.Query)
        
        return TextLookupResponse(
            Result=FoodLookupResponse(
                FoodName=Result.FoodName,
                ServingQuantity=1.0,
                ServingUnit=Result.ServingDescription,
                CaloriesPerServing=Result.CaloriesPerServing or 0,
                ProteinPerServing=Result.ProteinPerServing or 0.0,
                FibrePerServing=Result.FiberPerServing,
                CarbsPerServing=Result.CarbohydratesPerServing,
                FatPerServing=Result.FatPerServing,
                SaturatedFatPerServing=Result.SaturatedFatPerServing,
                SugarPerServing=Result.SugarPerServing,
                SodiumPerServing=Result.SodiumPerServing,
                Source=Result.Metadata.get("source", "ai"),
                Confidence=Result.Metadata.get("confidence", "low")
            )
        )
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail=f"AI fallback failed: {str(ErrorValue)}") from ErrorValue


@FoodLookupRouter.get("/multi-source/cache-stats", tags=["Food Lookup"])
async def GetCacheStats(CurrentUser: User = Depends(RequireUser)):
    """Get cache statistics for debugging and monitoring."""
    try:
        Stats = MultiSourceFoodLookupService.GetCacheStats()
        return Stats
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(ErrorValue)}") from ErrorValue


@FoodLookupRouter.get("/multi-source/rate-limit-stats", tags=["Food Lookup"])
async def GetRateLimitStats(CurrentUser: User = Depends(RequireUser)):
    """Get OpenFoodFacts rate limit statistics for monitoring."""
    try:
        Stats = OpenFoodFactsRateLimiter.GetAllStats()
        return Stats
    except Exception as ErrorValue:
        raise HTTPException(status_code=500, detail=f"Failed to get rate limit stats: {str(ErrorValue)}") from ErrorValue
