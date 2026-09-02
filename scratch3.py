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
        
        # KEYWORD_INPUT
        keyword_input = "#keyword, input[wire\\:model='keyword'], input[wire\\:model\\.defer='keyword'], input[name='keyword'], input[placeholder*='keyword' i]"
        # Mimic clear_and_type
        loc = page.locator(keyword_input).first
        loc.wait_for(state="visible", timeout=5000)
        loc.fill("TESTKW_PLAYWRIGHT_3")
        
        # Mimic add_keyword events
        try:
            loc.evaluate("(el) => { el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); }")
        except Exception as e:
            print("Error evaluating dispatch:", e)
            
        page.wait_for_timeout(500)
        
        # Mimic Save JS click
        clicked = page.evaluate("""
            let btn = Array.from(document.querySelectorAll('button, a')).find(el => el.innerText && (el.innerText.trim() === 'Save' || el.innerText.trim() === 'Add'));
            if(btn) { btn.click(); return true; }
            return false;
        """)
        print("Save button clicked:", clicked)
        page.wait_for_timeout(3000)
        
        html = page.evaluate("document.querySelector('table') ? document.querySelector('table').outerHTML : 'NO TABLE'")
        print("TESTKW_PLAYWRIGHT_3 in table?", "TESTKW_PLAYWRIGHT_3" in html)
        
        browser.close()

if __name__ == "__main__":
    main()
