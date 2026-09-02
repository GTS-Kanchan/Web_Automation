from playwright.sync_api import sync_playwright
import time
import json
import os
import sys

sys.path.append(r"C:\Users\Navjot Singh\project\cpaas_selenium_tests\cpaas_playwright_tests")
from utils.config import Config

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        state_path = r"C:\Users\Navjot Singh\project\cpaas_selenium_tests\cpaas_playwright_tests\reports\.auth\state.json"
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = json.load(f)
            context.add_cookies(state.get('cookies', []))
            
        page = context.new_page()
        page.goto(f"{Config.BASE_URL}/channels/sms/blocked-keywords")
        page.wait_for_timeout(3000)
        
        # Click Add Keyword
        page.evaluate("Array.from(document.querySelectorAll('button, a')).find(el => el.innerText && el.innerText.includes('Add Keyword'))?.click()")
        page.wait_for_timeout(2000)
        
        # Check if visible
        keyword_input = "#keyword, input[wire\\:model='keyword'], input[wire\\:model\\.defer='keyword']"
        is_vis = page.locator(keyword_input).first.is_visible()
        print(f"Visible after open: {is_vis}")
        
        # Click Cancel
        page.evaluate("Array.from(document.querySelectorAll('button, a')).find(el => el.innerText && el.innerText.trim() === 'Cancel')?.click()")
        page.wait_for_timeout(2000)
        
        # Check if hidden
        try:
            page.locator(keyword_input).first.wait_for(state="hidden", timeout=3000)
            print("Element is hidden correctly.")
        except Exception as e:
            print(f"Element did NOT hide: {e}")
            is_vis = page.locator(keyword_input).first.is_visible()
            print(f"Current visible state: {is_vis}")
            
        browser.close()

if __name__ == "__main__":
    main()
