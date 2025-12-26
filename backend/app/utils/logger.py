"""
Centralized logging configuration for Portion Note.
Logs to both console and rotating file with appropriate levels.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _ResolveLogLevel(LevelName: str, Default: str) -> int:
    CleanLevel = (LevelName or Default).upper()
    Resolved = logging.getLevelName(CleanLevel)
    if isinstance(Resolved, int):
        return Resolved
    return logging.getLevelName(Default.upper())


def _ResolveInt(Value: str | None, Default: int) -> int:
    if Value is None:
        return Default
    try:
        return int(Value)
    except ValueError:
        return Default


def SetupLogging(LogLevel: str = "INFO") -> logging.Logger:
    """
    Configure logging with console and rotating file handlers.
    
    Args:
        LogLevel: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    EnvLogLevel = os.getenv("LOG_LEVEL", LogLevel)
    ConsoleLevel = os.getenv("LOG_CONSOLE_LEVEL", EnvLogLevel)
    FileLevel = os.getenv("LOG_FILE_LEVEL", EnvLogLevel)
    LogFileName = os.getenv("LOG_FILE_NAME", "portionnote.log")
    MaxBytes = _ResolveInt(os.getenv("LOG_MAX_BYTES"), 10 * 1024 * 1024)
    BackupCount = _ResolveInt(os.getenv("LOG_BACKUP_COUNT"), 5)

    # Try /logs first (for containers), fall back to project ./logs for dev
    LogDir = Path(os.getenv("LOG_DIR", "/logs"))
    if not LogDir.is_absolute():
        ProjectRoot = Path(__file__).parent.parent.parent.parent
        LogDir = (ProjectRoot / LogDir).resolve()
    
    # If we can't write to /logs (dev environment), use project-relative path
    if not LogDir.exists():
        try:
            LogDir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fall back to project directory
            LogDir = Path(__file__).parent.parent.parent.parent / "logs"
            LogDir.mkdir(parents=True, exist_ok=True)
    
    LogFile = LogDir / LogFileName
    
    # Create logger
    Logger = logging.getLogger("portionnote")
    Logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter
    
    # Remove existing handlers
    Logger.handlers.clear()
    
    # Console handler - INFO and above
    ConsoleHandler = logging.StreamHandler(sys.stdout)
    ConsoleHandler.setLevel(_ResolveLogLevel(ConsoleLevel, "INFO"))
    ConsoleFormatter = logging.Formatter(
        "%(levelname)s:     %(message)s"
    )
    ConsoleHandler.setFormatter(ConsoleFormatter)
    
    # File handler - DEBUG and above, rotating at 10MB, keep 5 backups
    FileHandler = RotatingFileHandler(
        LogFile,
        maxBytes=MaxBytes,
        backupCount=BackupCount,
        encoding="utf-8"
    )
    FileHandler.setLevel(_ResolveLogLevel(FileLevel, "DEBUG"))
    FileFormatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    FileHandler.setFormatter(FileFormatter)
    
    Logger.addHandler(ConsoleHandler)
    Logger.addHandler(FileHandler)
    
    # Prevent propagation to root logger
    Logger.propagate = False
    
    return Logger


# Global logger instance
AppLogger = SetupLogging()


def GetLogger(Name: str) -> logging.Logger:
    """Get a child logger for a specific module."""
    return AppLogger.getChild(Name)
