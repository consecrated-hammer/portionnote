"""
Tests for rate limiter.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from app.services.rate_limiter import RateLimiter, OpenFoodFactsRateLimiter


@pytest.mark.asyncio
async def TestRateLimiterBasic():
    """Test basic rate limiter functionality."""
    Limiter = RateLimiter(MaxRequests=3, WindowSeconds=1)
    
    # First 3 requests should succeed immediately
    for _ in range(3):
        Result = await Limiter.Acquire(Wait=False)
        assert Result is True
    
    # 4th request should fail when not waiting
    Result = await Limiter.Acquire(Wait=False)
    assert Result is False
    
    # Stats should show we're at the limit
    Stats = Limiter.GetStats()
    assert Stats["current_count"] == 3
    assert Stats["remaining"] == 0
    assert Stats["percent_used"] == 100.0


@pytest.mark.asyncio
async def TestRateLimiterWait():
    """Test rate limiter waiting functionality."""
    Limiter = RateLimiter(MaxRequests=2, WindowSeconds=1)
    
    # Use up the quota
    await Limiter.Acquire(Wait=False)
    await Limiter.Acquire(Wait=False)
    
    # Next request should wait ~1 second
    StartTime = datetime.now()
    Result = await Limiter.Acquire(Wait=True)
    EndTime = datetime.now()
    
    assert Result is True
    ElapsedSeconds = (EndTime - StartTime).total_seconds()
    assert ElapsedSeconds >= 1.0
    assert ElapsedSeconds < 1.5  # Should not wait too long


@pytest.mark.asyncio
async def TestRateLimiterExpiry():
    """Test that old requests expire properly."""
    Limiter = RateLimiter(MaxRequests=2, WindowSeconds=1)
    
    # Use up the quota
    await Limiter.Acquire(Wait=False)
    await Limiter.Acquire(Wait=False)
    
    # Wait for window to expire
    await asyncio.sleep(1.1)
    
    # Should be able to make requests again
    Result = await Limiter.Acquire(Wait=False)
    assert Result is True


@pytest.mark.asyncio
async def TestRateLimiterStats():
    """Test rate limiter statistics."""
    Limiter = RateLimiter(MaxRequests=5, WindowSeconds=60)
    
    # Make 3 requests
    for _ in range(3):
        await Limiter.Acquire(Wait=False)
    
    Stats = Limiter.GetStats()
    assert Stats["max_requests"] == 5
    assert Stats["window_seconds"] == 60
    assert Stats["current_count"] == 3
    assert Stats["remaining"] == 2
    assert Stats["percent_used"] == 60.0


@pytest.mark.asyncio
async def TestOpenFoodFactsProductLimiter():
    """Test OpenFoodFacts product rate limiter."""
    # Get initial stats
    StatsBefore = OpenFoodFactsRateLimiter.ProductLimiter.GetStats()
    InitialCount = StatsBefore["current_count"]
    
    # Acquire a slot
    Result = await OpenFoodFactsRateLimiter.AcquireProduct(Wait=False)
    assert Result is True
    
    # Stats should reflect the new request
    StatsAfter = OpenFoodFactsRateLimiter.ProductLimiter.GetStats()
    assert StatsAfter["current_count"] == InitialCount + 1
    assert StatsAfter["max_requests"] == 100


@pytest.mark.asyncio
async def TestOpenFoodFactsSearchLimiter():
    """Test OpenFoodFacts search rate limiter."""
    # Get initial stats
    StatsBefore = OpenFoodFactsRateLimiter.SearchLimiter.GetStats()
    InitialCount = StatsBefore["current_count"]
    
    # Acquire a slot
    Result = await OpenFoodFactsRateLimiter.AcquireSearch(Wait=False)
    assert Result is True
    
    # Stats should reflect the new request
    StatsAfter = OpenFoodFactsRateLimiter.SearchLimiter.GetStats()
    assert StatsAfter["current_count"] == InitialCount + 1
    assert StatsAfter["max_requests"] == 10


def TestGetAllStats():
    """Test getting all rate limiter statistics."""
    AllStats = OpenFoodFactsRateLimiter.GetAllStats()
    
    assert "product" in AllStats
    assert "search" in AllStats
    assert "facet" in AllStats
    
    assert AllStats["product"]["max_requests"] == 100
    assert AllStats["search"]["max_requests"] == 10
    assert AllStats["facet"]["max_requests"] == 2


@pytest.mark.asyncio
async def TestConcurrentRequests():
    """Test rate limiter with concurrent requests."""
    Limiter = RateLimiter(MaxRequests=5, WindowSeconds=1)
    
    # Try to make 10 concurrent requests (only 5 should succeed immediately)
    Tasks = [Limiter.Acquire(Wait=False) for _ in range(10)]
    Results = await asyncio.gather(*Tasks)
    
    SuccessCount = sum(1 for R in Results if R is True)
    FailCount = sum(1 for R in Results if R is False)
    
    assert SuccessCount == 5
    assert FailCount == 5
