"""
Service for looking up food information using AI (text), image recognition, and barcode scanning.
"""
import base64
import json
import re
from typing import Optional

import httpx

from app.config import Settings
from app.services.openai_client import (
    GetOpenAiContent,
    GetOpenAiContentForModel,
    GetOpenAiContentWithModel
)
from app.utils.logger import GetLogger

Logger = GetLogger("food_lookup_service")


class FoodLookupResult:
    """Result from food lookup containing nutritional information."""
    
    def __init__(
        self,
        FoodName: str,
        ServingQuantity: float,
        ServingUnit: str,
        CaloriesPerServing: int,
        ProteinPerServing: float,
        FibrePerServing: Optional[float] = None,
        CarbsPerServing: Optional[float] = None,
        FatPerServing: Optional[float] = None,
        SaturatedFatPerServing: Optional[float] = None,
        SugarPerServing: Optional[float] = None,
        SodiumPerServing: Optional[float] = None,
        Source: str = "AI",
        Confidence: str = "High"
    ):
        self.FoodName = FoodName
        self.ServingQuantity = ServingQuantity
        self.ServingUnit = ServingUnit
        self.CaloriesPerServing = CaloriesPerServing
        self.ProteinPerServing = ProteinPerServing
        self.FibrePerServing = FibrePerServing
        self.CarbsPerServing = CarbsPerServing
        self.FatPerServing = FatPerServing
        self.SaturatedFatPerServing = SaturatedFatPerServing
        self.SugarPerServing = SugarPerServing
        self.SodiumPerServing = SodiumPerServing
        self.Source = Source
        self.Confidence = Confidence

    def ToDict(self) -> dict:
        return {
            "FoodName": self.FoodName,
            "ServingQuantity": self.ServingQuantity,
            "ServingUnit": self.ServingUnit,
            "CaloriesPerServing": self.CaloriesPerServing,
            "ProteinPerServing": self.ProteinPerServing,
            "FibrePerServing": self.FibrePerServing,
            "CarbsPerServing": self.CarbsPerServing,
            "FatPerServing": self.FatPerServing,
            "SaturatedFatPerServing": self.SaturatedFatPerServing,
            "SugarPerServing": self.SugarPerServing,
            "SodiumPerServing": self.SodiumPerServing,
            "Source": self.Source,
            "Confidence": self.Confidence
        }


def ParseLookupJson(Content: str) -> object:
    if not Content:
        raise ValueError("No response from AI.")

    if "```json" in Content:
        Content = Content.split("```json")[1].split("```")[0].strip()
    elif "```" in Content:
        Content = Content.split("```")[1].split("```")[0].strip()

    try:
        return json.loads(Content)
    except json.JSONDecodeError as ErrorValue:
        Cleaned = Content.strip()
        ListStart = Cleaned.find("[")
        ListEnd = Cleaned.rfind("]")
        ObjStart = Cleaned.find("{")
        ObjEnd = Cleaned.rfind("}")
        Candidate = ""
        if ListStart != -1 and ListEnd != -1 and ListEnd > ListStart:
            Candidate = Cleaned[ListStart:ListEnd + 1]
        elif ObjStart != -1 and ObjEnd != -1 and ObjEnd > ObjStart:
            Candidate = Cleaned[ObjStart:ObjEnd + 1]
        if Candidate:
            try:
                return json.loads(Candidate)
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Invalid AI response format: {ErrorValue}") from ErrorValue


def NormalizeServingSize(ServingQuantity: float, ServingUnit: str) -> tuple[float, str]:
    UnitValue = str(ServingUnit or "").strip()
    if not UnitValue:
        return ServingQuantity, "serving"

    Match = re.match(r"^(\d+\.?\d*)\s*([a-zA-Z]+)$", UnitValue)
    if Match and ServingQuantity == 1.0:
        ServingQuantity = float(Match.group(1))
        UnitValue = Match.group(2)

    UnitLower = UnitValue.lower()
    if UnitLower in ("g", "gram", "grams", "gr"):
        return ServingQuantity, "g"
    if UnitLower in ("ml", "milliliter", "milliliters", "millilitre", "millilitres"):
        return ServingQuantity, "mL"
    if UnitLower in ("servings", "portion", "portions"):
        return ServingQuantity, "serving"

    return ServingQuantity, UnitValue


def NormalizeFoodLookupResult(FoodData: dict, Query: str) -> FoodLookupResult:
    ServingQuantity = float(FoodData.get("ServingQuantity", 1.0))
    ServingUnit = FoodData.get("ServingUnit", "serving")
    ServingQuantity, ServingUnit = NormalizeServingSize(ServingQuantity, ServingUnit)
    return FoodLookupResult(
        FoodName=FoodData.get("FoodName", Query),
        ServingQuantity=ServingQuantity,
        ServingUnit=ServingUnit,
        CaloriesPerServing=int(FoodData.get("CaloriesPerServing", 0)),
        ProteinPerServing=float(FoodData.get("ProteinPerServing", 0)),
        FibrePerServing=float(FoodData["FibrePerServing"]) if FoodData.get("FibrePerServing") is not None else None,
        CarbsPerServing=float(FoodData["CarbsPerServing"]) if FoodData.get("CarbsPerServing") is not None else None,
        FatPerServing=float(FoodData["FatPerServing"]) if FoodData.get("FatPerServing") is not None else None,
        SaturatedFatPerServing=float(FoodData["SaturatedFatPerServing"]) if FoodData.get("SaturatedFatPerServing") is not None else None,
        SugarPerServing=float(FoodData["SugarPerServing"]) if FoodData.get("SugarPerServing") is not None else None,
        SodiumPerServing=float(FoodData["SodiumPerServing"]) if FoodData.get("SodiumPerServing") is not None else None,
        Source="AI-Text",
        Confidence=FoodData.get("Confidence", "Medium")
    )


def LookupFoodByText(Query: str) -> FoodLookupResult:
    """
    Look up food nutritional information by text query using OpenAI.
    
    Args:
        Query: Food name or description (e.g., "weet-bix", "banana", "chicken breast")
    
    Returns:
        FoodLookupResult with nutritional information
    
    Raises:
        ValueError: If OpenAI API key not configured or invalid response
    """
    if not Settings.OpenAiApiKey:
        raise ValueError("OpenAI API key not configured.")

    SystemPrompt = """You are a nutrition database assistant. When given a food name, return accurate nutritional information in JSON format.

Return ONLY a JSON object with these exact fields:
{
  "FoodName": "standardized food name",
  "ServingQuantity": 1.0,
  "ServingUnit": "unit (e.g., g, mL, cup, slice, piece)",
  "CaloriesPerServing": integer,
  "ProteinPerServing": float (grams),
  "FibrePerServing": float (grams) or null,
  "CarbsPerServing": float (grams) or null,
  "FatPerServing": float (grams) or null,
  "SaturatedFatPerServing": float (grams) or null,
  "SugarPerServing": float (grams) or null,
  "SodiumPerServing": float (mg) or null,
  "Confidence": "High" or "Medium" or "Low"
}

Serving size rules:
- Prefer measurable units when possible: use grams (g) for solids and milliliters (mL) for liquids.
- Avoid vague units like "serving" for basics such as milk, yogurt, rice, cereal, or vegetables.
- Use "serving" ONLY for named menu items or combo meals, and include the size in FoodName (e.g., "Large Tropical Whopper Meal").
- For discrete items, use clear units like piece, slice, egg, can, bar.

Use standard serving sizes. Be precise with nutritional values based on USDA or Australian food databases."""

    Content = GetOpenAiContent(
        [
            {"role": "system", "content": SystemPrompt},
            {"role": "user", "content": f"Look up nutritional information for: {Query}"}
        ],
        Temperature=0.3,
        MaxTokens=500
    )
    FoodData = ParseLookupJson(Content)
    if isinstance(FoodData, list):
        if not FoodData:
            raise ValueError("No results returned from AI.")
        FoodData = FoodData[0]
    if not isinstance(FoodData, dict):
        raise ValueError("Invalid AI response format.")

    return NormalizeFoodLookupResult(FoodData, Query)


def LookupFoodByTextOptions(Query: str) -> list[FoodLookupResult]:
    """
    Look up food nutritional information by text query using OpenAI.
    Returns multiple size options when available.
    """
    if not Settings.OpenAiApiKey:
        raise ValueError("OpenAI API key not configured.")

    SystemPrompt = """You are a nutrition database assistant. When given a food name, return multiple size options in JSON format.

Return ONLY a JSON array of 1 to 3 objects with these exact fields:
[
  {
    "FoodName": "standardized food name including size if needed",
    "ServingQuantity": 1.0,
    "ServingUnit": "unit (e.g., g, mL, cup, slice, piece)",
    "CaloriesPerServing": integer,
    "ProteinPerServing": float (grams),
    "FibrePerServing": float (grams) or null,
    "CarbsPerServing": float (grams) or null,
    "FatPerServing": float (grams) or null,
    "SaturatedFatPerServing": float (grams) or null,
    "SugarPerServing": float (grams) or null,
    "SodiumPerServing": float (mg) or null,
    "Confidence": "High" or "Medium" or "Low"
  }
]

Serving size rules:
- Prefer measurable units when possible: use grams (g) for solids and milliliters (mL) for liquids.
- Avoid vague units like "serving" for basics such as milk, yogurt, rice, cereal, or vegetables.
- Use "serving" ONLY for named menu items or combo meals, and include the size in FoodName (e.g., "Large Tropical Whopper Meal").
- For discrete items, use clear units like piece, slice, egg, can, bar.

When size variants exist for menu items or branded meals, include small, medium, and large entries. Otherwise return the most common measurable serving sizes."""

    Content = GetOpenAiContent(
        [
            {"role": "system", "content": SystemPrompt},
            {"role": "user", "content": f"Look up nutritional information for: {Query}"}
        ],
        Temperature=0.3,
        MaxTokens=700
    )
    try:
        FoodData = ParseLookupJson(Content)
    except ValueError:
        RetryContent, _RetryModelUsed = GetOpenAiContentWithModel(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a formatter. Return ONLY a JSON array of 1-3 objects "
                        "with the required fields. No extra text."
                    )
                },
                {"role": "user", "content": Content}
            ],
            Temperature=0.1,
            MaxTokens=400
        )
        FoodData = ParseLookupJson(RetryContent)
    if not isinstance(FoodData, (dict, list)):
        raise ValueError("Invalid AI response format.")

    if isinstance(FoodData, dict):
        FoodData = [FoodData]
    if not isinstance(FoodData, list):
        raise ValueError("Invalid AI response format.")

    Results: list[FoodLookupResult] = []
    for Item in FoodData:
        if not isinstance(Item, dict):
            continue
        Results.append(NormalizeFoodLookupResult(Item, Query))

    if not Results:
        raise ValueError("No results returned from AI.")

    return Results


def LookupFoodByImage(ImageBase64: str) -> list[FoodLookupResult]:
    """
    Analyze a food/meal image and return nutritional information for each ingredient.
    
    Args:
        ImageBase64: Base64-encoded image string (without data:image prefix)
    
    Returns:
        List of FoodLookupResult for each identified ingredient
    
    Raises:
        ValueError: If OpenAI API key not configured or invalid response
    """
    if not Settings.OpenAiApiKey:
        raise ValueError("OpenAI API key not configured.")

    SystemPrompt = """You are a nutrition assistant that analyzes food images. Identify all visible foods/ingredients and estimate their quantities and nutritional values.

Return ONLY a JSON array of objects with these exact fields:
[
  {
    "FoodName": "ingredient name",
    "ServingQuantity": estimated quantity as float,
    "ServingUnit": "unit (e.g., g, mL, cup, tbsp, slice)",
    "CaloriesPerServing": integer,
    "ProteinPerServing": float (grams),
    "FibrePerServing": float (grams) or null,
    "CarbsPerServing": float (grams) or null,
    "FatPerServing": float (grams) or null,
    "SaturatedFatPerServing": float (grams) or null,
    "SugarPerServing": float (grams) or null,
    "SodiumPerServing": float (mg) or null,
    "Confidence": "High" or "Medium" or "Low"
  }
]

Serving size rules:
- Prefer measurable units when possible: use grams (g) for solids and milliliters (mL) for liquids.
- For discrete items, use clear units like piece, slice, egg, can, bar.
- Use "serving" ONLY for named menu items or combo meals, and include the size in FoodName.

Provide reasonable estimates based on portion size visible in the image."""

    Payload = {
        "model": "gpt-4o",  # Vision requires gpt-4o or gpt-4-turbo
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": SystemPrompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{ImageBase64}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    Headers = {
        "Authorization": f"Bearer {Settings.OpenAiApiKey}",
        "Content-Type": "application/json"
    }

    Response = httpx.post(
        "https://api.openai.com/v1/chat/completions",  # Must use standard endpoint for vision
        headers=Headers,
        json=Payload,
        timeout=60.0
    )
    Response.raise_for_status()
    
    Data = Response.json()
    Content = Data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    if not Content:
        raise ValueError("No response from AI.")

    # Parse JSON response
    try:
        # Handle markdown code blocks if present
        if "```json" in Content:
            Content = Content.split("```json")[1].split("```")[0].strip()
        elif "```" in Content:
            Content = Content.split("```")[1].split("```")[0].strip()
        
        FoodsData = json.loads(Content)
        
        if not isinstance(FoodsData, list):
            raise ValueError("Expected array of foods from AI response.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid AI response format: {e}")

    Results = []
    for FoodData in FoodsData:
        ServingQuantity = float(FoodData.get("ServingQuantity", 1.0))
        ServingUnit = FoodData.get("ServingUnit", "serving")
        ServingQuantity, ServingUnit = NormalizeServingSize(ServingQuantity, ServingUnit)
        Results.append(FoodLookupResult(
            FoodName=FoodData.get("FoodName", "Unknown Food"),
            ServingQuantity=ServingQuantity,
            ServingUnit=ServingUnit,
            CaloriesPerServing=int(FoodData.get("CaloriesPerServing", 0)),
            ProteinPerServing=float(FoodData.get("ProteinPerServing", 0)),
            FibrePerServing=float(FoodData["FibrePerServing"]) if FoodData.get("FibrePerServing") is not None else None,
            CarbsPerServing=float(FoodData["CarbsPerServing"]) if FoodData.get("CarbsPerServing") is not None else None,
            FatPerServing=float(FoodData["FatPerServing"]) if FoodData.get("FatPerServing") is not None else None,
            SaturatedFatPerServing=float(FoodData["SaturatedFatPerServing"]) if FoodData.get("SaturatedFatPerServing") is not None else None,
            SugarPerServing=float(FoodData["SugarPerServing"]) if FoodData.get("SugarPerServing") is not None else None,
            SodiumPerServing=float(FoodData["SodiumPerServing"]) if FoodData.get("SodiumPerServing") is not None else None,
            Source="AI-Vision",
            Confidence=FoodData.get("Confidence", "Medium")
        ))

    return Results


def LookupFoodByBarcode(Barcode: str) -> Optional[FoodLookupResult]:
    """
    Look up food by barcode using Open Food Facts API (free).
    
    Args:
        Barcode: Product barcode (EAN/UPC)
    
    Returns:
        FoodLookupResult if found, None otherwise
    """
    # Open Food Facts API - free, no key required
    Url = f"https://world.openfoodfacts.org/api/v2/product/{Barcode}.json"
    
    try:
        Response = httpx.get(Url, timeout=10.0)
        Response.raise_for_status()
        Data = Response.json()
        
        if Data.get("status") != 1:
            return None  # Product not found
        
        Product = Data.get("product", {})
        Nutriments = Product.get("nutriments", {})
        
        # Get product name
        FoodName = Product.get("product_name") or Product.get("generic_name") or f"Product {Barcode}"
        
        # Get serving size
        ServingSize = Product.get("serving_size", "100g")
        ServingQuantity = 100.0  # Default to 100g
        ServingUnit = "g"
        
        # Parse serving size if it contains numbers
        try:
            import re
            Match = re.search(r'(\d+\.?\d*)\s*([a-zA-Z]+)', ServingSize)
            if Match:
                ServingQuantity = float(Match.group(1))
                ServingUnit = Match.group(2)
        except:
            pass
        
        # Get nutritional values per 100g (Open Food Facts standard)
        Calories = int(Nutriments.get("energy-kcal_100g", 0))
        Protein = float(Nutriments.get("proteins_100g", 0))
        Fibre = float(Nutriments.get("fiber_100g", 0)) if "fiber_100g" in Nutriments else None
        Carbs = float(Nutriments.get("carbohydrates_100g", 0)) if "carbohydrates_100g" in Nutriments else None
        Fat = float(Nutriments.get("fat_100g", 0)) if "fat_100g" in Nutriments else None
        SaturatedFat = float(Nutriments.get("saturated-fat_100g", 0)) if "saturated-fat_100g" in Nutriments else None
        Sugar = float(Nutriments.get("sugars_100g", 0)) if "sugars_100g" in Nutriments else None
        Sodium = float(Nutriments.get("sodium_100g", 0) * 1000) if "sodium_100g" in Nutriments else None  # Convert g to mg
        
        # Adjust values to per serving
        Factor = ServingQuantity / 100.0
        
        return FoodLookupResult(
            FoodName=FoodName,
            ServingQuantity=ServingQuantity,
            ServingUnit=ServingUnit,
            CaloriesPerServing=int(Calories * Factor),
            ProteinPerServing=round(Protein * Factor, 1),
            FibrePerServing=round(Fibre * Factor, 1) if Fibre is not None else None,
            CarbsPerServing=round(Carbs * Factor, 1) if Carbs is not None else None,
            FatPerServing=round(Fat * Factor, 1) if Fat is not None else None,
            SaturatedFatPerServing=round(SaturatedFat * Factor, 1) if SaturatedFat is not None else None,
            SugarPerServing=round(Sugar * Factor, 1) if Sugar is not None else None,
            SodiumPerServing=round(Sodium * Factor, 1) if Sodium is not None else None,
            Source="OpenFoodFacts",
            Confidence="High"
        )
    
    except (httpx.HTTPError, Exception):
        return None


def SearchAustralianFoodSuggestions(Query: str, Limit: int = 10) -> list[str]:
    """
    Search for Australian food suggestions based on partial query (autocomplete).
    Returns list of food name suggestions prioritizing Australian brands and products.
    
    Args:
        Query: Partial food name (2+ characters)
        Limit: Maximum number of suggestions (default 10)
    
    Returns:
        List of food name strings
    """
    if not Settings.OpenAiApiKey or len(Query) < 2:
        return []

    Limit = min(Limit, 5)

    SystemPrompt = """You are a food search assistant specialising in Australian foods and brands.

Input will be a single, messy line describing ONE meal/order (combined), possibly with typos and informal wording.

Task:
- Infer the best matching Australian food entry for the entire line as one combined order (do not split into individual ingredients/items).
- Prefer Australian brands and menus (eg Hungry Jack's AU, Macca's AU, KFC AU, Sanitarium, Arnott's).
- Be robust to spelling mistakes.
- Preserve key qualifiers when present (eg Large/Medium/Small, lite/skim, flavour, meal/combo, shake, sundae).
- Do not invent specific products. If an exact branded match is unclear, return a generic combined description that is still plausible in Australia.

Output:
Return ONLY a JSON array of strings, ordered by relevance, max 5.
- If size is specified, return exactly 1 suggestion reflecting that size.
- If size is NOT specified and size variants commonly exist, return 2-3 suggestions varying only by size (eg Small/Medium/Large), keeping all other details the same.
No explanations. No extra fields."""

    UserPrompt = Query.strip()

    def TryParseSuggestions(ContentValue: str) -> list[str] | None:
        if not ContentValue:
            return None
        Cleaned = ContentValue.strip()
        if "```json" in Cleaned:
            Cleaned = Cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in Cleaned:
            Cleaned = Cleaned.split("```")[1].split("```")[0].strip()
        try:
            Parsed = json.loads(Cleaned)
            if isinstance(Parsed, list):
                return [str(Item) for Item in Parsed]
        except json.JSONDecodeError:
            pass
        Start = Cleaned.find("[")
        End = Cleaned.rfind("]")
        if Start != -1 and End != -1 and End > Start:
            Candidate = Cleaned[Start:End + 1]
            try:
                Parsed = json.loads(Candidate)
                if isinstance(Parsed, list):
                    return [str(Item) for Item in Parsed]
            except json.JSONDecodeError:
                return None
        return None

    try:
        AutosuggestModel = Settings.OpenAiAutosuggestModel or "gpt-5-mini"
        try:
            Content, _ModelUsed = GetOpenAiContentForModel(
                AutosuggestModel,
                [
                    {"role": "system", "content": SystemPrompt},
                    {"role": "user", "content": UserPrompt}
                ],
                Temperature=0.4,
                MaxTokens=200
            )
        except Exception:
            Content, _ModelUsed = GetOpenAiContentWithModel(
                [
                    {"role": "system", "content": SystemPrompt},
                    {"role": "user", "content": UserPrompt}
                ],
                Temperature=0.4,
                MaxTokens=200
            )

        Suggestions = TryParseSuggestions(Content)
        if Suggestions is None:
            RetryContent, _RetryModelUsed = GetOpenAiContentWithModel(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a formatter. Return ONLY a JSON array of strings. "
                            "No extra text."
                        )
                    },
                    {"role": "user", "content": Content}
                ],
                Temperature=0.1,
                MaxTokens=200
            )
            Suggestions = TryParseSuggestions(RetryContent)
        if isinstance(Suggestions, list):
            return [str(S) for S in Suggestions[:Limit]]
        return []
    except Exception as Error:
        Logger.error(f"Error during food search autocomplete: {Error}", exc_info=True)
        return []
