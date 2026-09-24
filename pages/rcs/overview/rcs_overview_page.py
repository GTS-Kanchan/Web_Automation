import os

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class RcsOverviewPage(BasePage):

    REPORT_URL = "/rcs/dashboard"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'RCS Overview')]"
    BREADCRUMB_CURRENT = "xpath=//nav[@aria-label='Breadcrumb']//span[contains(normalize-space(.),'RCS Overview')]"

    # ── Date range (single flatpickr range-mode input) ──────────────────────
    DATE_RANGE_INPUT = "#rcs-overview-date-range-picker"
    FLATPICKR_CALENDAR_OPEN = ".flatpickr-calendar.open"
    FLATPICKR_PREV_MONTH = ".flatpickr-calendar.open .flatpickr-prev-month"
    FLATPICKR_NEXT_MONTH = ".flatpickr-calendar.open .flatpickr-next-month"
    FLATPICKR_ENABLED_DAYS = (
        ".flatpickr-calendar.open .flatpickr-day"
        ":not(.flatpickr-disabled):not(.prevMonthDay):not(.nextMonthDay)"
    )
    FLATPICKR_DISABLED_DAYS = ".flatpickr-calendar.open .flatpickr-day.flatpickr-disabled"

    # ── Summary cards (stats-card / stats-label / stats-value pattern) ──────
    STATS_CARD_VALUE_BY_LABEL_XPATH = (
        "xpath=//span[contains(@class,'stats-label') and normalize-space()='{title}']"
        "/ancestor::div[contains(@class,'stats-card')][1]"
        "//div[contains(@class,'stats-value')]"
    )

    # ── Product cards (title/value sibling <p> pattern) ─────────────────────
    CARD_VALUE_BY_TITLE_XPATH = "xpath=//p[normalize-space(text())='{title}']/following-sibling::p[1]"

    # ── Message Status Trend chart ───────────────────────────────────────────
    CHART_TITLE = "xpath=//h3[normalize-space()='Message Status Trend']"
    CHART_SUBTITLE = "xpath=//p[normalize-space()='Message delivery and engagement performance over time']"
    CHART_CONTAINER = "#status"
    CHART_CANVAS = "#status .apexcharts-canvas"
    CHART_MENU_ICON = "#status .apexcharts-menu-icon"
    CHART_MENU = "#status .apexcharts-menu"
    CHART_EXPORT_SVG = "#status .apexcharts-menu-item.exportSVG"
    CHART_EXPORT_PNG = "#status .apexcharts-menu-item.exportPNG"
    CHART_EXPORT_CSV = "#status .apexcharts-menu-item.exportCSV"
    # Confirmed absent for this chart instance (categorical x-axis, no
    # zoom/pan keys in the JS chart config) — kept only so a
    # presence-check can assert they do NOT exist.
    CHART_ZOOM_ICONS = (
        "#status .apexcharts-zoom-icon, #status .apexcharts-zoomin-icon, "
        "#status .apexcharts-zoomout-icon, #status .apexcharts-pan-icon"
    )
    # Hand-built legend (NOT the ApexCharts built-in legend -- confirmed
    # `legend: { show: false }` in the chart's own JS options).
    LEGEND_ITEM_BY_LABEL_XPATH = "xpath=//span[contains(@class,'text-sm') and normalize-space()='{label}']"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/rcs/dashboard" in url and "login" not in url.lower()

    def get_page_title_text(self):
        return self.h.wait_for_element_visible(self.PAGE_TITLE).inner_text().strip()

    # ── Date range picker ────────────────────────────────────────────────────

    def get_date_range_value(self):
        # input_value() (the live DOM property), not get_attribute("value")
        # (the static HTML attribute): this field is a flatpickr range-mode
        # input (see class docstring above), and flatpickr writes the
        # selected range into the input purely via the JS `.value`
        # property -- it never calls setAttribute('value', ...). Reading
        # the attribute instead of the property is a well-known
        # Playwright/flatpickr gotcha and returns None even once flatpickr
        # has populated a real value, which is consistent with this
        # exact symptom (TC002/TC004/TC005 all asserting a falsy `value`
        # despite the picker visibly showing a default/selected range).
        # Contrast with RcsAgentPage.get_filter_values(), whose two date
        # inputs are plain native (non-flatpickr) fields and correctly
        # already use input_value() for that reason.
        return self.h.wait_for_element_visible(self.DATE_RANGE_INPUT).input_value()

    def open_date_range_picker(self):
        """Opens the flatpickr calendar. Retries the click a few times --
        same rationale as the WhatsApp Overview page object: immediately
        after a fresh page navigation the input can be visible/clickable
        before flatpickr's JS has finished binding to it, so the very
        first click sometimes doesn't open the calendar."""
        if self.is_element_present(self.FLATPICKR_CALENDAR_OPEN, timeout=1000):
            return
        el = self.h.wait_for_element_visible(self.DATE_RANGE_INPUT)
        for attempt in range(4):
            try:
                el.click()
            except Exception:
                el = self.h.wait_for_element_visible(self.DATE_RANGE_INPUT)
                el.click(force=True)
            try:
                self.page.locator(self.FLATPICKR_CALENDAR_OPEN).first.wait_for(state="visible", timeout=4000)
                self.page.wait_for_timeout(300)
                return
            except Exception:
                self.page.wait_for_timeout(600)
        self.page.locator(self.FLATPICKR_CALENDAR_OPEN).first.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(300)

    def close_date_range_picker(self):
        try:
            self.page.evaluate("document.activeElement && document.activeElement.blur();")
            self.page.locator("body").click(force=True)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def select_date_range_first_two_enabled_days(self):
        """Selects a valid range by clicking the first two ENABLED
        (non-disabled, in-current-month) day cells in the currently open
        calendar. Same confirmed flatpickr range-mode behavior as the
        WhatsApp Overview page: click 1 = start, click 2 = end."""
        self.open_date_range_picker()
        days = self.page.locator(self.FLATPICKR_ENABLED_DAYS)
        assert days.count() >= 2, "Need at least 2 enabled days in the open calendar"
        days.first.click(force=True)
        self.page.wait_for_timeout(400)
        # Playwright locators re-query the live DOM on every call, so unlike
        # Selenium's cached WebElement list, `days` here is safe to re-index
        # even after flatpickr re-renders the day cells — but re-fetching
        # explicitly keeps this identical in spirit to the original.
        days = self.page.locator(self.FLATPICKR_ENABLED_DAYS)
        days.last.click(force=True)
        self.page.wait_for_timeout(1500)

    def select_same_day_twice(self):
        """Selecting the same day for both From and To (a 1-day range).
        Re-queries the day element by its visible day-number text before
        the second click — flatpickr re-renders the day cells' DOM nodes
        after the first click, so Selenium's cached WebElement reference
        went stale on the second click; Playwright's Locator API
        re-resolves on every call, so this matters less here, but the
        text-based re-lookup is kept for parity."""
        self.open_date_range_picker()
        days = self.page.locator(self.FLATPICKR_ENABLED_DAYS)
        count = days.count()
        assert count, "Need at least 1 enabled day in the open calendar"
        idx = count // 2
        day_text = days.nth(idx).inner_text().strip()
        days.nth(idx).click(force=True)
        self.page.wait_for_timeout(400)
        days = self.page.locator(self.FLATPICKR_ENABLED_DAYS)
        target = None
        for i in range(days.count()):
            if days.nth(i).inner_text().strip() == day_text:
                target = days.nth(i)
                break
        if target is None:
            target = days.nth(min(idx, days.count() - 1))
        target.click(force=True)
        self.page.wait_for_timeout(1500)

    def get_disabled_future_day_count(self):
        self.open_date_range_picker()
        return self.page.locator(self.FLATPICKR_DISABLED_DAYS).count()

    def click_prev_month(self):
        self._js_click(self.FLATPICKR_PREV_MONTH, timeout=5000)
        self.page.wait_for_timeout(400)

    # ── Summary cards (stats-card pattern) ───────────────────────────────────

    def get_stats_card_value(self, title, timeout=20000):
        locator = self.STATS_CARD_VALUE_BY_LABEL_XPATH.format(title=title)
        el = self.page.locator(locator).first
        el.wait_for(state="attached", timeout=timeout)
        return el.inner_text().strip()

    def get_all_summary_card_values(self):
        titles = ["Total Messages", "Submitted", "Delivered", "Read",
                  "Failed", "DLR Awaited", "Rejected"]
        return {t: self.get_stats_card_value(t) for t in titles}

    # ── Product cards (title/value sibling <p> pattern) ──────────────────────

    def get_card_value(self, title, timeout=20000):
        """For the confirmed Transactional/Promotional/OTP/Multi Use
        product cards -- title <p> immediately followed by a sibling
        value <p> within the same wrapper div."""
        locator = self.CARD_VALUE_BY_TITLE_XPATH.format(title=title)
        el = self.page.locator(locator).first
        el.wait_for(state="attached", timeout=timeout)
        return el.inner_text().strip()

    def get_all_product_card_values(self):
        titles = ["Transactional", "Promotional", "OTP", "Multi Use"]
        return {t: self.get_card_value(t) for t in titles}

    # ── Message Status Trend chart ───────────────────────────────────────────

    def is_chart_title_visible(self):
        return self._is_visible(self.CHART_TITLE)

    def _is_visible(self, locator, timeout=5000):
        try:
            return self.page.locator(locator).first.is_visible()
        except Exception:
            return False

    def is_legend_item_visible(self, label):
        locator = self.LEGEND_ITEM_BY_LABEL_XPATH.format(label=label)
        return self._is_visible(locator)

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

    def export_chart(self, fmt, timeout_ms=20000):
        """Migration note: the Selenium version polled DOWNLOAD_DIR for a
        new/updated file by mtime. Playwright captures the download as an
        event directly via expect_download(), wrapped around the same
        open-menu-then-click sequence as click_chart_export()."""
        ext_map = {"png": ".png", "svg": ".svg", "csv": ".csv"}
        try:
            with self.page.expect_download(timeout=timeout_ms) as dl_info:
                self.click_chart_export(fmt)
            download = dl_info.value
        except Exception:
            return None
        filename = download.suggested_filename or f"chart-export{ext_map[fmt]}"
        dest = os.path.join(DOWNLOAD_DIR, filename)
        download.save_as(dest)
        return {"file_path": dest, "file_size": os.path.getsize(dest)}

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - window.performance.timing.navigationStart"
            )
        except Exception:
            return None
