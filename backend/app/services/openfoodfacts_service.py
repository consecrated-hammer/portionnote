"""
OpenFoodFacts API integration service.

Fetches nutrition data from the OpenFoodFacts database (au.openfoodfacts.org).
This is a free, open-source database with comprehensive Australian product data.

Rate limits enforced:
- 100 req/min for product queries
- 10 req/min for search queries
"""

import httpx
from typing import Optional, List, Dict, Any
from app.models.schemas import FoodInfo
from app.services.rate_limiter import OpenFoodFactsRateLimiter


class OpenFoodFactsService:
    """Service for fetching food data from OpenFoodFacts API."""
    
    # Use world database with country filter - AU database search is unreliable
    BASE_URL = "https://world.openfoodfacts.org"
    SEARCH_URL = f"{BASE_URL}/cgi/search.pl"
    PRODUCT_URL = f"{BASE_URL}/api/v2/product"
    
    # User agent as requested by OpenFoodFacts
    USER_AGENT = "PortionNote/1.0 (https://github.com/yourusername/portionnote)"
    
    @classmethod
    async def SearchProducts(cls, Query: str, PageSize: int = 10) -> List[FoodInfo]:
        """
        Search for products on OpenFoodFacts.
        
        Rate limit: 10 req/min for search queries.
        
        Args:
            Query: Search term (e.g., "bega crunchy")
            PageSize: Number of results to return (default 10)
            
        Returns:
            List of FoodInfo objects
        """
        # Enforce rate limit (wait if necessary)
        await OpenFoodFactsRateLimiter.AcquireSearch(Wait=True)
        
        Params = {
            "search_terms": Query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": PageSize * 2,  # Request more to allow for filtering
            "tagtype_0": "countries",
            "tag_contains_0": "contains",
            "tag_0": "australia",
            "fields": "code,product_name,brands,image_url,nutriments,serving_size,serving_quantity,countries_tags"
        }
        
        Headers = {
            "User-Agent": cls.USER_AGENT
        }
        
        async with httpx.AsyncClient(timeout=10.0) as Client:
            Response = await Client.get(cls.SEARCH_URL, params=Params, headers=Headers)
            Response.raise_for_status()
            Data = Response.json()
            
            Results = []
            for Product in Data.get("products", []):
                FoodInfoObj = cls._ParseProduct(Product)
                if FoodInfoObj:
                    Results.append(FoodInfoObj)
                    if len(Results) >= PageSize:
                        break
            
            return Results
    
    @classmethod
    async def GetProductByBarcode(cls, Barcode: str) -> Optional[FoodInfo]:
        """
        Get a specific product by its barcode.
        
        Rate limit: 100 req/min for product queries.
        
        Args:
            Barcode: Product barcode (e.g., "9352042002827")
            
        Returns:
            FoodInfo object or None if not found
        """
        # Enforce rate limit (wait if necessary)
        await OpenFoodFactsRateLimiter.AcquireProduct(Wait=True)
        
        Url = f"{cls.PRODUCT_URL}/{Barcode}.json"
        
        Headers = {
            "User-Agent": cls.USER_AGENT
        }
        
        async with httpx.AsyncClient(timeout=10.0) as Client:
            Response = await Client.get(Url, headers=Headers)
            
            if Response.status_code == 404:
                return None
            
            Response.raise_for_status()
            Data = Response.json()
            
            if Data.get("status") != 1:
                return None
            
            return cls._ParseProduct(Data.get("product", {}))
    
    @classmethod
    def _ParseProduct(cls, Product: Dict[str, Any]) -> Optional[FoodInfo]:
        """
        Parse OpenFoodFacts product data into FoodInfo schema.
        
        Args:
            Product: Raw product data from OpenFoodFacts API
            
        Returns:
            FoodInfo object or None if invalid data
        """
        # Extract basic info
        ProductName = Product.get("product_name", "")
        Brands = Product.get("brands", "")
        Barcode = Product.get("code", "")
        
        if not ProductName:
            return None
        
        # Construct full name with brand
        if Brands:
            FullName = f"{Brands} {ProductName}"
        else:
            FullName = ProductName
        
        # Extract nutrition data (per 100g/100ml)
        Nutriments = Product.get("nutriments", {})
        
        # Helper function to safely convert to float
        def ToFloat(Value):
            if Value is None:
                return None
            try:
                return float(Value)
            except (ValueError, TypeError):
                return None
        
        # OpenFoodFacts uses "energy-kcal_100g" for calories
        CaloriesPer100g = ToFloat(Nutriments.get("energy-kcal_100g"))
        ProteinPer100g = ToFloat(Nutriments.get("proteins_100g"))
        FatPer100g = ToFloat(Nutriments.get("fat_100g"))
        SaturatedFatPer100g = ToFloat(Nutriments.get("saturated-fat_100g"))
        CarbsPer100g = ToFloat(Nutriments.get("carbohydrates_100g"))
        SugarPer100g = ToFloat(Nutriments.get("sugars_100g"))
        FiberPer100g = ToFloat(Nutriments.get("fiber_100g"))
        SodiumPer100g = ToFloat(Nutriments.get("sodium_100g"))
        
        # Serving size info
        ServingSize = Product.get("serving_size", "")
        ServingQuantity = ToFloat(Product.get("serving_quantity"))  # in grams
        
        # Determine serving description
        if ServingSize:
            ServingDescription = ServingSize
        elif ServingQuantity:
            ServingDescription = f"{ServingQuantity}g"
        else:
            ServingDescription = "100g"
        
        # Calculate per serving values (default to per 100g if no serving size)
        ServingMultiplier = 1.0
        if ServingQuantity:
            ServingMultiplier = ServingQuantity / 100.0
        
        CaloriesPerServing = round(CaloriesPer100g * ServingMultiplier) if CaloriesPer100g else None
        ProteinPerServing = round(ProteinPer100g * ServingMultiplier, 1) if ProteinPer100g else None
        FatPerServing = round(FatPer100g * ServingMultiplier, 1) if FatPer100g else None
        SaturatedFatPerServing = round(SaturatedFatPer100g * ServingMultiplier, 1) if SaturatedFatPer100g else None
        CarbsPerServing = round(CarbsPer100g * ServingMultiplier, 1) if CarbsPer100g else None
        SugarPerServing = round(SugarPer100g * ServingMultiplier, 1) if SugarPer100g else None
        FiberPerServing = round(FiberPer100g * ServingMultiplier, 1) if FiberPer100g else None
        
        # Sodium (convert mg to grams for consistency)
        SodiumPerServing = round(SodiumPer100g * ServingMultiplier * 1000, 1) if SodiumPer100g else None
        
        # Image URL
        ImageUrl = Product.get("image_url") or Product.get("image_front_url")
        
        # Product URL
        ProductUrl = f"https://au.openfoodfacts.org/product/{Barcode}" if Barcode else None
        
        # Build metadata
        Metadata = {
            "source": "openfoodfacts",
            "barcode": Barcode,
            "brands": Brands,
            "image_url": ImageUrl,
            "url": ProductUrl,
            "serving_size": ServingSize,
            "per_100g": {
                "calories": CaloriesPer100g,
                "protein": ProteinPer100g,
                "fat": FatPer100g,
                "saturated_fat": SaturatedFatPer100g,
                "carbohydrates": CarbsPer100g,
                "sugars": SugarPer100g,
                "fiber": FiberPer100g,
                "sodium": SodiumPer100g
            }
        }
        
        return FoodInfo(
            FoodName=FullName,
            ServingDescription=ServingDescription,
            CaloriesPerServing=CaloriesPerServing,
            ProteinPerServing=ProteinPerServing,
            FatPerServing=FatPerServing,
            SaturatedFatPerServing=SaturatedFatPerServing,
            CarbohydratesPerServing=CarbsPerServing,
            SugarPerServing=SugarPerServing,
            FiberPerServing=FiberPerServing,
            SodiumPerServing=SodiumPerServing,
            Metadata=Metadata
        )
