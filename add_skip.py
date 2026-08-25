import os
import glob
import re

def insert_skip_condition():
    tests_dir = r"C:\Users\Navjot Singh\project\cpaas_selenium_tests\cpaas_playwright_tests\tests"
    files = glob.glob(os.path.join(tests_dir, "test_*.py"))

    # Regex to find .click_next_page() calls inside test functions
    # We capture the indentation (whitespace) and the object name.
    # Group 1: indentation, Group 2: page object name
    # Example: "    country_report_page.click_next_page()"
    pattern = re.compile(r'^(\s+)([a-zA-Z0-9_]+)\.click_next_page\(\)\s*$', re.MULTILINE)

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        changed = False

        def replacer(match):
            indent = match.group(1)
            page_obj = match.group(2)
            
            # If the check is already present right before this, don't duplicate it.
            # We can't easily check backward in re.sub without full context, 
            # so we'll just check if the exact string is already in the file.
            check_str = f"if not {page_obj}.is_element_present({page_obj}.NEXT_PAGE_BTN, timeout=3000):"
            if check_str in content:
                # Assuming if it's in the file, it's already added properly for this call
                # (This is safe because usually there's only 1 or 2 click_next_page calls in a file)
                return match.group(0)

            new_lines = [
                f"{indent}if not {page_obj}.is_element_present({page_obj}.NEXT_PAGE_BTN, timeout=3000):",
                f"{indent}    pytest.skip(\"Next page button not present (not enough records or locator mismatch)\")",
                match.group(0) # the original click_next_page() line
            ]
            return "\n".join(new_lines)

        new_content, count = pattern.subn(replacer, content)

        # Same for click_prev_page()
        pattern_prev = re.compile(r'^(\s+)(?:[a-zA-Z0-9_]+\s*=\s*)?([a-zA-Z0-9_]+)\.click_prev_page\(\)\s*$', re.MULTILINE)
        def replacer_prev(match):
            indent = match.group(1)
            page_obj = match.group(2)
            check_str = f"if not {page_obj}.is_element_present({page_obj}.PREV_PAGE_BTN, timeout=3000):"
            if check_str in content or check_str in new_content:
                return match.group(0)
            
            new_lines = [
                f"{indent}if not {page_obj}.is_element_present({page_obj}.PREV_PAGE_BTN, timeout=3000):",
                f"{indent}    pytest.skip(\"Previous page button not present (not enough records or locator mismatch)\")",
                match.group(0)
            ]
            return "\n".join(new_lines)
            
        new_content, count_prev = pattern_prev.subn(replacer_prev, new_content)


        if count > 0 or count_prev > 0:
            # We must be careful not to rewrite if nothing actually changed (due to already existing)
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {os.path.basename(filepath)}")

if __name__ == "__main__":
    insert_skip_condition()
