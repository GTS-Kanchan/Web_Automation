"""
reporting/classifier.py -- conservative automatic failure classification
(requirement #9). When nothing matches confidently, returns UNKNOWN
rather than guessing -- an incorrect category is worse than none.
"""
import re

ASSERTION      = "ASSERTION"
TIMEOUT        = "TIMEOUT"
AUTHENTICATION = "AUTHENTICATION"
NETWORK        = "NETWORK"
API            = "API"
DLR            = "DLR"
DOWNLOAD       = "DOWNLOAD"
VALIDATION     = "VALIDATION"
PLATFORM_ERROR = "PLATFORM_ERROR"
BROWSER        = "BROWSER"
CONFIGURATION  = "CONFIGURATION"
UNKNOWN        = "UNKNOWN"

ALL_CATEGORIES = (
    ASSERTION, TIMEOUT, AUTHENTICATION, NETWORK, API, DLR, DOWNLOAD,
    VALIDATION, PLATFORM_ERROR, BROWSER, CONFIGURATION, UNKNOWN,
)

# Checked in order -- the FIRST match wins, so more specific signals
# (DLR, platform-error text) are listed ahead of generic ones
# (ASSERTION) that would otherwise also match on stray wording.
_RULES = [
    (DLR,            re.compile(r"\bDLR\b|delivery\s+report|delivery\s+status", re.I)),
    (PLATFORM_ERROR, re.compile(r"whoops|livewire|internal\s+server\s+error|fatal\s+error|sqlstate|queryexception", re.I)),
    (AUTHENTICATION, re.compile(r"\b401\b|unauthori[sz]ed|authentication\s+failed|login\s+failed|invalid\s+credentials", re.I)),
    (API,            re.compile(r"\b(403|500|502|503)\b|api\s+error|http\s+error|request\s+failed\s+with\s+status", re.I)),
    (DOWNLOAD,       re.compile(r"download|header\s+mismatch|\.csv\b|\.xlsx\b|file\s+not\s+found", re.I)),
    (NETWORK,        re.compile(r"connection\s+refused|net::err_|econnreset|dns|network\s+error|ERR_CONNECTION", re.I)),
    (TIMEOUT,        re.compile(r"timeout|timed\s+out|TimeoutError", re.I)),
    (BROWSER,        re.compile(r"target\s+closed|browser\s+has\s+been\s+closed|browser.*crash|page\s+crashed", re.I)),
    (CONFIGURATION,  re.compile(r"not\s+configured|missing.*(env|config)|base_url\s+is\s+empty|credentials\s+missing", re.I)),
    (VALIDATION,     re.compile(r"validation\s+error|invalid\s+(value|input|format)", re.I)),
    (ASSERTION,      re.compile(r"assertionerror|assert\s|expected.*(but|got)|did\s+not\s+match", re.I)),
]


def classify(exc_type: str = "", message: str = "", longrepr_text: str = "") -> str:
    """Conservative, rule-based classification. Looks at the exception
    type name, the (already-normalized-for-display) message, and a
    bounded slice of the full traceback text -- in that order of
    reliability, but all three are searched together since a signal
    (e.g. "DLR") may only appear in the traceback body."""
    haystack = " ".join(
        part for part in (exc_type or "", message or "", (longrepr_text or "")[:2000]) if part
    )
    if not haystack.strip():
        return UNKNOWN
    for category, pattern in _RULES:
        if pattern.search(haystack):
            return category
    return UNKNOWN
