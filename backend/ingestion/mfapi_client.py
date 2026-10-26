"""Minimal mfapi.in client with retries + rate limiting.

mfapi.in is a free, unauthenticated API. We're a well-behaved caller: a small
delay between requests and exponential backoff on transient failures.

Response shape:
    {
      "meta":   { "fund_house", "scheme_type", "scheme_category", "scheme_code",
                  "scheme_name", "isin_growth", "isin_div_reinvestment" },
      "status": "SUCCESS",
      "data":   [ { "date": "DD-MM-YYYY", "nav": "123.45678" }, ... ]
    }
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

logger = logging.getLogger(__name__)


class MfApiError(RuntimeError):
    """Raised when mfapi returns a non-SUCCESS status or malformed payload."""


@dataclass(frozen=True)
class NavRow:
    date: date
    nav: float


@dataclass
class SchemeData:
    scheme_code: int
    scheme_name: str
    fund_house: str | None
    scheme_category: str | None
    isin_growth: str | None
    rows: list[NavRow]


class MfApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        request_delay_ms: int | None = None,
        max_retries: int | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        s = get_settings()
        self.base_url = (base_url or s.mfapi_base_url).rstrip("/")
        self.request_delay_s = (request_delay_ms or s.mfapi_request_delay_ms) / 1000.0
        self.max_retries = max_retries or s.mfapi_max_retries
        self._client = client or httpx.Client(timeout=30.0)
        self._last_call = 0.0

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MfApiClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _throttle(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.request_delay_s:
            time.sleep(self.request_delay_s - elapsed)
        self._last_call = time.monotonic()

    def fetch_scheme(self, scheme_code: int) -> SchemeData:
        """Return the complete NAV history for a scheme."""
        self._throttle()
        payload = self._get_json(f"{self.base_url}/{scheme_code}")
        if payload.get("status") != "SUCCESS":
            raise MfApiError(f"scheme {scheme_code}: status={payload.get('status')!r}")
        meta = payload.get("meta") or {}
        rows = _parse_rows(payload.get("data") or [], scheme_code)
        return SchemeData(
            scheme_code=int(meta.get("scheme_code") or scheme_code),
            scheme_name=str(meta.get("scheme_name") or f"Scheme {scheme_code}"),
            fund_house=meta.get("fund_house"),
            scheme_category=meta.get("scheme_category"),
            isin_growth=meta.get("isin_growth"),
            rows=rows,
        )

    # ------------------------------------------------------------------ helpers

    def _get_json(self, url: str) -> dict[str, Any]:
        decorated = retry(
            reraise=True,
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
            retry=retry_if_exception_type(
                (httpx.TransportError, httpx.HTTPStatusError, httpx.ReadTimeout)
            ),
        )(self._do_get)
        return decorated(url)

    def _do_get(self, url: str) -> dict[str, Any]:
        resp = self._client.get(url)
        if resp.status_code >= 500 or resp.status_code == 429:
            logger.warning("mfapi transient %s on %s", resp.status_code, url)
            resp.raise_for_status()  # triggers tenacity retry
        resp.raise_for_status()
        return resp.json()


def _parse_rows(raw: list[dict[str, Any]], scheme_code: int) -> list[NavRow]:
    out: list[NavRow] = []
    for item in raw:
        try:
            d = datetime.strptime(item["date"], "%d-%m-%Y").date()
            v = float(item["nav"])
        except (KeyError, ValueError) as exc:
            logger.debug("skip malformed row for %s: %s (%s)", scheme_code, item, exc)
            continue
        out.append(NavRow(date=d, nav=v))
    # mfapi returns newest-first; store ascending so later queries can lean on order.
    out.sort(key=lambda r: r.date)
    return out
