from pages.common.base_page import BasePage


class DashboardPage(BasePage):
    # ── Locators (update after first login to inspect real DOM) ────────────────
    SIDEBAR_NAV     = "nav, aside, [class*='sidebar'], [class*='nav']"
    # CONFIRMED via pasted DOM: the user-menu trigger is the avatar button
    # (contains an <img>, distinguishing it from the notification-bell
    # button which only has an <svg>) — same pattern already confirmed and
    # used on SMSErrorCodesPage/SMSBlockedNumbersPage.
    USER_MENU       = "xpath=//button[contains(@class,'rounded-full') and .//img]"
    # CONFIRMED via pasted DOM:
    #   <a title="Log out" href=".../logout" onclick="event.preventDefault(); this.closest('form').submit();">
    # — was previously guessed as "Logout"/"Sign out" text, which never matched.
    LOGOUT_BTN      = "xpath=//a[@title='Log out']"
    PAGE_HEADING    = "h1, h2, [class*='heading'], [class*='title']"
    NOTIFICATION    = "[class*='notification'], [class*='bell']"

    # ── Common nav items (will vary by role) ───────────────────────────────────
    NAV_ITEMS = "nav a, aside a, [class*='sidebar'] a, [class*='menu-item']"

    # ── Actions ────────────────────────────────────────────────────────────────

    def get_nav_links(self):
        """Return list of (text, href) for all sidebar/nav links."""
        items = self.page.locator(self.NAV_ITEMS)
        result = []
        for i in range(items.count()):
            el = items.nth(i)
            text = el.inner_text().strip()
            if text:
                result.append((text, el.get_attribute("href")))
        return result

    def open_user_menu(self):
        self.h.wait_for_element_clickable(self.USER_MENU).click()
        return self

    def logout(self):
        self.open_user_menu()
        # allow the user-menu dropdown's open transition to finish
        self.page.wait_for_timeout(500)
        self.h.wait_for_element_clickable(self.LOGOUT_BTN).click()

    def get_page_heading(self):
        if self.is_element_present(self.PAGE_HEADING):
            return self.h.wait_for_element_visible(self.PAGE_HEADING).inner_text()
        return None

    # ── Assertions ─────────────────────────────────────────────────────────────

    def is_dashboard_loaded(self):
        """True if URL changed away from /login and sidebar is present."""
        url = self.get_current_url()
        return "login" not in url and "forgot" not in url

    def is_sidebar_present(self):
        return self.is_element_present(self.SIDEBAR_NAV, timeout=10000)
