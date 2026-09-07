"""
api_client.py

Thin wrapper around Playwright's synchronous `APIRequestContext` for the
Enhanced SMS API endpoints. Keeps base URL / headers / timeout concerns
in one place so tests stay focused on assertions, not plumbing.

MIGRATION NOTES (requests -> Playwright APIRequestContext):
- `requests.post(url, json=payload, headers=..., timeout=..., verify=...)`
  becomes `context.post(url, data=payload, headers=..., timeout=<ms>)`.
  Playwright serializes a dict/list passed via `data=` to a JSON string
  and sets `Content-Type: application/json` automatically (same
  contract as requests' `json=` kwarg), so payload shapes are unchanged.
- `verify=False` has no per-call Playwright equivalent; it is configured
  once at context-creation time via `ignore_https_errors` (see
  conftest.py's `api_request_context` fixture).
- Playwright's `timeout` is in **milliseconds**, not seconds.
- Playwright's `APIResponse` does not expose `.elapsed`, `.status_code`,
  or a lazy `.text` property the way `requests.Response` does. Rather
  than touch every test assertion, `ApiResponse` below adapts
  Playwright's response object to the same interface tests already use
  (`response.status_code`, `response.text`, `response.json()`,
  `response.elapsed.total_seconds()`). This kept 100% of the original
  test-level assertions unchanged during the migration.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Optional

from playwright.sync_api import APIRequestContext, APIResponse

from utils.sms_api_config_loader import EnvironmentConfig


class _Elapsed:
    """Mimics `requests.Response.elapsed`, which is a timedelta-like
    object exposing `.total_seconds()`."""

    __slots__ = ("_seconds",)

    def __init__(self, seconds: float):
        self._seconds = seconds

    def total_seconds(self) -> float:
        return self._seconds


class ApiResponse:
    """
    Adapter exposing a `requests.Response`-like interface over
    Playwright's `APIResponse`.

    This is what every `SmsApiClient` method returns, so existing test
    code (`response.status_code`, `response.text`, `response.json()`,
    `response.elapsed.total_seconds()`) keeps working without changes.
    """

    def __init__(self, response: APIResponse, elapsed_seconds: float):
        self._response = response
        self._elapsed_seconds = elapsed_seconds
        self._text_cache: Optional[str] = None

    @property
    def status_code(self) -> int:
        return self._response.status

    @property
    def ok(self) -> bool:
        return self._response.ok

    @property
    def headers(self) -> dict:
        return self._response.headers

    @property
    def text(self) -> str:
        # Lazily fetched and cached, matching requests' behavior of
        # reading the body once and reusing it for repeated access.
        if self._text_cache is None:
            self._text_cache = self._response.text()
        return self._text_cache

    def json(self) -> Any:
        return self._response.json()

    @property
    def elapsed(self) -> _Elapsed:
        return _Elapsed(self._elapsed_seconds)

    def raise_for_status(self) -> None:
        if not self.ok:
            raise AssertionError(
                f"Request to {self._response.url} failed with status "
                f"{self.status_code}. Body: {self.text}"
            )

    @property
    def raw(self) -> APIResponse:
        """Escape hatch to the underlying Playwright APIResponse."""
        return self._response


def _timed(context_call: Callable[..., APIResponse], *args: Any, **kwargs: Any) -> ApiResponse:
    """Times a Playwright APIRequestContext call and wraps the result
    in an ApiResponse so callers get `.elapsed` for free."""
    start = time.perf_counter()
    response = context_call(*args, **kwargs)
    elapsed_seconds = time.perf_counter() - start
    return ApiResponse(response, elapsed_seconds)


class SmsApiClient:
    def __init__(self, env_config: EnvironmentConfig, request_context: APIRequestContext):
        self.env = env_config
        # Exposed (not private) so tests that need a bespoke/edge-case
        # call (custom headers, raw malformed bodies, etc.) can reach
        # Playwright's context directly instead of importing `requests`.
        self.context = request_context
        self._timeout_ms = env_config.timeout_seconds * 1000

    # ---- POST /api/sms/send ---------------------------------------------
    def send_sms(self, payload: dict, headers: Optional[dict] = None) -> ApiResponse:
        return _timed(
            self.context.post,
            self.env.sms_send_url,
            data=payload,
            headers=headers if headers is not None else self.env.headers,
            timeout=self._timeout_ms,
        )

    # ---- GET /api/sms/send (query params instead of JSON body) ----------
    def send_sms_get(self, query_params: dict, headers: dict = None) -> ApiResponse:
        """
        Authentication is via the `api_token` query parameter — NOT a
        Bearer header. The Authorization header is intentionally excluded.
        """
        req_headers = {
            "Accept": "application/json",
            "domain": "demo.cpaas.test",
        }

        if headers:
            req_headers.update(headers)
        # Allow callers to clear a default header by passing None as its value
        req_headers = {k: v for k, v in req_headers.items() if v is not None}

        query = dict(query_params)
        if query.get("api_token") == "VALID_TOKEN":
            query["api_token"] = self.env.auth_token

        return _timed(
            self.context.get,
            self.env.sms_send_url,
            params=query,
            headers=req_headers,
            timeout=self._timeout_ms,
        )

    # ---- POST /api/sms/campaign/send -------------------------------------
    def send_campaign(self, payload: dict, headers: Optional[dict] = None) -> ApiResponse:
        return _timed(
            self.context.post,
            self.env.campaign_send_url,
            data=payload,
            headers=headers if headers is not None else self.env.headers,
            timeout=self._timeout_ms,
        )

    # ---- POST /api/sms/template/send -------------------------------------
    def send_template(self, payload: dict, headers: Optional[dict] = None) -> ApiResponse:
        return _timed(
            self.context.post,
            self.env.template_send_url,
            data=payload,
            headers=headers if headers is not None else self.env.headers,
            timeout=self._timeout_ms,
        )

    # ---- POST /api/sms/json ----------------------------------------------
    def send_json(self, payload: dict, headers: Optional[dict] = None) -> ApiResponse:
        """
        Batch endpoint with a `root` object (default from/text/to values)
        and a `data` array of per-message entries. Entries in `data` can
        omit fields to inherit them from `root` — this is presumably the
        endpoint's core feature (send many messages that mostly share the
        same from/text but override a few fields each).
        """
        return _timed(
            self.context.post,
            self.env.sms_json_url,
            data=payload,
            headers=headers if headers is not None else self.env.headers,
            timeout=self._timeout_ms,
        )

    # ---- POST /api/sms/send-msg (query params, no JSON body) -------------
    def send_msg(self, query_params: dict, headers: Optional[dict] = None) -> ApiResponse:
        """
        Unlike the other endpoints, this one takes its data as URL
        query parameters rather than a JSON request body — there is no
        Content-Type / JSON payload at all. `params` (if present) should
        be a Python list; it gets JSON-encoded into the query string the
        same way the sample curl command does
        (e.g. params=["test","test2"]).

        automatically, so callers should NOT pre-encode values (same
        contract as requests' `params=` kwarg).
        """
        # Force empty cookie header so Playwright doesn't send accumulated cookies
        req_headers = (
            dict(headers) if headers is not None else {"Authorization": f"Bearer {self.env.auth_token}"}
        )
        if "Accept" not in req_headers:
            req_headers["Accept"] = "application/json"
        req_headers["Cookie"] = ""
        
        query = dict(query_params)
        if "params" in query and isinstance(query["params"], list):
            query["params"] = json.dumps(query["params"])

        # Req headers are already built above


        return _timed(
            self.context.post,
            self.env.send_msg_url,
            params=query,
            headers=req_headers,
            timeout=self._timeout_ms,
        )

    # ---- POST /api/v1/sms/webengage/send -----------------------------------
    def send_webengage(self, payload: dict, headers: dict = None) -> ApiResponse:
        req_headers = dict(self.env.headers)
        if headers:
            req_headers.update(headers)

        return _timed(
            self.context.post,
            self.env.webengage_send_url,
            data=payload,
            headers=req_headers,
            timeout=self._timeout_ms,
        )

    # ---- Raw / malformed-body escape hatch --------------------------------
    def post_raw(self, url: str, raw_body: str, headers: dict) -> ApiResponse:
        """
        Sends a raw string body untouched (no JSON encoding) - used for
        malformed-JSON negative tests where the payload must NOT be
        valid JSON.

        IMPORTANT: Playwright's `data=` parameter does NOT treat a
        Python `str` the way `requests`' `data=<str>` does. If the
        string isn't valid JSON *and* the Content-Type header says
        `application/json`, Playwright's client silently re-encodes it
        with `json.dumps(...)` - wrapping the malformed body in quotes
        and turning it into a *valid* JSON string literal before it
        ever reaches the wire. That would make every "malformed JSON"
        negative test in this suite silently test the wrong thing.

        Passing raw_bytes (`bytes`) instead of `str` sidesteps that
        re-encoding entirely - Playwright sends bytes verbatim as the
        request body - which matches `requests.post(data=<str>)`'s
        literal, byte-for-byte behavior.
        """
        return _timed(
            self.context.post,
            url,
            data=raw_body.encode("utf-8"),
            headers=headers,
            timeout=self._timeout_ms,
        )
