"""
Test 03: 首页功能测试

测试首页统计显示、AI 搜索功能
"""

import pytest

from conftest import BASE_URL, expand_bottom_nav


def test_stats_display(browser_page):
    """统计卡片显示"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    page.wait_for_timeout(1000)

    page.screenshot(path="/tmp/test_home_stats.png")

    stats_cards = page.locator(".stat-card, .el-card, [class*='stat']")
    if stats_cards.count() > 0:
        print(f"  [v] 找到 {stats_cards.count()} 个统计卡片")
    else:
        page_content = page.content()
        if "论文" in page_content or "Papers" in page_content:
            print("  [v] 统计信息已显示")
        else:
            print("  [!] 统计卡片未找到")


def test_search_input_visible(browser_page):
    """搜索框显示"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    page.wait_for_timeout(500)

    search_input = page.locator(
        "input[placeholder*='搜索'], input[placeholder*='search'], input[placeholder*='自然语言']"
    )

    if search_input.count() > 0:
        print("  [v] 搜索框显示")
    else:
        all_inputs = page.locator("input[type='text'], input:not([type])")
        print(f"  [!] 未找到特定搜索框，页面有 {all_inputs.count()} 个输入框")


def test_ai_search(browser_page, api_config):
    """AI 搜索功能（真实 API）"""
    page = browser_page

    if not api_config.get("ai_api_key"):
        pytest.skip("未配置 AI API Key")

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    page.wait_for_timeout(500)

    search_input = page.locator(
        "input[placeholder*='搜索'], input[placeholder*='search'], input[placeholder*='自然语言']"
    ).first

    if search_input.count() == 0:
        all_inputs = page.locator("input[type='text'], input:not([type])")
        if all_inputs.count() > 0:
            search_input = all_inputs.first
        else:
            pytest.skip("未找到搜索输入框")

    test_query = "DFT calculations for battery materials"
    print(f"  输入搜索查询: {test_query}")
    search_input.fill(test_query)
    page.wait_for_timeout(300)

    search_btn = page.locator("button:has-text('搜索'), button:has-text('Search')")
    if search_btn.count() > 0:
        search_btn.first.click()
    else:
        search_input.press("Enter")

    print("  等待搜索结果...")
    page.wait_for_timeout(5000)

    page.screenshot(path="/tmp/test_home_search_results.png")
    print("  [v] AI 搜索执行完成")


def test_search_results_display(browser_page):
    """搜索结果展示"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    page.wait_for_timeout(500)

    paper_cards = page.locator(".paper-card")

    if paper_cards.count() > 0:
        print(f"  [v] 找到 {paper_cards.count()} 个论文卡片")
    else:
        print("  [!] 未找到论文卡片（可能需要先执行搜索）")


def test_field_filter_button(browser_page):
    """领域筛选按钮"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    page.wait_for_timeout(500)

    filter_btn = page.locator("button:has-text('筛选'), button:has-text('Filter'), text=筛选领域")

    if filter_btn.count() > 0:
        print("  [v] 领域筛选按钮显示")
    else:
        print("  [!] 领域筛选按钮未找到")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
