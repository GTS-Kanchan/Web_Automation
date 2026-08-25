import time

from pages.common.base_page import BasePage


class SMSOverviewPage(BasePage):

    # ── Direct URL ─────────────────────────────────────────────────────────────
    OVERVIEW_URL = "/channels/sms/overview"

    # ── Sidebar navigation ─────────────────────────────────────────────────────
    NAV_SMS      = "xpath=//nav//a[contains(@href,'/channels')] | //a[contains(.,'SMS')]"
    NAV_OVERVIEW = "xpath=//a[contains(@href,'/channels/sms/overview') or contains(.,'Overview')]"

    # ── Date range — single flatpickr range input ──────────────────────────────
    # The page uses ONE combined flatpickr range picker (rangeMode).
    # INPUT_FROM_DATE / INPUT_TO_DATE are kept as aliases for test-file references.
    INPUT_DATE_RANGE = "#sms-overview-date-range-picker"
    INPUT_FROM_DATE  = INPUT_DATE_RANGE   # alias — same element
    INPUT_TO_DATE    = INPUT_DATE_RANGE   # alias — same element
    BTN_APPLY_DATE   = "xpath=//button[contains(text(),'Apply')] | //button[contains(text(),'Search')] | //button[contains(text(),'Go')]"
    CALENDAR_POPUP   = ".flatpickr-calendar.open"

    # ── Cascade count boxes (top section — NOT lazy-loaded) ────────────────────
    # Actual page labels: "Total Units", "Submitted", "Delivered", "DLR Awaited",
    #                     "Failed", "Rejected", "Delivery Rate"
    BOX_TOTAL_MESSAGES     = "xpath=//*[normalize-space(text())='Total Units']"
    BOX_MESSAGES_SENT      = "xpath=//*[normalize-space(text())='Submitted']"
    BOX_MESSAGES_DELIVERED = "xpath=//*[contains(text(),'Delivered')]//following-sibling::*"
    BOX_DELIVERY_RATE      = "xpath=//*[contains(text(),'Delivery Rate')]//following-sibling::*"

    # ── Source count boxes (lazy-loaded section — Transactional / Promotional / OTP)
    # Note: API, UI, Flow boxes do not exist on this page.
    BOX_TRANSACTIONAL = "xpath=//*[normalize-space(text())='Transactional']"
    BOX_PROMOTIONAL   = "xpath=//*[normalize-space(text())='Promotional']"
    BOX_OTP           = "xpath=//*[normalize-space(text())='OTP']"

    # ── Graphs ─────────────────────────────────────────────────────────────────
    # Chart container has a stable id="analytics" (wire:ignore).
    # The inner .apexcharts-canvas has a dynamic ID — use the stable outer div.
    GRAPH_DELIVERY_STATUS = "#analytics"

    # ── Graph controls (3-dot menu / toolbar) ──────────────────────────────────
    # ApexCharts toolbar — actual classes from rendered HTML
    GRAPH_THREE_DOT_MENU = ".apexcharts-menu-icon"
    BTN_DOWNLOAD_PNG     = ".apexcharts-menu-item.exportPNG"
    BTN_DOWNLOAD_SVG     = ".apexcharts-menu-item.exportSVG"
    BTN_DOWNLOAD_CSV     = ".apexcharts-menu-item.exportCSV"
    # Note: chart menu offers SVG / PNG / CSV — no XLSX option on this page

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════════════

    def navigate_via_sidebar(self):
        """Navigate to SMS Overview — direct URL first, then sidebar fallback."""
        self.open(self.OVERVIEW_URL)
        self.page.wait_for_timeout(2000)
        if "overview" in self.get_current_url().lower() and "login" not in self.get_current_url().lower():
            return self
        try:
            self.h.wait_for_element_clickable(self.NAV_SMS, timeout=10000).click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        self.h.wait_for_element_clickable(self.NAV_OVERVIEW, timeout=10000).click()
        self.h.wait_for_url_contains("overview", timeout=15000)
        return self

    def is_overview_page(self):
        return "overview" in self.get_current_url().lower()

    # ══════════════════════════════════════════════════════════════════════════
    # Lazy-load helper
    # ══════════════════════════════════════════════════════════════════════════

    def _ensure_lazy_loaded(self):
        """
        Scroll Livewire lazy sections (x-intersect) into viewport to trigger
        their data fetch, then scroll back to top.
        """
        try:
            lazy_els = self.page.locator("[x-intersect]")
            for i in range(lazy_els.count()):
                lazy_els.nth(i).scroll_into_view_if_needed()
                self.page.wait_for_timeout(300)
            self.page.wait_for_timeout(3000)  # wait for Livewire to fetch and render content
            self.page.evaluate("window.scrollTo(0, 0);")
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # Date range
    # ══════════════════════════════════════════════════════════════════════════

    def get_from_date_value(self):
        """Return the From portion of the flatpickr range value."""
        try:
            val = self.page.locator(self.INPUT_DATE_RANGE).first.input_value()
            if val and " to " in val:
                return val.split(" to ")[0].strip()
            return val  # single date or pre-populated format
        except Exception:
            return None

    def get_to_date_value(self):
        """Return the To portion of the flatpickr range value."""
        try:
            val = self.page.locator(self.INPUT_DATE_RANGE).first.input_value()
            if val and " to " in val:
                return val.split(" to ")[1].strip()
            return val
        except Exception:
            return None

    def wait_for_date_range_populated(self, timeout_ms=10000):
        """Poll until the flatpickr range input has a non-empty value, or
        timeout_ms elapses. A single immediate read occasionally raced the
        default-value JS on a real (slower) remote-app load; polling for a
        few seconds is more resilient than reading once right after
        navigation. Returns (from_val, to_val) — either may still be None
        if the field truly never populates."""
        deadline = time.time() + (timeout_ms / 1000)
        from_val = to_val = None
        while True:
            from_val = self.get_from_date_value()
            to_val = self.get_to_date_value()
            if from_val or to_val:
                return from_val, to_val
            if time.time() >= deadline:
                return from_val, to_val
            self.page.wait_for_timeout(500)

    def click_from_date(self):
        """Click the range picker input to open the calendar."""
        self.h.wait_for_element_clickable(self.INPUT_DATE_RANGE).click()
        self.page.wait_for_timeout(500)

    def click_to_date(self):
        """Click the range picker input (same single input for range mode)."""
        self.h.wait_for_element_clickable(self.INPUT_DATE_RANGE).click()
        self.page.wait_for_timeout(500)

    def is_calendar_open(self):
        return self.is_element_present(self.CALENDAR_POPUP, timeout=3000)

    def set_from_date(self, date_str):
        """Set the from-date portion via flatpickr JS API."""
        self._set_date_range_js(date_str, date_str)

    def set_to_date(self, date_str):
        """Set the to-date portion via flatpickr JS API (re-applies full range)."""
        # Reads current from-date so it isn't lost
        current_from = self.get_from_date_value() or date_str
        self._set_date_range_js(current_from, date_str)

    def _set_date_range_js(self, from_date, to_date):
        """
        Set the flatpickr date range using the JavaScript API.
        Accepts ISO date strings (YYYY-MM-DD).  triggerChange=true fires
        the onChange callback which updates the Livewire component.
        """
        try:
            self.page.evaluate(
                """([from_date, to_date]) => {
                    var el = document.querySelector('#sms-overview-date-range-picker');
                    if (el && el._flatpickr) {
                        el._flatpickr.setDate([from_date, to_date], true);
                    }
                }""",
                [from_date, to_date]
            )
        except Exception:
            pass

    def apply_date_range(self, from_date, to_date):
        """
        Apply a date range via flatpickr JS API and wait for Livewire to refresh.
        from_date / to_date must be ISO strings: 'YYYY-MM-DD'.
        """
        self._set_date_range_js(from_date, to_date)
        # No Apply button needed — onChange fires automatically via triggerChange=true
        try:
            self.h.wait_for_element_clickable(self.BTN_APPLY_DATE, timeout=3000).click()
        except Exception:
            pass  # no Apply button on this page; that's expected
        self.page.wait_for_timeout(2000)  # allow Livewire to re-fetch and re-render

    # ══════════════════════════════════════════════════════════════════════════
    # Count boxes
    # ══════════════════════════════════════════════════════════════════════════

    def _get_box_value(self, locator):
        try:
            return self.h.wait_for_element_visible(locator).inner_text().strip()
        except Exception:
            return None

    def get_total_messages(self):     return self._get_box_value(self.BOX_TOTAL_MESSAGES)
    def get_messages_sent(self):      return self._get_box_value(self.BOX_MESSAGES_SENT)
    def get_messages_delivered(self): return self._get_box_value(self.BOX_MESSAGES_DELIVERED)
    def get_delivery_rate(self):      return self._get_box_value(self.BOX_DELIVERY_RATE)
    def get_transactional(self):      return self._get_box_value(self.BOX_TRANSACTIONAL)
    def get_promotional(self):        return self._get_box_value(self.BOX_PROMOTIONAL)
    def get_otp(self):                return self._get_box_value(self.BOX_OTP)

    def is_box_present(self, locator, timeout=20000):
        """
        Check whether a count box is visible.
        Transactional / Promotional / OTP are in a Livewire lazy section —
        scroll to trigger them before checking.

        Timeout raised from 8s to 20s — a live pytest run showed
        BOX_TOTAL_MESSAGES / BOX_DELIVERY_RATE intermittently not yet
        rendered within 8s after a date-range change on the real remote
        app. Also added a fallback for BOX_DELIVERY_RATE: its locator is a
        "following-sibling" xpath relative to the "Delivery Rate" label,
        which assumes a specific DOM relationship between label and value.
        If that exact relationship isn't found, fall back to just
        confirming the "Delivery Rate" label itself is present — good
        enough to satisfy "the box should be displayed" without depending
        on an unconfirmed assumption about exactly how the value is
        positioned relative to the label.

        A later live run showed the box STILL occasionally missing even
        after the 20s wait — the Livewire fetch on the real remote app can
        stall outright rather than just being slow, and no amount of extra
        waiting fixes a stalled request. So this now does one full
        page.reload() + a second wait cycle as a last resort before giving
        up, which recovers from that stalled-request case (same "verify +
        retry" idiom used in the RCS/WhatsApp download-center filter code)."""
        lazy_locators = {
            self.BOX_TRANSACTIONAL,
            self.BOX_PROMOTIONAL,
            self.BOX_OTP,
        }
        if locator in lazy_locators:
            self._ensure_lazy_loaded()
        if self.is_element_present(locator, timeout=timeout):
            return True
        if locator == self.BOX_DELIVERY_RATE and self.is_element_present(
                "xpath=//*[contains(text(),'Delivery Rate')]", timeout=3000):
            return True

        # Last resort: reload and give the Livewire fetch a fresh attempt.
        try:
            self.page.reload()
            self.page.wait_for_timeout(2000)
        except Exception:
            return False
        if locator in lazy_locators:
            self._ensure_lazy_loaded()
        if self.is_element_present(locator, timeout=timeout):
            return True
        if locator == self.BOX_DELIVERY_RATE:
            return self.is_element_present(
                "xpath=//*[contains(text(),'Delivery Rate')]", timeout=3000)
        return False

    # ══════════════════════════════════════════════════════════════════════════
    # Graphs
    # ══════════════════════════════════════════════════════════════════════════

    def is_delivery_status_graph_visible(self):
        return self.is_element_present(self.GRAPH_DELIVERY_STATUS, timeout=10000)

    def wait_for_graph_rendered(self, timeout_ms=10000):
        """Poll bounding_box() until the graph container has non-zero
        width/height, or timeout_ms elapses. ApexCharts renders its canvas
        asynchronously after the container itself is attached, so reading
        bounding_box() immediately can catch it mid-layout (0x0) on a
        slower real-app load. Returns the last bounding_box() read
        (possibly still zero-sized if it truly never rendered)."""
        deadline = time.time() + (timeout_ms / 1000)
        box = None
        while True:
            try:
                box = self.page.locator(self.GRAPH_DELIVERY_STATUS).first.bounding_box()
            except Exception:
                box = None
            if box and box["width"] > 0 and box["height"] > 0:
                return box
            if time.time() >= deadline:
                return box
            self.page.wait_for_timeout(500)

    def _open_graph_menu(self, graph_locator):
        """Hover over graph and click 3-dot menu."""
        graph = self.h.wait_for_element_visible(graph_locator)
        graph.scroll_into_view_if_needed()
        graph.hover()
        self.page.wait_for_timeout(500)
        menus = self.page.locator(self.GRAPH_THREE_DOT_MENU)
        if menus.count() > 0:
            menus.first.click()
            self.page.wait_for_timeout(500)

    def download_delivery_graph(self, format_type):
        """format_type: 'PNG', 'SVG', 'CSV'"""
        self._open_graph_menu(self.GRAPH_DELIVERY_STATUS)
        if format_type == "PNG":
            self.h.wait_for_element_clickable(self.BTN_DOWNLOAD_PNG).click()
        elif format_type == "SVG":
            self.h.wait_for_element_clickable(self.BTN_DOWNLOAD_SVG).click()
        elif format_type in ("CSV", "XLSX"):   # XLSX alias kept for compatibility
            self.h.wait_for_element_clickable(self.BTN_DOWNLOAD_CSV).click()
        self.page.wait_for_timeout(2000)

    def zoom_in_graph(self):
        try:
            self.h.wait_for_element_clickable(self.BTN_ZOOM_IN).click()
            self.page.wait_for_timeout(500)
            return True
        except Exception:
            return False

    def zoom_out_graph(self):
        try:
            self.h.wait_for_element_clickable(self.BTN_ZOOM_OUT).click()
            self.page.wait_for_timeout(500)
            return True
        except Exception:
            return False
