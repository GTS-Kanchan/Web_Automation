import time
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("VALID_EMAIL")
PASS = os.getenv("VALID_PASSWORD")
BASE_URL = os.getenv("BASE_URL")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"{BASE_URL}/login")
    page.fill("input[type='email']", EMAIL)
    page.fill("input[type='password']", PASS)
    page.click("button[type='submit']")
    page.wait_for_url(lambda url: "login" not in url.lower(), timeout=45000)
    print("Logged in!")
    
    page.goto(f"{BASE_URL}/channels/sms/template")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    print("Templates URL:", page.url)
    
    # Print HTML of the filter panel
    try:
        page.locator("button:has-text('Filter')").click()
        time.sleep(2)
        print("Filter HTML:")
        print(page.locator("div[x-show='open'], .filter-panel, .dropdown-menu").first.inner_html())
    except Exception as e:
        print("Error getting filter HTML:", e)
        
    browser.close()
