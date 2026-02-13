"""Shared HTTP client session for optimal connection pooling."""

import aiohttp
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global session instance
_shared_session: Optional[aiohttp.ClientSession] = None


async def get_shared_session() -> aiohttp.ClientSession:
    """
    Get or create the shared aiohttp session.

    Thread-safe lazy initialization. Session is reused across all analyzers.
    Connection pool configured for SEO audit use case.
    """
    global _shared_session

    if _shared_session is None or _shared_session.closed:
        connector = aiohttp.TCPConnector(
            limit=50,  # Max total connections
            limit_per_host=10,  # Max per domain
            ttl_dns_cache=300,  # Cache DNS for 5 minutes
            ssl=False,  # Disable SSL verification for SEO crawling
        )

        timeout = aiohttp.ClientTimeout(total=60, connect=10)

        _shared_session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; SEOAuditBot/1.0)',
            },
        )

        logger.info("Created shared HTTP session with connection pool (limit=50)")

    return _shared_session


async def close_shared_session():
    """Close the shared session (called on app shutdown)."""
    global _shared_session

    if _shared_session and not _shared_session.closed:
        await _shared_session.close()
        _shared_session = None
        logger.info("Closed shared HTTP session")
