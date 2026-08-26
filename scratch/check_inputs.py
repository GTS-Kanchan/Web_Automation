import os
import time
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=r"C:\Users\Navjot Singh\project\cpaas_selenium_tests\cpaas_playwright_tests\reports\.auth\state.json")
        page = context.new_page()
        
        print("Navigating to campaigns page...")
        page.goto("https://testqa.cpaas.globeteleservices.com/campaigns/sms")
        page.wait_for_load_state("networkidle")
        time.sleep(5)
        
        with open("scratch/campaign_dom.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        print("DOM dumped to campaign_dom.html")
        
        # Also print inputs
        locator = "input[placeholder*='Search'], input[wire\\:model*='search']"
        inputs = page.locator(locator)
        count = inputs.count()
        print(f"Found {count} inputs matching '{locator}'")
        
        for i in range(count):
            el = inputs.nth(i)
            is_vis = el.is_visible()
            ph = el.get_attribute("placeholder")
            wire = el.get_attribute("wire:model") or el.get_attribute("wire:model.live") or el.get_attribute("wire:model.lazy")
            print(f"Input {i}: visible={is_vis}, placeholder={ph}, wire:model={wire}")
            
        browser.close()

if __name__ == "__main__":
    main()
