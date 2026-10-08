
import sys
import time

from playwright.sync_api import sync_playwright


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/diagnose_short_url_click.py <short_url>")
        sys.exit(1)

    short_url = sys.argv[1].strip()
    target = short_url if short_url.startswith(("http://", "https://")) else f"https://{short_url}"

    events = []

    def log(kind, req_or_resp):
        try:
            url = req_or_resp.url
            method = getattr(req_or_resp, "method", None) or getattr(req_or_resp.request, "method", "")
            status = getattr(req_or_resp, "status", None)
        except Exception as exc:
            events.append((time.time(), kind, f"<error reading event: {exc}>"))
            return
        events.append((time.time(), kind, f"{method} {url} -> status={status}"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.on("request", lambda req: log("REQUEST", req))
        page.on("response", lambda resp: log("RESPONSE", resp))

        print(f"\nNavigating to: {target}\n")
        t0 = time.time()
        try:
            page.goto(target, wait_until="load", timeout=30000)
        except Exception as exc:
            print(f"goto() raised: {exc}")
            if not short_url.startswith(("http://", "https://")) and "cert" in str(exc).lower():
                fallback = "http://" + target[len("https://"):]
                print(f"Retrying over plain http: {fallback}")
                page.goto(fallback, wait_until="load", timeout=30000)

        print(f"Final URL after load: {page.url}")

        # Give any trailing async beacon/analytics call a few seconds to fire
        # after "load" -- this is exactly the kind of call that could be
        # invisible to a server-side redirect-hit counter alone.
        page.wait_for_timeout(5000)

        browser.close()

    print("\n" + "=" * 100)
    print(f"Full network log ({len(events)} events), relative to t0:")
    print("=" * 100)
    for ts, kind, line in events:
        print(f"[+{ts - t0:6.2f}s] {kind:9s} {line}")

    print("\n" + "=" * 100)
    print("Look specifically for: more than one REQUEST whose URL contains the")
    print("short link's path/host (or an obvious tracking/analytics/beacon call)")
    print("after the initial redirect -- that is the extra click source.")
    print("=" * 100)


if __name__ == "__main__":
    main()
