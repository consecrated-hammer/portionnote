from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import Settings
from app.routes import (
    AiSuggestionRouter,
    AuthRouter,
    DailyLogRouter,
    FoodLookupRouter,
    FoodRouter,
    HealthRouter,
    LogRouter,
    MealTemplateRouter,
    ScheduleRouter,
    SettingsRouter,
    SummaryRouter
)
from app.utils.database import GetConnection
from app.utils.logger import GetLogger
from app.utils.migrations import RunMigrations
from app.utils.seed import SeedDatabase

Logger = GetLogger("main")
RequestLogger = GetLogger("requests")

@asynccontextmanager
async def Lifespan(app: FastAPI):
    Logger.info("Starting Portion Note API...")
    try:
        RunMigrations()
        Logger.info("Migrations completed")
        SeedDatabase()
        Logger.info("Database seeded")
        Logger.info("Application ready")
        yield
    except Exception as Error:
        Logger.error(f"Startup error: {Error}", exc_info=True)
        raise
    finally:
        Logger.info("Shutting down...")
        Connection = GetConnection()
        Connection.close()
        Logger.info("Shutdown complete")


App = FastAPI(title="Portion Note API", lifespan=Lifespan)


@App.middleware("http")
async def LogRequests(Request: Request, CallNext):
    if not Request.url.path.startswith("/api"):
        return await CallNext(Request)

    StartTime = perf_counter()
    ClientHost = Request.client.host if Request.client else "unknown"
    PathWithQuery = Request.url.path
    if Request.url.query:
        PathWithQuery = f"{PathWithQuery}?{Request.url.query}"

    try:
        Response = await CallNext(Request)
    except Exception as ErrorValue:
        DurationMs = int((perf_counter() - StartTime) * 1000)
        RequestLogger.error(
            f"{Request.method} {PathWithQuery} 500 {DurationMs}ms client={ClientHost}",
            exc_info=True
        )
        raise

    DurationMs = int((perf_counter() - StartTime) * 1000)
    StatusCode = Response.status_code

    if StatusCode >= 500:
        RequestLogger.error(f"{Request.method} {PathWithQuery} {StatusCode} {DurationMs}ms client={ClientHost}")
    elif StatusCode >= 400:
        RequestLogger.warning(f"{Request.method} {PathWithQuery} {StatusCode} {DurationMs}ms client={ClientHost}")
    else:
        RequestLogger.info(f"{Request.method} {PathWithQuery} {StatusCode} {DurationMs}ms client={ClientHost}")

    return Response

App.add_middleware(
    SessionMiddleware,
    secret_key=Settings.SessionSecret,
    session_cookie=Settings.SessionCookieName,
    max_age=Settings.SessionDays * 24 * 60 * 60,
    same_site="lax",
    https_only=(Settings.Environment == "production")
)

# Allow multiple origins for development
AllowedOrigins = [Settings.WebOrigin]
# Add common development origins
if Settings.Environment == "development":
    AllowedOrigins.extend([
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ])
    # Add any http://* origin that might be used locally
    import re
    # This will be checked per-request below

App.add_middleware(
    CORSMiddleware,
    allow_origins=AllowedOrigins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"http://192\.168\.\d+\.\d+:\d+" if Settings.Environment == "development" else None
)

App.include_router(HealthRouter, prefix="/api/health")
App.include_router(AuthRouter, prefix="/api/auth")
App.include_router(FoodRouter, prefix="/api/foods")
App.include_router(FoodLookupRouter, prefix="/api/food-lookup")
App.include_router(DailyLogRouter, prefix="/api/daily-logs")
App.include_router(SummaryRouter, prefix="/api/summary")
App.include_router(MealTemplateRouter, prefix="/api/meal-templates")
App.include_router(AiSuggestionRouter, prefix="/api/suggestions")
App.include_router(ScheduleRouter, prefix="/api/schedule")
App.include_router(SettingsRouter, prefix="/api/settings")
App.include_router(LogRouter, prefix="/api/logs")

# Global exception handler
@App.exception_handler(Exception)
async def GlobalExceptionHandler(Request: Request, Exc: Exception):
    Logger.error(
        f"Unhandled exception: {type(Exc).__name__}: {Exc}",
        exc_info=True,
        extra={"path": Request.url.path, "method": Request.method}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. Please try again later."}
    )

# Static file serving for SPA
StaticDir = Path(__file__).parent / "static"
if StaticDir.exists():
    # Mount assets directory
    AssetsDir = StaticDir / "assets"
    if AssetsDir.exists():
        App.mount("/assets", StaticFiles(directory=str(AssetsDir)), name="assets")

    ImagesDir = StaticDir / "images"
    if ImagesDir.exists():
        App.mount("/images", StaticFiles(directory=str(ImagesDir)), name="images")

    SourceIconsDir = StaticDir / "source-icons"
    if SourceIconsDir.exists():
        App.mount("/source-icons", StaticFiles(directory=str(SourceIconsDir)), name="source-icons")

    FaviconPath = StaticDir / "favicon.svg"
    if FaviconPath.exists():
        @App.get("/favicon.svg", response_class=FileResponse, include_in_schema=False)
        async def ServeFavicon():
            return FileResponse(str(FaviconPath))

    # Serve index.html at root
    @App.get("/", response_class=FileResponse, include_in_schema=False)
    async def ServeRoot():
        return FileResponse(str(StaticDir / "index.html"))
    
    # SPA routing fallback - only matches GET requests for non-API, non-asset paths
    @App.get("/{full_path:path}", response_class=FileResponse, include_in_schema=False)
    async def ServeSPA(full_path: str):
        return FileResponse(str(StaticDir / "index.html"))
else:
    @App.get("/", include_in_schema=False)
    async def Root() -> dict[str, str]:
        return {
            "name": "Portion Note API",
            "status": "running",
            "environment": Settings.Environment
        }
