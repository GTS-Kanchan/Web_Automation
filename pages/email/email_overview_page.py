import os

from pages.common.base_page import BasePage
from utils.config import DOWNLOAD_DIR


class EmailOverviewPage(BasePage):

    REPORT_URL = "/email/overview"

    # ── Page header ──────────────────────────────────────────────────────────
    PAGE_TITLE = "xpath=//h1[contains(normalize-space(.),'Email Overview')]"
    BREADCRUMB_CURRENT = (
        "xpath=//nav[@aria-label='Breadcrumb']//span[contains(normalize-space(.),'Email Overview')]"
    )

    # ── Date filters (two separate native date inputs, no stable id —
    # located via their unique wire:model.live attribute) ───────────────────
    TO_DATE_INPUT = "input[wire\\:model\\.live='to_date']"
    FROM_DATE_INPUT = "input[wire\\:model\\.live='from_date']"

    # ── Summary cards (title <p> immediately followed by value <p>) ─────────
    CARD_VALUE_BY_TITLE_XPATH = (
        "xpath=//p[normalize-space(text())='{title}']/following-sibling::p[1]")
    CARD_TITLES = ["Total Emails", "Emails Sent", "Emails Delivered",
                   "Total Opens", "Unique Opens", "Total Bounced",
                   "Total Failed", "DLR Awaited", "Unique Clicks"]

    # ── Email Delivery Status chart ──────────────────────────────────────────
    CHART_TITLE = "xpath=//h3[normalize-space()='Email Delivery Status']"
    # Custom HTML legend (NOT the ApexCharts built-in legend, which is
    # explicitly disabled via legend:{show:false} in this chart's JS
    # config, confirmed from the captured <script> block) — these two
    # color-coded chips are plain sibling <div>s next to the chart title.
    CHART_LEGEND_SENT = (
        "xpath=//div[contains(@class,'bg-blue-500') and contains(@class,'rounded-full')]"
        "/following-sibling::span[normalize-space()='Sent']"
    )
    CHART_LEGEND_DELIVERED = (
        "xpath=//div[contains(@class,'bg-green-500') and contains(@class,'rounded-full')]"
        "/following-sibling::span[normalize-space()='Delivered']"
    )
    CHART_CONTAINER = "#analytics"
    CHART_SVG = "#analytics svg"
    CHART_MENU_ICON = "#analytics .apexcharts-menu-icon"
    CHART_MENU = "#analytics .apexcharts-menu"
    CHART_EXPORT_SVG = "#analytics .apexcharts-menu-item.exportSVG"
    CHART_EXPORT_PNG = "#analytics .apexcharts-menu-item.exportPNG"
    CHART_EXPORT_CSV = "#analytics .apexcharts-menu-item.exportCSV"
    CHART_ZOOM_ICONS = (
        "#analytics .apexcharts-zoom-icon, #analytics .apexcharts-zoomin-icon, "
        "#analytics .apexcharts-zoomout-icon, #analytics .apexcharts-pan-icon, "
        "#analytics .apexcharts-reset-icon"
    )
    CHART_TOOLTIP = "#analytics .apexcharts-tooltip"
    CHART_TOOLTIP_Y_LABEL = "#analytics .apexcharts-tooltip-text-y-label"
    CHART_TOOLTIP_Y_VALUE = "#analytics .apexcharts-tooltip-text-y-value"

    # ── Navigation / page state ─────────────────────────────────────────────

    def navigate_to_report(self):
        self.open(self.REPORT_URL)
        self.page.wait_for_timeout(2000)
        return self

    def is_report_page(self):
        url = self.get_current_url()
        return "/email/overview" in url and "login" not in url.lower()

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

    # ── Date filters ─────────────────────────────────────────────────────────

    def get_to_date_value(self):
        return self.h.wait_for_element_visible(self.TO_DATE_INPUT).input_value()

    def get_from_date_value(self):
        return self.h.wait_for_element_visible(self.FROM_DATE_INPUT).input_value()

    def set_to_date(self, date_str):
        el = self.h.wait_for_element_visible(self.TO_DATE_INPUT)
        el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            date_str
        )
        self.page.wait_for_timeout(1500)

    def set_from_date(self, date_str):
        el = self.h.wait_for_element_visible(self.FROM_DATE_INPUT)
        el.evaluate(
            "(elm, v) => { elm.value = v; "
            "elm.dispatchEvent(new Event('input', {bubbles: true})); "
            "elm.dispatchEvent(new Event('change', {bubbles: true})); }",
            date_str
        )
        self.page.wait_for_timeout(1500)

    def set_date_range(self, from_date, to_date):
        self.set_from_date(from_date)
        self.set_to_date(to_date)

    # ── Summary cards ─────────────────────────────────────────────────────────

    def get_card_value(self, title, timeout=20000):
        xpath = self.CARD_VALUE_BY_TITLE_XPATH.format(title=title)
        el = self.h.wait_for_element_visible(xpath, timeout=timeout)
        return el.inner_text().strip()

    def get_all_card_values(self):
        return {t: self.get_card_value(t) for t in self.CARD_TITLES}

    @staticmethod
    def _parse_numeric(value_text):
        """Card values may be plain integers ('40'), a fraction-like
        string, or a percentage ('65%') — strip non-digit trailing chars
        and parse the leading integer. Returns None if unparseable
        (e.g. '26/40' — not used by the logical-relation check, which
        only reads the confirmed single-number cards)."""
        if value_text is None:
            return None
        digits = ""
        for ch in value_text.strip():
            if ch.isdigit():
                digits += ch
            elif digits:
                break
        return int(digits) if digits else None

    def get_card_numeric(self, title):
        return self._parse_numeric(self.get_card_value(title))

    # ── Email Delivery Status chart ──────────────────────────────────────────

    def is_chart_title_visible(self):
        return self._is_visible(self.CHART_TITLE)

    def is_chart_rendered(self):
        return self.is_element_present(self.CHART_SVG, timeout=10000)

    def has_zoom_controls(self):
        return self.is_element_present(self.CHART_ZOOM_ICONS, timeout=3000)

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

    def export_chart(self, fmt, timeout=20000):
        """ApexCharts' PNG/SVG/CSV export menu items trigger a client-side
        blob download, captured here via Playwright's native download
        event (same pattern already confirmed working in
        whatsapp_overview_page.export_chart()) rather than the old
        Selenium mtime-polling approach. fmt: 'png' | 'svg' | 'csv'"""
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
            filename = download.suggested_filename or f"email_overview_chart{ext_map[fmt]}"
            dest = os.path.join(DOWNLOAD_DIR, filename)
            download.save_as(dest)
            return {"file_path": dest, "file_size": os.path.getsize(dest)}
        except Exception:
            return None

    def hover_over_chart(self):
        """Moves the mouse over the chart's SVG area to trigger ApexCharts'
        mousemove-driven crosshair/tooltip — the supplied DOM dump was
        itself captured mid-hover with a real, populated tooltip, so this
        interaction and the resulting tooltip markup are both confirmed,
        not assumed. Uses Playwright's own hover() (replacing Selenium's
        ActionChains.move_to_element) plus a small offset nudge to ensure
        a genuine mousemove (not just mouseenter) fires."""
        chart = self.h.wait_for_element_visible(self.CHART_SVG)
        chart.scroll_into_view_if_needed()
        chart.hover()
        self.page.wait_for_timeout(500)
        box = chart.bounding_box()
        if box:
            self.page.mouse.move(box["x"] + box["width"] / 2 + 5, box["y"] + box["height"] / 2)
        self.page.wait_for_timeout(500)

    def is_tooltip_visible(self):
        return self.is_element_present(self.CHART_TOOLTIP, timeout=5000)

    def get_tooltip_series_texts(self):
        """Returns {label: value} pairs from the currently-open tooltip,
        e.g. {'Sent:': '12 emails', 'Delivered:': '10 emails'}."""
        labels = self.page.locator(self.CHART_TOOLTIP_Y_LABEL)
        values = self.page.locator(self.CHART_TOOLTIP_Y_VALUE)
        result = {}
        count = min(labels.count(), values.count())
        for i in range(count):
            key = labels.nth(i).inner_text().strip()
            if key:
                result[key] = values.nth(i).inner_text().strip()
        return result

    # ── Performance ──────────────────────────────────────────────────────────

    def get_page_load_time_ms(self):
        try:
            return self.page.evaluate(
                "() => window.performance.timing.loadEventEnd - "
                "window.performance.timing.navigationStart"
            )
        except Exception:
            return None
