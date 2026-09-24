import os

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class WhatsappOverviewPage(BasePage):

    REPORT_URL = "/whatsapp/channels/overview"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'WhatsApp Overview')]"
    BREADCRUMB_CURRENT = (
        "xpath=//nav[@aria-label='Breadcrumb']//span[contains(normalize-space(.),'WhatsApp Overview')]"
    )

    # ── Date range (single flatpickr range-mode input) ──────────────────────
    DATE_RANGE_INPUT = "#wa-overview-date-range-picker"
    FLATPICKR_CALENDAR_OPEN = ".flatpickr-calendar.open"
    FLATPICKR_PREV_MONTH = ".flatpickr-calendar.open .flatpickr-prev-month"
    FLATPICKR_NEXT_MONTH = ".flatpickr-calendar.open .flatpickr-next-month"
    FLATPICKR_ENABLED_DAYS = (
        ".flatpickr-calendar.open .flatpickr-day"
        ":not(.flatpickr-disabled):not(.prevMonthDay):not(.nextMonthDay)"
    )
    FLATPICKR_DISABLED_DAYS = ".flatpickr-calendar.open .flatpickr-day.flatpickr-disabled"

    # ── Summary cascade cards (shared locator pattern with product cards) ───
    CARD_VALUE_BY_TITLE_XPATH = (
        "xpath=//p[normalize-space(text())='{title}']/following-sibling::p[1]")

    # ── WhatsApp Delivery Status chart ──────────────────────────────────────
    CHART_TITLE = "xpath=//h3[normalize-space()='WhatsApp Delivery Status']"
    CHART_CONTAINER = "#analytics"
    CHART_SKELETON = "#analytics-skeleton"
    CHART_NODATA = "#analytics-nodata"
    CHART_MENU_ICON = "#analytics .apexcharts-menu-icon"
    CHART_MENU = "#analytics .apexcharts-menu"
    CHART_EXPORT_SVG = "#analytics .apexcharts-menu-item.exportSVG"
    CHART_EXPORT_PNG = "#analytics .apexcharts-menu-item.exportPNG"
    CHART_EXPORT_CSV = "#analytics .apexcharts-menu-item.exportCSV"
    # Confirmed absent for this chart instance (categorical x-axis) — kept
    # here only so a presence-check can assert they do NOT exist.
    CHART_ZOOM_ICONS = (
        "#analytics .apexcharts-zoom-icon, #analytics .apexcharts-zoomin-icon, "
        "#analytics .apexcharts-zoomout-icon, #analytics .apexcharts-pan-icon"
    )

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/whatsapp/channels/overview" in url and "login" not in url.lower()

    def get_page_title_text(self):
        el = self.h.wait_for_element_visible(self.PAGE_TITLE)
        return el.inner_text().strip()

    def _is_visible(self, locator, timeout=1000):
        try:
            loc = self.page.locator(locator)
            for i in range(loc.count()):
                if loc.nth(i).is_visible():
                    return True
            return False
        except Exception:
            return False

    # ── Date range picker ────────────────────────────────────────────────────

    def get_date_range_value(self):
        el = self.h.wait_for_element_visible(self.DATE_RANGE_INPUT)
        return el.input_value()

    def open_date_range_picker(self):
        """Opens the flatpickr calendar. Retries the click a few times:
        observed in a live run that immediately after a fresh page
        navigation the input can be visible/clickable before flatpickr's
        JS has finished binding to it, so the very first click sometimes
        doesn't open the calendar (TimeoutError) even though a retry
        a moment later succeeds."""
        if self.is_element_present(self.FLATPICKR_CALENDAR_OPEN, timeout=1000):
            return
        el = self.h.wait_for_element_visible(self.DATE_RANGE_INPUT)
        for attempt in range(4):
            try:
                el.click()
            except Exception:
                el = self.h.wait_for_element_visible(self.DATE_RANGE_INPUT)
                self.h.js_click(self.DATE_RANGE_INPUT)
            try:
                self.page.locator(self.FLATPICKR_CALENDAR_OPEN).first.wait_for(
                    state="visible", timeout=4000)
                self.page.wait_for_timeout(300)
                return
            except Exception:
                self.page.wait_for_timeout(600)
        # Final attempt with the original full timeout -- let it raise if
        # still genuinely stuck (real failure, not just a slow first click).
        self.page.locator(self.FLATPICKR_CALENDAR_OPEN).first.wait_for(
            state="visible", timeout=10000)
        self.page.wait_for_timeout(300)

    def close_date_range_picker(self):
        try:
            self.page.evaluate("document.activeElement && document.activeElement.blur();")
            self.page.locator("body").click()
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def select_date_range_first_two_enabled_days(self):
        """Selects a valid range by clicking the first two ENABLED
        (non-disabled, in-current-month) day cells in the currently open
        calendar. Confirmed pattern: flatpickr range mode treats click 1
        as start, click 2 as end, regardless of order clicked."""
        self.open_date_range_picker()
        days = self.page.locator(self.FLATPICKR_ENABLED_DAYS)
        assert days.count() >= 2, "Need at least 2 enabled days in the open calendar"
        days.nth(0).click(force=True)
        self.page.wait_for_timeout(400)
        # Re-query since flatpickr re-renders day classes after the first click
        days = self.page.locator(self.FLATPICKR_ENABLED_DAYS)
        days.nth(days.count() - 1).click(force=True)
        self.page.wait_for_timeout(1500)

    def select_same_day_twice(self):
        """TC006: selecting the same day for both From and To (a 1-day
        range). Re-queries the day element by its visible day-number text
        before the second click -- flatpickr re-renders the day cells'
        DOM nodes after the first click (same behavior already noted in
        select_date_range_first_two_enabled_days above), so reusing the
        original locator reference for the second click risks acting on a
        stale/detached node."""
        self.open_date_range_picker()
        days = self.page.locator(self.FLATPICKR_ENABLED_DAYS)
        count = days.count()
        assert count, "Need at least 1 enabled day in the open calendar"
        idx = count // 2
        day_text = days.nth(idx).inner_text().strip()
        days.nth(idx).click(force=True)
        self.page.wait_for_timeout(400)
        # Re-query since flatpickr re-renders day cells after the first click
        days = self.page.locator(self.FLATPICKR_ENABLED_DAYS)
        target_idx = idx
        for i in range(days.count()):
            if days.nth(i).inner_text().strip() == day_text:
                target_idx = i
                break
        else:
            target_idx = min(idx, days.count() - 1)
        days.nth(target_idx).click(force=True)
        self.page.wait_for_timeout(1500)

    def get_disabled_future_day_count(self):
        self.open_date_range_picker()
        return self.page.locator(self.FLATPICKR_DISABLED_DAYS).count()

    def click_prev_month(self):
        self._js_click(self.FLATPICKR_PREV_MONTH, timeout=5000)
        self.page.wait_for_timeout(400)

    # ── Summary cascade cards ────────────────────────────────────────────────

    def get_card_value(self, title, timeout=20000):
        """Works for BOTH the summary cascade cards (Total Messages,
        Submitted, Delivered, Read, Failed, DLR Awaited, Rejected,
        Delivery Rate) and the product/message-type cards (Authentication,
        Marketing, Utility, Others) — both use the identical title-then-
        value sibling <p> DOM pattern, and all 12 confirmed titles are
        unique across the page."""
        xpath = self.CARD_VALUE_BY_TITLE_XPATH.format(title=title)
        el = self.h.wait_for_element_visible(xpath, timeout=timeout)
        return el.inner_text().strip()

    def get_all_summary_card_values(self):
        titles = ["Total Messages", "Submitted", "Delivered", "Read",
                  "Failed", "DLR Awaited", "Rejected", "Delivery Rate"]
        return {t: self.get_card_value(t) for t in titles}

    # ── WhatsApp Delivery Status chart ──────────────────────────────────────

    def is_chart_title_visible(self):
        return self._is_visible(self.CHART_TITLE)

    def open_chart_menu(self):
        self._js_click(self.CHART_MENU_ICON, timeout=10000)
        self.page.locator(self.CHART_MENU).first.wait_for(state="visible", timeout=5000)
        self.page.wait_for_timeout(300)

    def click_chart_export(self, fmt):
        """fmt: 'png' | 'svg' | 'csv'"""
        self.open_chart_menu()
        locator = {
            "png": self.CHART_EXPORT_PNG,
            "svg": self.CHART_EXPORT_SVG,
            "csv": self.CHART_EXPORT_CSV,
        }[fmt]
        self._js_click(locator, timeout=10000)
        self.page.wait_for_timeout(1500)

    def has_zoom_controls(self):
        return self.is_element_present(self.CHART_ZOOM_ICONS, timeout=2000)

    def export_chart(self, fmt, timeout=20000):
        """ApexCharts' PNG/SVG/CSV export menu items trigger a client-side
        blob download, captured here via Playwright's native download
        event (same pattern as sms_incoming_messages_page.export_csv())
        rather than the old Selenium mtime-polling approach. fmt: 'png' |
        'svg' | 'csv'"""
        ext_map = {"png": ".png", "svg": ".svg", "csv": ".csv"}
        locator = {
            "png": self.CHART_EXPORT_PNG,
            "svg": self.CHART_EXPORT_SVG,
            "csv": self.CHART_EXPORT_CSV,
        }[fmt]
        self.open_chart_menu()
        try:
            with self.page.expect_download(timeout=timeout) as dl_info:
                self._js_click(locator, timeout=10000)
            download = dl_info.value
            filename = download.suggested_filename or f"whatsapp_overview_chart{ext_map[fmt]}"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {"file_path": dest, "file_size": os.path.getsize(dest)}
        except Exception:
            return None

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
