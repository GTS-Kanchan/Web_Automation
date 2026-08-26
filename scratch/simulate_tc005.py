import os
import time
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=r"C:\Users\Navjot Singh\project\cpaas_selenium_tests\cpaas_playwright_tests\reports\.auth\state.json")
        page = context.new_page()
        
        page.goto("https://testqa.cpaas.globeteleservices.com/channels/sms/incoming-messages")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Get first sender_id
        # In the real page, sender_id is the 4th column (User Number, Message Id, Sender Id, Content)
        # We can just extract it
        first_row = page.locator("table tbody tr").first
        if not first_row.is_visible():
            print("No rows found!")
            return
            
        tds = first_row.locator("td")
        sender_id = tds.nth(2).inner_text().strip()
        print(f"Target Sender ID: '{sender_id}'")
        
        # Search for it
        box = page.locator("input[placeholder*='Search']").first
        box.fill(sender_id)
        page.wait_for_timeout(500)
        box.press("Enter")
        page.wait_for_timeout(500)
        box.blur()
        
        # Wait for search to settle (fake)
        print("Waiting for search to settle...")
        time.sleep(3)
        
        # Count rows
        rows = page.locator("table tbody tr")
        print(f"Row count after search: {rows.count()}")
        
        if rows.count() > 0:
            print(f"First row sender_id after search: {rows.nth(0).locator('td').nth(2).inner_text().strip()}")
            
        browser.close()

if __name__ == "__main__":
    main()
