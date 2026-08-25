"""
RCS Campaign Page Object
Covers: list page (TC001–TC021) and create flow.
"""
from pages.common.base_page import BasePage


class RCSCampaignPage(BasePage):

    CAMPAIGN_LIST_URL   = "/rcs/campaign"
    CAMPAIGN_CREATE_URL = "/rcs/campaign/create"

    # ── List page ──────────────────────────────────────────────────────────────
    BTN_CREATE          = (
        "xpath=//a[contains(@href,'create')] | //button[contains(.,'Create')]"
        " | //a[contains(.,'Create')]"
    )
    BTN_REFRESH         = (
        "xpath=//button[@*[name()='wire:click' and (contains(.,'refresh') or contains(.,'Refresh'))]]"
        " | //button[.//svg[contains(@class,'refresh') or contains(@class,'arrow')]]"
    )
    INPUT_SEARCH        = (
        "input[type='search'],"
        "input[placeholder*='Search'],"
        "input[placeholder*='search'],"
        "input[placeholder*='Campaign']"
    )
    NO_RECORDS          = (
        "xpath=//*[contains(text(),'No records') or contains(text(),'no records')"
        " or contains(text(),'No data') or contains(text(),'No campaigns')"
        " or contains(text(),'no campaigns') or contains(text(),'No results')"
        " or contains(text(),'no results') or contains(text(),'Nothing found')"
        " or contains(text(),'There are no') or contains(text(),'there are no')"
        " or contains(text(),'Not found') or contains(text(),'0 campaigns')"
        " or contains(text(),'No matching')]"
    )
    TABLE_ROWS          = (
        "xpath=//table//tbody//tr | //div[contains(@class,'table')]//div[contains(@class,'row')]"
    )

    # Filter locators (standard Livewire table filter structure)
    BTN_FILTER               = "xpath=//button[contains(.,'Filter') or @*[name()='wire:click' and contains(.,'filter')]]"
    SELECT_FILTER_DEPARTMENT = "#rcs_campaigns-filter-department"
    SELECT_FILTER_USER       = "#rcs_campaigns-filter-user"
    SELECT_FILTER_STATUS     = "#rcs_campaigns-filter-status"
    INPUT_FILTER_TEMPLATE_NAME = "#rcs_campaigns-filter-template_name"

    # Bulk action / export / columns
    BTN_BULK_ACTION     = "xpath=//button[contains(.,'Bulk Action') or contains(.,'Actions')]"
    BTN_EXPORT          = "xpath=//button[contains(.,'Export')] | //a[contains(.,'Export')]"
    BTN_COLUMNS         = "xpath=//button[contains(.,'Columns')]"
    COLUMN_CHECKBOX     = "xpath=(//input[@type='checkbox'])[2]"

    # Per page
    SELECT_PER_PAGE     = "xpath=//select[@*[name()='wire:model' and (contains(.,'perPage') or contains(.,'per_page'))]]"

    # ── Create page ────────────────────────────────────────────────────────────
    INPUT_CAMPAIGN_NAME = (
        "xpath=//input["
        "@*[name()='wire:model'       and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@*[name()='wire:model.live'  and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@*[name()='wire:model.defer' and (contains(.,'campaign_name') or contains(.,'campaign'))] or "
        "@id='campaign_name' or @name='campaign_name' or "
        "contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'campaign name')"
        "]"
    )

    # ── Actions ────────────────────────────────────────────────────────────────

    def load_campaign_list(self):
        """Navigate to the RCS Campaigns list page."""
        self.open(self.CAMPAIGN_LIST_URL)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def wait_for_spinner_to_disappear(self):
        """Wait for any loading spinner to disappear."""
        try:
            self.page.locator(".spinner, .loading, [wire\\:loading]").first.wait_for(
                state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def search_campaign(self, term: str):
        """Search the Livewire table."""
        self.wait_for_spinner_to_disappear()
        inp = self.h.wait_for_element_visible(self.INPUT_SEARCH)
        inp.fill(term)
        self.page.wait_for_timeout(1000)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def get_table_rows(self):
        """Return the list of current rows (ignoring 'No records' placeholder)."""
        self.wait_for_spinner_to_disappear()
        try:
            rows = self.page.locator(self.TABLE_ROWS)
            count = rows.count()
            if count == 1 and rows.first.locator(self.NO_RECORDS).count() > 0:
                return []
            return [rows.nth(i) for i in range(count)]
        except Exception:
            return []

    def set_per_page(self, limit: str):
        """Set the items-per-page dropdown."""
        self.wait_for_spinner_to_disappear()
        self.h.select_option(self.SELECT_PER_PAGE, value=str(limit))
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def open_filters(self):
        """Click the filter button to reveal the filter dropdown/panel."""
        self.wait_for_spinner_to_disappear()
        btn = self.h.wait_for_element_visible(self.BTN_FILTER)
        if btn.get_attribute("aria-expanded") != "true":
            btn.click()
            self.page.wait_for_timeout(500)

    def set_status_filter(self, status: str):
        """Filter by status."""
        self.open_filters()
        self.h.select_option(self.SELECT_FILTER_STATUS, label=status)
        self.wait_for_spinner_to_disappear()
        self.page.wait_for_timeout(1000)

    def export_data(self):
        """Click the Export button."""
        self.wait_for_spinner_to_disappear()
        self.h.wait_for_element_clickable(self.BTN_EXPORT).click()
        self.page.wait_for_timeout(2000)
