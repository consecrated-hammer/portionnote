"""
Rate limiter for OpenFoodFacts API requests.

Enforces rate limits per OpenFoodFacts documentation:
- 100 req/min for product queries
- 10 req/min for search queries
- 2 req/min for facet queries
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import deque


class RateLimiter:
    """Token bucket rate limiter with per-minute tracking."""
    
    def __init__(self, MaxRequests: int, WindowSeconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            MaxRequests: Maximum requests allowed in the window
            WindowSeconds: Time window in seconds (default 60 for per-minute)
        """
        self.MaxRequests = MaxRequests
        self.WindowSeconds = WindowSeconds
        self.Requests: deque = deque()
        self.Lock = asyncio.Lock()
    
    async def Acquire(self, Wait: bool = True) -> bool:
        """
        Acquire permission to make a request.
        
        Args:
            Wait: If True, wait until a slot is available. If False, return immediately.
            
        Returns:
            True if request can proceed, False if rate limit reached (when Wait=False)
        """
        async with self.Lock:
            Now = datetime.now()
            Cutoff = Now - timedelta(seconds=self.WindowSeconds)
            
            # Remove expired requests
            while self.Requests and self.Requests[0] < Cutoff:
                self.Requests.popleft()
            
            # Check if we're under the limit
            if len(self.Requests) < self.MaxRequests:
                self.Requests.append(Now)
                return True
            
            # If not waiting, return False
            if not Wait:
                return False
            
            # Calculate wait time until oldest request expires
            OldestRequest = self.Requests[0]
            WaitUntil = OldestRequest + timedelta(seconds=self.WindowSeconds)
            WaitSeconds = (WaitUntil - Now).total_seconds()
            
            if WaitSeconds > 0:
                await asyncio.sleep(WaitSeconds + 0.1)  # Add small buffer
            
            # Retry acquisition
            return await self.Acquire(Wait=True)
    
    def GetCurrentCount(self) -> int:
        """Get current number of requests in the window."""
        Now = datetime.now()
        Cutoff = Now - timedelta(seconds=self.WindowSeconds)
        
        # Count valid requests
        Count = sum(1 for Timestamp in self.Requests if Timestamp >= Cutoff)
        return Count
    
    def GetStats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        Count = self.GetCurrentCount()
        Remaining = self.MaxRequests - Count
        PercentUsed = (Count / self.MaxRequests) * 100 if self.MaxRequests > 0 else 0
        
        return {
            "max_requests": self.MaxRequests,
            "window_seconds": self.WindowSeconds,
            "current_count": Count,
            "remaining": Remaining,
            "percent_used": round(PercentUsed, 1)
        }


class OpenFoodFactsRateLimiter:
    """Rate limiters for different OpenFoodFacts API endpoints."""
    
    # Per OpenFoodFacts documentation
    ProductLimiter = RateLimiter(MaxRequests=100, WindowSeconds=60)  # 100/min
    SearchLimiter = RateLimiter(MaxRequests=10, WindowSeconds=60)    # 10/min
    FacetLimiter = RateLimiter(MaxRequests=2, WindowSeconds=60)      # 2/min
    
    @classmethod
    async def AcquireProduct(cls, Wait: bool = True) -> bool:
        """Acquire permission for a product query."""
        return await cls.ProductLimiter.Acquire(Wait)
    
    @classmethod
    async def AcquireSearch(cls, Wait: bool = True) -> bool:
        """Acquire permission for a search query."""
        return await cls.SearchLimiter.Acquire(Wait)
    
    @classmethod
    async def AcquireFacet(cls, Wait: bool = True) -> bool:
        """Acquire permission for a facet query."""
        return await cls.FacetLimiter.Acquire(Wait)
    
    @classmethod
    def GetAllStats(cls) -> Dict[str, Dict]:
        """Get statistics for all rate limiters."""
        return {
            "product": cls.ProductLimiter.GetStats(),
            "search": cls.SearchLimiter.GetStats(),
            "facet": cls.FacetLimiter.GetStats()
        }
