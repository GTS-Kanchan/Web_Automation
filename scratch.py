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
        
        # Click Add Keyword button
        page.evaluate("Array.from(document.querySelectorAll('button, a')).find(el => el.innerText && el.innerText.includes('Add Keyword'))?.click()")
        page.wait_for_timeout(2000)
        
        # Fill Keyword
        keyword_input = "#keyword, input[wire\\:model='keyword'], input[wire\\:model\\.defer='keyword']"
        page.locator(keyword_input).first.fill("TESTPLAYWRIGHT1")
        page.wait_for_timeout(500)
        
        # Click Save
        page.evaluate("Array.from(document.querySelectorAll('button')).find(el => el.innerText && el.innerText.includes('Save'))?.click()")
        page.wait_for_timeout(4000)
        
        # Dump table HTML
        html = page.evaluate("document.querySelector('table') ? document.querySelector('table').outerHTML : 'NO TABLE'")
        with open("table_html.txt", "w", encoding="utf-8") as f:
            f.write(html)
            
        browser.close()

if __name__ == "__main__":
    main()
