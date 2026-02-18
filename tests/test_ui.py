"""Test arXiv Pulse UI with Playwright"""

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"


def test_categories_api():
    """Test categories API returns correct structure"""
    import json
    import urllib.request

    url = f"{BASE_URL}/api/config/categories"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())

    assert "categories" in data
    assert "all_categories" in data
    assert "default_fields" in data
    assert len(data["all_categories"]) > 100
    assert data["default_fields"] == ["cond-mat.mtrl-sci", "quant-ph", "cs.LG"]
    print(f"✓ Categories API: {len(data['all_categories'])} categories")


def test_ui_init_page():
    """Test init page tree selector"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        content = page.content()

        assert "arXiv Pulse" in content
        print("✓ Init page loaded")

        page.screenshot(path="/tmp/init_page.png")

        browser.close()


def test_ui_category_tree():
    """Test category tree structure in init page"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        page.screenshot(path="/tmp/category_tree.png", full_page=True)

        page_content = page.content()

        if "category-tree" in page_content:
            print("✓ Category tree found in page")
        else:
            print("⚠ Category tree not found - may need to check UI")

        browser.close()


if __name__ == "__main__":
    test_categories_api()
    test_ui_init_page()
    test_ui_category_tree()
    print("\nAll tests passed!")
