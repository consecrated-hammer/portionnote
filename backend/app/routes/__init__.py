from app.routes.auth import AuthRouter
from app.routes.health import HealthRouter
from app.routes.foods import FoodRouter
from app.routes.food_lookup import FoodLookupRouter
from app.routes.daily_logs import DailyLogRouter
from app.routes.summary import SummaryRouter
from app.routes.meal_templates import MealTemplateRouter
from app.routes.ai_suggestions import AiSuggestionRouter
from app.routes.schedule import ScheduleRouter
from app.routes.settings import SettingsRouter
from app.routes.logs import LogRouter
from app.routes.admin_users import AdminUserRouter

__all__ = [
    "AuthRouter",
    "HealthRouter",
    "FoodRouter",
    "FoodLookupRouter",
    "DailyLogRouter",
    "SummaryRouter",
    "MealTemplateRouter",
    "AiSuggestionRouter",
    "ScheduleRouter",
    "SettingsRouter",
    "LogRouter",
    "AdminUserRouter"
]
