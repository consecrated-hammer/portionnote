"""
Australian supermarket scraper service.

Scrapes product data from Coles and Woolworths using Playwright for JavaScript rendering.
Handles bot detection with proper headers and delays.

NOTE: Coles has aggressive bot protection (Cloudflare) that may block automated access.
Woolworths generally allows scraping. Consider using OpenFoodFacts as primary source.
"""

from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page
import asyncio
from app.models.schemas import FoodInfo
from app.utils.logger import GetLogger

Logger = GetLogger("supermarket_scraper_service_old")


class SupermarketScraperService:
    """Service for scraping Australian supermarket websites."""
    
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    SCRAPER_API_KEY = "1bf7db33acd991bb3784d90bd5e867b5"
    SCRAPER_API_PROXY = {
        "server": "http://proxy-server.scraperapi.com:8001",
        "username": "scraperapi",
        "password": SCRAPER_API_KEY
    }
    
    @classmethod
    async def SearchColes(cls, Query: str, Limit: int = 10) -> List[FoodInfo]:
        """
        Search for products on Coles website.
        
        Args:
            Query: Search term (e.g., "bega crunchy")
            Limit: Maximum number of results (default 10)
            
        Returns:
            List of FoodInfo objects
        """
        SearchUrl = f"https://www.coles.com.au/search/products?q={Query}"
        
        async with async_playwright() as Playwright:
            Browser = await Playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            Context = await Browser.new_context(
                user_agent=cls.USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True
            )
            
            # Evade bot detection
            await Context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            Page = await Context.new_page()
            
            try:
                # Navigate to search page
                await Page.goto(SearchUrl, wait_until="domcontentloaded", timeout=30000)
                
                # Wait longer for JS to render products and bypass bot check
                await Page.wait_for_timeout(8000)
                
                # Check if we hit bot protection
                BodyText = await Page.evaluate('() => document.body.innerText')
                if 'bot' in BodyText.lower() or 'pardon' in BodyText.lower():
                    Logger.warning("Coles bot protection triggered - scrapers may be rate-limited")
                    return []
                
                # Extract product data
                Products = await Page.query_selector_all('[data-testid="product-tile"]')
                Results = []
                
                for Product in Products[:Limit]:
                    ProductData = await cls._ExtractColesProduct(Product, Page)
                    if ProductData:
                        Results.append(ProductData)
                
                return Results
            
            except Exception as E:
                Logger.warning(f"Coles scraping error: {E}", exc_info=True)
                return []
            
            finally:
                await Browser.close()
    
    @classmethod
    async def SearchWoolworths(cls, Query: str, Limit: int = 10) -> List[FoodInfo]:
        """
        Search for products on Woolworths website.
        
        Args:
            Query: Search term (e.g., "bega crunchy")
            Limit: Maximum number of results (default 10)
            
        Returns:
            List of FoodInfo objects
        """
        SearchUrl = f"https://www.woolworths.com.au/shop/search/products?searchTerm={Query}"
        
        async with async_playwright() as Playwright:
            Browser = await Playwright.chromium.launch(headless=True)
            Context = await Browser.new_context(user_agent=cls.USER_AGENT)
            Page = await Context.new_page()
            
            try:
                # Navigate to search page
                await Page.goto(SearchUrl, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for JS to render products
                await Page.wait_for_timeout(3000)
                
                # Extract product data
                Products = await Page.query_selector_all('shared-product-tile')
                
                if not Products:
                    Logger.info(f"Woolworths: No products found for query '{Query}'")
                
                Results = []
                
                Logger.debug(f"Extracting from {len(Products)} product tiles")
                
                for Product in Products[:Limit]:
                    ProductData = await cls._ExtractWoolworthsProduct(Product, Page)
                    Logger.debug(f"Extraction result: {ProductData is not None}")
                    if ProductData:
                        Results.append(ProductData)
                
                Logger.debug(f"Collected {len(Results)} valid products")
                return Results
            
            except Exception as E:
                Logger.warning(f"Woolworths scraping error: {E}", exc_info=True)
                return []
            
            finally:
                await Browser.close()
    
    @classmethod
    async def GetColesProductDetails(cls, ProductUrl: str) -> Optional[FoodInfo]:
        """
        Get detailed nutrition information from a Coles product page.
        
        Args:
            ProductUrl: Full URL to Coles product page
            
        Returns:
            FoodInfo object with detailed nutrition or None
        """
        async with async_playwright() as Playwright:
            Browser = await Playwright.chromium.launch(headless=True)
            Context = await Browser.new_context(user_agent=cls.USER_AGENT)
            Page = await Context.new_page()
            
            try:
                await Page.goto(ProductUrl, wait_until="networkidle", timeout=30000)
                
                # Extract product name
                NameElement = await Page.query_selector('h1')
                ProductName = await NameElement.inner_text() if NameElement else "Unknown Product"
                
                # Extract nutrition panel
                NutritionData = await cls._ExtractColesNutrition(Page)
                
                # Extract image
                ImageElement = await Page.query_selector('img[data-testid="product-image"]')
                ImageUrl = await ImageElement.get_attribute('src') if ImageElement else None
                
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
            
            finally:
                await Browser.close()
    
    @classmethod
    async def GetWoolworthsProductDetails(cls, ProductUrl: str) -> Optional[FoodInfo]:
        """
        Get detailed nutrition information from a Woolworths product page.
        
        Args:
            ProductUrl: Full URL to Woolworths product page
            
        Returns:
            FoodInfo object with detailed nutrition or None
        """
        async with async_playwright() as Playwright:
            Browser = await Playwright.chromium.launch(headless=True)
            Context = await Browser.new_context(user_agent=cls.USER_AGENT)
            Page = await Context.new_page()
            
            try:
                await Page.goto(ProductUrl, wait_until="networkidle", timeout=30000)
                
                # Extract product name
                NameElement = await Page.query_selector('h1')
                ProductName = await NameElement.inner_text() if NameElement else "Unknown Product"
                
                # Extract nutrition panel
                NutritionData = await cls._ExtractWoolworthsNutrition(Page)
                
                # Extract image
                ImageElement = await Page.query_selector('img[data-testid="product-image"]')
                ImageUrl = await ImageElement.get_attribute('src') if ImageElement else None
                
                if not NutritionData:
                    return None
                
                Metadata = {
                    "source": "woolworths",
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
                Logger.warning(f"Woolworths product details error: {E}", exc_info=True)
                return None
            
            finally:
                await Browser.close()
    
    @classmethod
    async def _ExtractColesProduct(cls, ProductElement: Any, Page: Page) -> Optional[FoodInfo]:
        """Extract basic product info from Coles search result."""
        try:
            # Extract product name from h2 or h3
            NameElement = await ProductElement.query_selector('h2, h3')
            if not NameElement:
                return None
            
            ProductName = (await NameElement.inner_text()).strip()
            if not ProductName:
                return None
            
            # Extract product URL
            LinkElement = await ProductElement.query_selector('a[href*="/product/"]')
            ProductUrl = None
            if LinkElement:
                Href = await LinkElement.get_attribute('href')
                if Href:
                    ProductUrl = Href if Href.startswith('http') else f"https://www.coles.com.au{Href}"
            
            # Extract image
            ImageElement = await ProductElement.query_selector('img')
            ImageUrl = await ImageElement.get_attribute('src') if ImageElement else None
            
            # Extract price (for display)
            PriceText = None
            PriceElements = await ProductElement.query_selector_all('[class*="price"]')
            for PriceElement in PriceElements:
                Text = (await PriceElement.inner_text()).strip()
                if Text and '$' in Text and 'SPECIAL' not in Text:
                    PriceText = Text
                    break
            
            Metadata = {
                "source": "coles",
                "url": ProductUrl,
                "image_url": ImageUrl,
                "price": PriceText,
                "requires_detail_fetch": True
            }
            
            # Return basic info - nutrition requires fetching product page
            return FoodInfo(
                FoodName=ProductName,
                ServingDescription="100g",  # Default serving size
                CaloriesPerServing=None,
                ProteinPerServing=None,
                Metadata=Metadata
            )
        
        except Exception as E:
            Logger.warning(f"Error extracting Coles product: {E}", exc_info=True)
            return None
    
    @classmethod
    async def _ExtractWoolworthsProduct(cls, ProductElement: Any, Page: Page) -> Optional[FoodInfo]:
        """Extract basic product info from Woolworths search result."""
        try:
            # Extract product name from h2 or h3
            NameElement = await ProductElement.query_selector('h2, h3')
            if not NameElement:
                return None
            
            ProductName = (await NameElement.inner_text()).strip()
            # Remove 'Promoted' label if present
            ProductName = ProductName.replace('Promoted\n', '').replace('Promoted', '').strip()
            if not ProductName:
                return None
            
            # Extract product URL
            LinkElement = await ProductElement.query_selector('a[href*="/product/"]')
            ProductUrl = None
            if LinkElement:
                Href = await LinkElement.get_attribute('href')
                if Href:
                    ProductUrl = Href if Href.startswith('http') else f"https://www.woolworths.com.au{Href}"
            
            # Extract image (skip promo roundels)
            ImageElement = await ProductElement.query_selector('img[src*="assets.woolworths.com.au"]')
            ImageUrl = await ImageElement.get_attribute('src') if ImageElement else None
            
            # Extract price (for display)
            PriceText = None
            PriceElements = await ProductElement.query_selector_all('[class*="price"]')
            for PriceElement in PriceElements:
                Text = (await PriceElement.inner_text()).strip()
                # Extract just the dollar amount
                Lines = Text.split('\n')
                for Line in Lines:
                    if '$' in Line and 'SAVE' not in Line and 'EVERYDAY' not in Line:
                        PriceText = Line.split()[0]  # Get first token with $
                        break
                if PriceText:
                    break
            
            Metadata = {
                "source": "woolworths",
                "url": ProductUrl,
                "image_url": ImageUrl,
                "price": PriceText,
                "requires_detail_fetch": True
            }
            
            # Return basic info - nutrition requires fetching product page
            return FoodInfo(
                FoodName=ProductName,
                ServingDescription="100g",  # Default serving size
                CaloriesPerServing=None,
                ProteinPerServing=None,
                Metadata=Metadata
            )
        
        except Exception as E:
            Logger.warning(f"Error extracting Woolworths product: {E}", exc_info=True)
            return None
    
    @classmethod
    async def _ExtractColesNutrition(cls, Page: Page) -> Optional[Dict[str, Any]]:
        """Extract nutrition information from Coles product page."""
        try:
            # Wait for table to load
            await Page.wait_for_timeout(2000)
            
            # Look for nutrition table
            TableElement = await Page.query_selector('table')
            if not TableElement:
                Logger.debug("No nutrition table found")
                return None
            
            # Get table text
            TableText = await TableElement.inner_text()
            
            # Parse nutrition values
            NutritionData = {
                "serving_size": "100g",  # Coles uses per 100g by default
                "calories": None,
                "protein": None,
                "fat": None,
                "saturated_fat": None,
                "carbohydrates": None,
                "sugar": None,
                "fiber": None,
                "sodium": None
            }
            
            # Extract energy (calories from kJ)
            if 'Energy' in TableText:
                Lines = TableText.split('\n')
                for i, Line in enumerate(Lines):
                    if Line.startswith('Energy'):
                        # Get the per 100g value (first value after label)
                        Values = Lines[i].split()
                        if len(Values) > 1:
                            KjValue = Values[1].replace('kJ', '')
                            try:
                                # Convert kJ to calories (kJ * 0.239)
                                NutritionData["calories"] = int(float(KjValue) * 0.239)
                            except ValueError:
                                pass
            
            # Extract other nutrients
            NutrientMap = {
                'Protein': 'protein',
                'Fat - Total': 'fat',
                'Fat - Saturated': 'saturated_fat',
                'Carbohydrate': 'carbohydrates',
                'Sugars': 'sugar',
                'Sodium': 'sodium'
            }
            
            Lines = TableText.split('\n')
            for i, Line in enumerate(Lines):
                for Label, Key in NutrientMap.items():
                    if Line.startswith(Label):
                        Values = Line.split()
                        if len(Values) > 1:
                            ValueStr = Values[-2] if len(Values) > 2 else Values[1]
                            ValueStr = ValueStr.replace('g', '').replace('mg', '')
                            try:
                                Value = float(ValueStr)
                                # Convert sodium from mg to mg (keep as is)
                                NutritionData[Key] = Value
                            except ValueError:
                                pass
                        break
            
            return NutritionData if NutritionData["calories"] else None
        
        except Exception as E:
            Logger.warning(f"Error extracting Coles nutrition: {E}", exc_info=True)
            return None
    
    @classmethod
    async def _ExtractWoolworthsNutrition(cls, Page: Page) -> Optional[Dict[str, Any]]:
        """Extract nutrition information from Woolworths product page."""
        try:
            # Look for nutrition table
            NutritionSection = await Page.query_selector('[data-testid="nutrition-information"]')
            if not NutritionSection:
                return None
            
            # Extract values - this will need adjustment based on actual HTML structure
            # This is a placeholder implementation
            return {
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
        
        except Exception as E:
            Logger.warning(f"Error extracting Woolworths nutrition: {E}", exc_info=True)
            return None
