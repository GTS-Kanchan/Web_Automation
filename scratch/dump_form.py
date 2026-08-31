import os
import time
from playwright.sync_api import sync_playwright

from utils.config import Config

state_path = os.path.abspath("reports/.auth/state.json")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state=state_path, accept_downloads=True, ignore_https_errors=True)
    page = context.new_page()
    
    # Navigate to template list
    page.goto(f"{Config.BASE_URL}/channels/sms/template")
    page.wait_for_load_state("networkidle")
    
    # Click create template
    try:
        page.click("a[href*='/template/create'], button:has-text('Create')")
        page.wait_for_timeout(3000)
        
        # Take a screenshot
        page.screenshot(path="scratch/template_create_form.png", full_page=True)
        
        # Dump HTML of the form
        html = page.content()
        with open("scratch/template_create.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("Done. Screenshot saved to scratch/template_create_form.png")
    except Exception as e:
        print(f"Error: {e}")
        page.screenshot(path="scratch/error_create_form.png")
    
    context.close()
    browser.close()
