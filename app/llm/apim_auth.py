"""
APIM OAuth2 client-credentials token manager.

Thread-safe, caches the access token until 60s before expiry, then refreshes.
One instance per (tenant, client_id) — created lazily by cortex_service.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_TOKEN_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
_REFRESH_LEEWAY_SECONDS = 60  # refresh this many seconds before actual expiry


class APIMTokenManager:
    """Acquires and caches an APIM OAuth2 bearer token (client_credentials flow)."""

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str,
        token_url: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        if not (tenant_id and client_id and client_secret and scope):
            raise ValueError(
                "APIM auth misconfigured. Set APIM_TENANT_ID, APIM_CLIENT_ID, "
                "APIM_CLIENT_SECRET, and APIM_SCOPE in your .env file."
            )
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token_url = token_url or _DEFAULT_TOKEN_URL_TEMPLATE.format(tenant_id=tenant_id)
        self._timeout = timeout

        self._lock = threading.Lock()
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0  # epoch seconds

    def get_access_token(self) -> str:
        """Return a valid bearer token, refreshing if needed."""
        now = time.time()
        # Fast path: cached token still valid
        if self._access_token and now < self._expires_at - _REFRESH_LEEWAY_SECONDS:
            return self._access_token

        with self._lock:
            # Re-check inside the lock (another thread may have refreshed)
            now = time.time()
            if self._access_token and now < self._expires_at - _REFRESH_LEEWAY_SECONDS:
                return self._access_token
            self._refresh_locked()
            return self._access_token  # type: ignore[return-value]

    def invalidate(self) -> None:
        """Force the next get_access_token() to fetch a new token."""
        with self._lock:
            self._access_token = None
            self._expires_at = 0.0

    # ------------------------------------------------------------------
    def _refresh_locked(self) -> None:
        logger.info("Acquiring new APIM access token via client_credentials flow.")
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": self._scope,
        }
        try:
            resp = httpx.post(self._token_url, data=data, timeout=self._timeout)
        except httpx.HTTPError as e:
            raise RuntimeError(f"APIM token request failed (network error): {e}") from e

        if resp.status_code != 200:
            raise RuntimeError(
                f"APIM token request failed (HTTP {resp.status_code}): {resp.text[:300]}"
            )

        try:
            payload = resp.json()
        except ValueError as e:
            raise RuntimeError(
                f"APIM token endpoint returned non-JSON response (likely a misconfigured "
                f"APIM_TENANT_ID / APIM_TOKEN_URL). Body starts with: {resp.text[:200]!r}"
            ) from e
        token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not token or not expires_in:
            raise RuntimeError(
                f"APIM token response missing access_token/expires_in: {payload}"
            )

        self._access_token = token
        self._expires_at = time.time() + int(expires_in)
        logger.info(f"APIM token acquired; valid for ~{int(expires_in)}s.")
