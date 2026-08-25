"""
error_monitor.py
Detects platform-level errors on any page during test execution and
immediately saves a timestamped screenshot to reports/Error_Screenshots/.

Errors detected:
  - HTTP 500 / 503 / 502 pages
  - Laravel / Symfony exception pages ("Whoops!")
  - Redis connection errors
  - "Internal Server Error" text anywhere on page
  - Livewire / PHP fatal error banners
  - Any page title containing "Error" or "Exception"

Usage (from a test or page object):
    from utils.error_monitor import ErrorMonitor
    monitor = ErrorMonitor(page)
    monitor.check()               # returns ErrorCapture | None

Automatic use — hooked into conftest.py so every test phase is checked.

Migrated from Selenium: driver.page_source -> page.content(),
driver.find_element(By.TAG_NAME, "body").text -> page.locator("body").inner_text(),
driver.save_screenshot(path) -> page.screenshot(path=path).
"""

import os
import re
import datetime

# Where error screenshots land
ERROR_SCREENSHOT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "reports", "Error_Screenshots"
)
os.makedirs(ERROR_SCREENSHOT_DIR, exist_ok=True)


# Patterns searched in page source / visible text
_ERROR_PATTERNS = [
    # HTTP error pages
    r"500\s+Internal\s+Server\s+Error",
    r"503\s+Service\s+(Un)?available",
    r"502\s+Bad\s+Gateway",
    # Laravel / Symfony / generic PHP
    r"Whoops[,!].*something went wrong",
    r"Symfony\s+Exception",
    r"PHP\s+Fatal\s+error",
    r"Fatal\s+error:",
    r"Unhandled\s+Exception",
    r"ErrorException",
    # Redis / cache
    r"Redis\s+(connection|server)\s+(refused|failed|error)",
    r"Predis\\Connection",
    r"MISCONF\s+Redis",
    r"Connection\s+refused.*redis",
    # Livewire
    r"Livewire\s+encountered\s+an\s+error",
    r"livewire.*exception",
    # Database
    r"SQLSTATE\[",
    r"QueryException",
    r"Database\s+(connection\s+)?(error|refused)",
    # Generic
    r"Internal\s+Server\s+Error",
    r"Application\s+Error",
    r"Service\s+Temporarily\s+Unavailable",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _ERROR_PATTERNS]

# Page title keywords that signal an error page
_ERROR_TITLES = [
    "500", "503", "502", "error", "exception",
    "whoops", "unavailable", "fatal",
]


class ErrorCapture:
    """Represents a detected error — stores screenshot path + details."""
    def __init__(self, path: str, pattern: str, url: str, test_name: str = ""):
        self.path      = path
        self.pattern   = pattern
        self.url       = url
        self.test_name = test_name
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return (f"[ErrorMonitor] Platform error detected!\n"
                f"  Pattern : {self.pattern}\n"
                f"  URL     : {self.url}\n"
                f"  Screenshot: {self.path}\n"
                f"  Time    : {self.timestamp}")


class ErrorMonitor:
    """
    Checks the current browser page for known platform error signatures.
    Call check() after any action that might trigger a server error.
    """

    def __init__(self, page, test_name: str = ""):
        self.page      = page
        self.test_name = test_name
        self._captures = []   # all captures this session

    # ── Public API ────────────────────────────────────────────────────────────

    def check(self) -> "ErrorCapture | None":
        """
        Inspect the current page for error signatures.
        If found: save screenshot, print warning, return ErrorCapture.
        If clean: return None.
        """
        try:
            return self._inspect()
        except Exception:
            return None

    @property
    def captures(self):
        """List of all ErrorCapture objects found this session."""
        return list(self._captures)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _inspect(self) -> "ErrorCapture | None":
        page = self.page
        url  = page.url

        # 1. Check page title
        title = page.title() or ""
        if any(kw in title.lower() for kw in _ERROR_TITLES):
            return self._capture(f"Error title: '{title}'", url)

        # 2. Scan page source (fast, catches hidden error divs too)
        try:
            src = page.content() or ""
        except Exception:
            src = ""

        for pattern in _COMPILED:
            if pattern.search(src):
                return self._capture(pattern.pattern, url)

        # 3. Check visible body text (catches JS-rendered error messages)
        try:
            body_text = page.locator("body").inner_text() or ""
            for pattern in _COMPILED:
                if pattern.search(body_text):
                    return self._capture(pattern.pattern, url)
        except Exception:
            pass

        return None  # page is clean

    def _capture(self, matched_pattern: str, url: str) -> ErrorCapture:
        """Save screenshot and return an ErrorCapture object."""
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_"
                            for c in self.test_name) or "unknown"
        filename = f"error_{safe_name}_{ts}.png"
        path     = os.path.join(ERROR_SCREENSHOT_DIR, filename)

        try:
            self.page.screenshot(path=path)
        except Exception as exc:
            path = f"(screenshot failed: {exc})"

        capture = ErrorCapture(
            path=path,
            pattern=matched_pattern,
            url=url,
            test_name=self.test_name,
        )
        self._captures.append(capture)
        print(f"\n{'='*60}")
        print(capture)
        print(f"{'='*60}\n")
        return capture


# ── Module-level convenience used by conftest.py ──────────────────────────────

def check_page_for_errors(page, test_name: str = "") -> "ErrorCapture | None":
    """One-shot check without keeping a monitor instance."""
    return ErrorMonitor(page, test_name).check()
