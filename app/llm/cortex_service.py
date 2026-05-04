"""
CortexAPIService — composes APIM auth + HTTP calls into one reusable service.

Mirrors the shape of the production CortexAPIService (APIMClient + APIClient)
but uses httpx directly so we don't depend on the `shared.*` packages.

Singleton accessor: get_cortex_service().
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.llm.apim_auth import APIMTokenManager

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}


class CortexAPIService:
    """APIM-authenticated HTTP service against the Cortex OpenAI gateway."""

    def __init__(
        self,
        base_url: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str,
        token_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.apim = APIMTokenManager(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            token_url=token_url,
        )

        # Reusable connection pools (important for parallel runs)
        self._client = httpx.Client(timeout=timeout)
        self._aclient = httpx.AsyncClient(timeout=timeout)

    # ------------------------------------------------------------------
    def _build_headers(self, content_type: str, extra: Optional[dict] = None) -> dict:
        token = self.apim.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": content_type,
        }
        if extra:
            headers.update(extra)
        return headers

    def _full_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    # ------------------------------------------------------------------
    def call(
        self,
        endpoint: str,
        method: str = "GET",
        query_params: Optional[dict] = None,
        data: Optional[dict[str, Any]] = None,
        content_type: str = "application/json",
        extra_headers: Optional[dict] = None,
    ) -> httpx.Response:
        """Synchronous request with retries + token-refresh on 401."""
        url = self._full_url(endpoint)
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            headers = self._build_headers(content_type, extra_headers)
            try:
                resp = self._client.request(
                    method=method.upper(),
                    url=url,
                    params=query_params,
                    json=data if content_type == "application/json" else None,
                    headers=headers,
                )
            except httpx.HTTPError as e:
                last_exc = e
                logger.warning(f"Cortex {method} {endpoint} network error (attempt {attempt}): {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise

            if resp.status_code == 401:
                logger.warning("Cortex returned 401; invalidating token and retrying.")
                self.apim.invalidate()
                if attempt < self.max_retries:
                    continue
                resp.raise_for_status()

            if resp.status_code in _RETRYABLE_STATUS and attempt < self.max_retries:
                logger.warning(
                    f"Cortex {method} {endpoint} returned {resp.status_code} "
                    f"(attempt {attempt}); retrying."
                )
                time.sleep(2 ** (attempt - 1))
                continue

            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Cortex {method} {endpoint} failed with HTTP {resp.status_code}. "
                    f"Response body: {resp.text[:1000]}"
                )
            return resp

        # Should be unreachable, but keep type-checker happy
        raise RuntimeError(f"Cortex call failed after {self.max_retries} attempts: {last_exc}")

    async def acall(
        self,
        endpoint: str,
        method: str = "GET",
        query_params: Optional[dict] = None,
        data: Optional[dict[str, Any]] = None,
        content_type: str = "application/json",
        extra_headers: Optional[dict] = None,
    ) -> httpx.Response:
        """Async variant of call()."""
        import asyncio  # local import to avoid global asyncio dep at module load

        url = self._full_url(endpoint)
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            headers = self._build_headers(content_type, extra_headers)
            try:
                resp = await self._aclient.request(
                    method=method.upper(),
                    url=url,
                    params=query_params,
                    json=data if content_type == "application/json" else None,
                    headers=headers,
                )
            except httpx.HTTPError as e:
                last_exc = e
                logger.warning(f"Cortex async {method} {endpoint} network error (attempt {attempt}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** (attempt - 1))
                    continue
                raise

            if resp.status_code == 401:
                logger.warning("Cortex returned 401; invalidating token and retrying.")
                self.apim.invalidate()
                if attempt < self.max_retries:
                    continue
                resp.raise_for_status()

            if resp.status_code in _RETRYABLE_STATUS and attempt < self.max_retries:
                logger.warning(
                    f"Cortex async {method} {endpoint} returned {resp.status_code} "
                    f"(attempt {attempt}); retrying."
                )
                await asyncio.sleep(2 ** (attempt - 1))
                continue

            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Cortex async {method} {endpoint} failed with HTTP {resp.status_code}. "
                    f"Response body: {resp.text[:1000]}"
                )
            return resp

        raise RuntimeError(f"Cortex async call failed after {self.max_retries} attempts: {last_exc}")

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass


# ----------------------------------------------------------------------
# Singleton
# ----------------------------------------------------------------------
_service: Optional[CortexAPIService] = None
_service_lock = threading.Lock()


def get_cortex_service() -> CortexAPIService:
    """Lazy, thread-safe singleton."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = CortexAPIService(
                    base_url=settings.cortex_openai_base,
                    tenant_id=settings.apim_tenant_id,
                    client_id=settings.apim_client_id,
                    client_secret=settings.apim_client_secret,
                    scope=settings.apim_scope,
                    token_url=settings.apim_token_url or None,
                )
                logger.info(f"CortexAPIService initialized (base_url={settings.cortex_openai_base}).")
    return _service
