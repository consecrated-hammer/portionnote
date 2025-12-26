"""Frontend logging endpoint - allows frontend to send logs to backend."""
import os
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.utils.logger import GetLogger

LogRouter = APIRouter()
Logger = GetLogger("frontend")

# Rate limiting dictionary to prevent log spam
_LogCounts = {}
def _ResolveInt(Value: str | None, Default: int) -> int:
    if Value is None:
        return Default
    try:
        return int(Value)
    except ValueError:
        return Default


_MaxLogsPerMinute = _ResolveInt(os.getenv("LOG_FRONTEND_RATE_LIMIT_PER_MIN"), 0)


class FrontendLogEntry(BaseModel):
    Level: Literal["debug", "info", "warn", "error"] = "info"
    Message: str = Field(..., max_length=1000)
    Context: dict = Field(default_factory=dict, max_length=10)
    Timestamp: str


def _ReserveLogSlots(ClientId: str, Count: int) -> int:
    """Simple rate limiting - max logs per minute per client."""
    import time
    if _MaxLogsPerMinute <= 0:
        return Count

    Now = time.time()
    
    if ClientId not in _LogCounts:
        _LogCounts[ClientId] = []
    
    # Remove logs older than 1 minute
    _LogCounts[ClientId] = [T for T in _LogCounts[ClientId] if Now - T < 60]
    
    AvailableSlots = max(0, _MaxLogsPerMinute - len(_LogCounts[ClientId]))
    ReservedSlots = min(Count, AvailableSlots)
    
    if ReservedSlots > 0:
        _LogCounts[ClientId].extend([Now] * ReservedSlots)

    return ReservedSlots


def _LogEntry(Entry: FrontendLogEntry):
    ContextStr = f" | {Entry.Context}" if Entry.Context else ""
    Message = f"[FRONTEND] {Entry.Message}{ContextStr}"

    if Entry.Level == "debug":
        Logger.debug(Message)
    elif Entry.Level == "info":
        Logger.info(Message)
    elif Entry.Level == "warn":
        Logger.warning(Message)
    elif Entry.Level == "error":
        Logger.error(Message)


@LogRouter.post("/", status_code=204, tags=["Logging"])
async def LogFromFrontend(Entry: FrontendLogEntry, Request: Request):
    """
    Receive logs from frontend and write to backend log file.
    Rate limited to prevent spam.
    """
    ClientHost = Request.client.host if Request.client else "unknown"
    ClientId = f"{ClientHost}-{Entry.Timestamp[:10]}"

    ReservedSlots = _ReserveLogSlots(ClientId, 1)
    if ReservedSlots <= 0:
        return

    _LogEntry(Entry)

    return  # 204 No Content


@LogRouter.post("/batch", status_code=204, tags=["Logging"])
async def LogFromFrontendBatch(Entries: list[FrontendLogEntry], Request: Request):
    if not Entries:
        return

    ClientHost = Request.client.host if Request.client else "unknown"
    ClientId = f"{ClientHost}-{Entries[0].Timestamp[:10]}"

    ReservedSlots = _ReserveLogSlots(ClientId, len(Entries))
    if ReservedSlots <= 0:
        return

    for Entry in Entries[:ReservedSlots]:
        _LogEntry(Entry)

    if ReservedSlots < len(Entries):
        DroppedCount = len(Entries) - ReservedSlots
        Logger.warning(f"[FRONTEND] Dropped {DroppedCount} log entries due to rate limit")

    return  # 204 No Content
