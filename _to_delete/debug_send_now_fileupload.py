import os, sys, json
sys.path.insert(0, os.getcwd())
from playwright.sync_api import sync_playwright
from pages.rcs.rcs_campaign_create_page import RcsCampaignCreatePage
from utils.test_data_generator import DATA_DIR

STATE_PATH = "reports/.auth/state.json"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(storage_state=STATE_PATH)
    page = context.new_page()

    cp = RcsCampaignCreatePage(page)
    cp.navigate()
    cp.fill_campaign_name("DEBUG_FILE_UPLOAD")

    try:
        cp.select_agent_by_index(1)
    except Exception as e:
        print("agent select failed:", e)

    try:
        cp.select_template_by_index(1)
    except Exception as e:
        print("template select failed:", e)

    filepath = os.path.join(DATA_DIR, "valid_contacts.xlsx")
    res = cp.click_import_contacts_btn()
    print("click_import_contacts_btn:", res)

    res = cp.upload_contact_file(filepath)
    print("upload_contact_file:", res)

    res = cp.click_import_confirm()
    print("click_import_confirm:", res)

    page.wait_for_timeout(1000)

    # ---- DOM inspection before touching Send Now ----
    modal_open = cp.is_contacts_modal_present(timeout=1500)
    print("modal still present after confirm:", modal_open)

    radios = page.locator("xpath=//input[@type='radio']")
    n = radios.count()
    print(f"total radio inputs on page: {n}")
    for i in range(n):
        el = radios.nth(i)
        try:
            info = el.evaluate("""(node) => ({
                id: node.id, value: node.value, checked: node.checked,
                visible: !!(node.offsetParent), name: node.name,
                outerHTML: node.outerHTML.slice(0,200)
            })""")
        except Exception as e:
            info = f"ERR {e}"
        print(f"  radio[{i}]:", info)

    send_now_label_count = page.locator(cp.SEND_NOW_LABEL).count()
    print("SEND_NOW_LABEL match count:", send_now_label_count)
    for i in range(send_now_label_count):
        lbl = page.locator(cp.SEND_NOW_LABEL).nth(i)
        try:
            print(f"  label[{i}] visible={lbl.is_visible()} text={lbl.inner_text()!r}")
        except Exception as e:
            print(f"  label[{i}] ERR {e}")

    # Now try the actual select_send_now and inspect result
    res = cp.select_send_now()
    print("select_send_now() result:", res)

    # dump page html for offline inspection
    with open("debug_after_send_now.html", "w", encoding="utf-8") as f:
        f.write(page.content())

    browser.close()
