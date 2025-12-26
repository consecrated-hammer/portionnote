"""
Australian supermarket scraper service using ScraperAPI.

Uses ScraperAPI to bypass bot detection and handle JavaScript rendering.
Parses HTML with BeautifulSoup for product extraction.
"""

from typing import Optional, List, Dict, Any
import httpx
from bs4 import BeautifulSoup
import re

from app.models.schemas import FoodInfo
from app.config import Settings
from app.utils.logger import GetLogger

Logger = GetLogger("supermarket_scraper_service")


class SupermarketScraperService:
    """Service for scraping Australian supermarket websites via ScraperAPI."""
    
    @classmethod
    def _GetScraperApiUrl(cls, TargetUrl: str, RenderJs: bool = True) -> str:
        """Construct ScraperAPI URL for target page."""
        if not Settings.ScraperApiKey:
            raise ValueError("SCRAPER_API_KEY not configured in .env")
        
        Params = [
            f"api_key={Settings.ScraperApiKey}",
            f"url={TargetUrl}",
            "country_code=au"
        ]
        
        if RenderJs:
            Params.append("render=true")
        
        return f"http://api.scraperapi.com/?{'&'.join(Params)}"
    
    @classmethod
    async def SearchColes(cls, Query: str, Limit: int = 10) -> List[FoodInfo]:
        """Search for products on Coles website via ScraperAPI."""
        SearchUrl = f"https://www.coles.com.au/search/products?q={Query}"
        ScraperUrl = cls._GetScraperApiUrl(SearchUrl)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as Client:
                Response = await Client.get(ScraperUrl)
                Response.raise_for_status()
                
            Soup = BeautifulSoup(Response.text, 'html.parser')
            ProductTiles = Soup.find_all(attrs={'data-testid': 'product-tile'})
            
            Results = []
            for Tile in ProductTiles[:Limit]:
                ProductData = cls._ExtractColesProduct(Tile)
                if ProductData:
                    Results.append(ProductData)
            
            return Results
            
        except Exception as E:
            Logger.warning(f"Coles scraping error: {E}", exc_info=True)
            return []
    
    @classmethod
    async def SearchWoolworths(cls, Query: str, Limit: int = 10) -> List[FoodInfo]:
        """Search for products on Woolworths website via ScraperAPI."""
        SearchUrl = f"https://www.woolworths.com.au/shop/search/products?searchTerm={Query}"
        ScraperUrl = cls._GetScraperApiUrl(SearchUrl)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as Client:
                Response = await Client.get(ScraperUrl)
                Response.raise_for_status()
                
            Soup = BeautifulSoup(Response.text, 'html.parser')
            ProductTiles = Soup.find_all('shared-product-tile')
            
            Results = []
            for Tile in ProductTiles[:Limit]:
                ProductData = cls._ExtractWoolworthsProduct(Tile)
                if ProductData:
                    Results.append(ProductData)
            
            return Results
            
        except Exception as E:
            Logger.warning(f"Woolworths scraping error: {E}", exc_info=True)
            return []
    
    @classmethod
    def _ExtractColesProduct(cls, TileElement: Any) -> Optional[FoodInfo]:
        """Extract product info from Coles search result tile (BeautifulSoup element)."""
        try:
            # Extract product name from h2 or h3
            NameElement = TileElement.find(['h2', 'h3'])
            if not NameElement:
                return None
            
            ProductName = NameElement.get_text(strip=True)
            if not ProductName:
                return None
            
            # Extract product URL
            LinkElement = TileElement.find('a', href=re.compile(r'/product/'))
            ProductUrl = None
            if LinkElement and LinkElement.get('href'):
                Href = LinkElement['href']
                ProductUrl = Href if Href.startswith('http') else f"https://www.coles.com.au{Href}"
            
            # Extract image
            ImageElement = TileElement.find('img')
            ImageUrl = ImageElement.get('src') if ImageElement else None
            
            Metadata = {
                "source": "coles",
                "url": ProductUrl,
                "image_url": ImageUrl,
                "requires_detail_fetch": True
            }
            
            return FoodInfo(
                FoodName=ProductName,
                ServingDescription="100g",
                CaloriesPerServing=None,
                ProteinPerServing=None,
                Metadata=Metadata
            )
        
        except Exception as E:
            Logger.warning(f"Error extracting Coles product: {E}", exc_info=True)
            return None
    
    @classmethod
    def _ExtractWoolworthsProduct(cls, TileElement: Any) -> Optional[FoodInfo]:
        """Extract product info from Woolworths search result tile (BeautifulSoup element)."""
        try:
            # Extract product name from h2 or h3
            NameElement = TileElement.find(['h2', 'h3'])
            if not NameElement:
                return None
            
            ProductName = NameElement.get_text(strip=True)
            # Remove 'Promoted' label if present
            ProductName = ProductName.replace('Promoted', '').strip()
            if not ProductName:
                return None
            
            # Extract product URL
            LinkElement = TileElement.find('a', href=re.compile(r'/product/'))
            ProductUrl = None
            if LinkElement and LinkElement.get('href'):
                Href = LinkElement['href']
                ProductUrl = Href if Href.startswith('http') else f"https://www.woolworths.com.au{Href}"
            
            # Extract image (skip promo roundels)
            ImageElement = TileElement.find('img', src=re.compile(r'assets\.woolworths\.com\.au'))
            ImageUrl = ImageElement.get('src') if ImageElement else None
            
            Metadata = {
                "source": "woolworths",
                "url": ProductUrl,
                "image_url": ImageUrl,
                "requires_detail_fetch": True
            }
            
            return FoodInfo(
                FoodName=ProductName,
                ServingDescription="100g",
                CaloriesPerServing=None,
                ProteinPerServing=None,
                Metadata=Metadata
            )
        
        except Exception as E:
            Logger.warning(f"Error extracting Woolworths product: {E}", exc_info=True)
            return None
    
    @classmethod
    async def GetColesProductDetails(cls, ProductUrl: str) -> Optional[FoodInfo]:
        """Get detailed nutrition information from a Coles product page."""
        ScraperUrl = cls._GetScraperApiUrl(ProductUrl)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as Client:
                Response = await Client.get(ScraperUrl)
                Response.raise_for_status()
            
            Soup = BeautifulSoup(Response.text, 'html.parser')
            
            # Extract product name
            NameElement = Soup.find('h1')
            ProductName = NameElement.get_text(strip=True) if NameElement else "Unknown Product"
            
            # Extract nutrition table
            NutritionData = cls._ExtractColesNutrition(Soup)
            
            # Extract image
            ImageElement = Soup.find('img', attrs={'data-testid': 'product-image'})
            ImageUrl = ImageElement.get('src') if ImageElement else None
            
            if not NutritionData:
                return None
            
            Metadata = {
                "source": "coles",
                "url": ProductUrl,
                "image_url": ImageUrl
            }
            
            return FoodInfo(
                FoodName=ProductName,
                ServingDescription=NutritionData.get("serving_size", "100g"),
                CaloriesPerServing=NutritionData.get("calories"),
                ProteinPerServing=NutritionData.get("protein"),
                FatPerServing=NutritionData.get("fat"),
                SaturatedFatPerServing=NutritionData.get("saturated_fat"),
                CarbohydratesPerServing=NutritionData.get("carbohydrates"),
                SugarPerServing=NutritionData.get("sugar"),
                FiberPerServing=NutritionData.get("fiber"),
                SodiumPerServing=NutritionData.get("sodium"),
                Metadata=Metadata
            )
        
        except Exception as E:
            Logger.warning(f"Coles product details error: {E}", exc_info=True)
            return None
    
    @classmethod
    def _ExtractColesNutrition(cls, Soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract nutrition information from Coles product page."""
        try:
            # Look for nutrition table
            TableElement = Soup.find('table')
            if not TableElement:
                return None
            
            NutritionData = {
                "serving_size": "100g",
                "calories": None,
                "protein": None,
                "fat": None,
                "saturated_fat": None,
                "carbohydrates": None,
                "sugar": None,
                "fiber": None,
                "sodium": None
            }
            
            # Parse table rows
            Rows = TableElement.find_all('tr')
            
            for Row in Rows:
                Cells = Row.find_all(['td', 'th'])
                if len(Cells) < 2:
                    continue
                
                Label = Cells[0].get_text(strip=True)
                Value = Cells[1].get_text(strip=True)  # Per 100g/ml column
                
                # Extract energy (calories from kJ)
                if Label == 'Energy':
                    KjValue = Value.replace('kJ', '').strip()
                    try:
                        NutritionData["calories"] = int(float(KjValue) * 0.239)
                    except ValueError:
                        pass
                
                # Extract protein
                elif Label == 'Protein':
                    ValueStr = Value.replace('g', '').strip()
                    try:
                        NutritionData["protein"] = float(ValueStr)
                    except ValueError:
                        pass
                
                # Extract carbohydrates
                elif Label == 'Carbohydrate':
                    ValueStr = Value.replace('g', '').strip()
                    try:
                        NutritionData["carbohydrates"] = float(ValueStr)
                    except ValueError:
                        pass
                
                # Extract total fat
                elif Label == 'Fat - Total':
                    ValueStr = Value.replace('g', '').strip()
                    try:
                        NutritionData["fat"] = float(ValueStr)
                    except ValueError:
                        pass
                
                # Extract saturated fat
                elif Label == 'Fat - Saturated':
                    ValueStr = Value.replace('g', '').strip()
                    try:
                        NutritionData["saturated_fat"] = float(ValueStr)
                    except ValueError:
                        pass
                
                # Extract sugars
                elif 'Sugars' in Label:
                    ValueStr = Value.replace('g', '').strip()
                    try:
                        NutritionData["sugar"] = float(ValueStr)
                    except ValueError:
                        pass
                
                # Extract fiber
                elif 'Fibre' in Label or 'Fiber' in Label:
                    ValueStr = Value.replace('g', '').strip()
                    try:
                        NutritionData["fiber"] = float(ValueStr)
                    except ValueError:
                        pass
                
                # Extract sodium
                elif Label == 'Sodium':
                    ValueStr = Value.replace('mg', '').strip()
                    try:
                        # Convert mg to mg (no conversion needed, already in mg)
                        NutritionData["sodium"] = float(ValueStr)
                    except ValueError:
                        pass
            
            return NutritionData if NutritionData["calories"] else None
        
        except Exception as E:
            Logger.warning(f"Error extracting Coles nutrition: {E}", exc_info=True)
            return None
