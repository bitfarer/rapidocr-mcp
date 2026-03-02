"""URL download and caching utilities."""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Any
import httpx
from loguru import logger

from ..config import settings


class URLDownloader:
    """Async URL image downloader with caching."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._cache_dir = Path(settings.resolved_cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    def _get_cache_path(self, url: str) -> Path:
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return self._cache_dir / f"{url_hash}.cache"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        if not cache_path.exists():
            return False
        if settings.url_cache_ttl == 0:
            return True
        age = time.time() - cache_path.stat().st_mtime
        return age < settings.url_cache_ttl

    async def download(self, url: str, use_cache: bool = True) -> bytes:
        """Download image from URL, optionally using cache."""
        cache_path = self._get_cache_path(url)

        if use_cache and self._is_cache_valid(cache_path):
            logger.info(f"Using cached image for {url}")
            return cache_path.read_bytes()

        logger.info(f"Downloading image from {url}")
        client = await self._get_client()
        response = await client.get(url)
        response.raise_for_status()
        data = response.content

        if use_cache:
            cache_path.write_bytes(data)
            logger.info(f"Cached image to {cache_path}")

        return data

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


url_downloader = URLDownloader()
