import pytest

@pytest.mark.regression
def test_dump_download_center_row(download_center_page):
    from pages.common.base_page import ensure_on_dc_page
    ensure_on_dc_page(download_center_page)
    download_center_page.page.wait_for_timeout(3000) # let it load
    
    rows = download_center_page.page.locator("tbody tr")
    if rows.count() > 0:
        html = rows.nth(0).inner_html()
        with open("first_row.html", "w", encoding="utf-8") as f:
            f.write(html)
    else:
        with open("first_row.html", "w", encoding="utf-8") as f:
            f.write("NO ROWS FOUND")
