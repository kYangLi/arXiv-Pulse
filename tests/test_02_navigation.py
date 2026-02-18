"""
Test 02: 页面导航测试

测试底部导航栏和页面切换功能
"""

import pytest

from conftest import BASE_URL, expand_bottom_nav, navigate_to


def test_bottom_nav_expand(browser_page):
    """底部导航栏悬停展开"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(1000)

    bottom_nav = page.locator(".bottom-nav")
    if not bottom_nav.is_visible():
        setup = page.locator(".setup-container")
        if setup.is_visible():
            pytest.skip("在 setup 模式")
        pytest.skip("底部导航栏未显示")

    print("  悬停展开导航栏...")
    bottom_nav.hover()
    page.wait_for_timeout(500)

    nav_items = page.locator(".nav-item")
    assert nav_items.count() >= 4, f"导航项不足，只有 {nav_items.count()} 个"
    print(f"  [v] 导航栏展开，显示 {nav_items.count()} 个导航项")


def test_navigate_to_recent(browser_page):
    """导航到近期论文页"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)

    print("  导航到近期论文页...")
    navigate_to(page, "recent")

    page.screenshot(path="/tmp/navigation_recent.png")

    page_title = page.locator("text=近期论文")
    assert page_title.count() > 0, "近期论文标题未显示"
    print("  [v] 近期论文页导航成功")


def test_navigate_to_sync(browser_page):
    """导航到同步页"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)

    print("  导航到同步页...")
    navigate_to(page, "sync")

    page.screenshot(path="/tmp/navigation_sync.png")

    sync_indicator = page.locator("text=数据管理, text=同步状态, text=同步设置, .sync-status-card")
    assert sync_indicator.count() > 0, "同步页面未显示"
    print("  [v] 同步页导航成功")


def test_navigate_to_collections(browser_page):
    """导航到论文集页"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)

    print("  导航到论文集页...")
    navigate_to(page, "collections")

    page.screenshot(path="/tmp/navigation_collections.png")

    collections_title = page.locator("text=论文集, .collections-page-header")
    assert collections_title.count() > 0, "论文集页面未显示"
    print("  [v] 论文集页导航成功")


def test_navigate_to_home(browser_page):
    """导航回首页"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)

    print("  先导航到近期论文页...")
    navigate_to(page, "recent")
    page.wait_for_timeout(300)

    print("  再导航回首页...")
    navigate_to(page, "home")

    page.screenshot(path="/tmp/navigation_home.png")

    print("  [v] 首页导航成功")


def test_no_console_errors(browser_page):
    """导航时无 JS 错误"""
    page = browser_page

    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda err: errors.append(str(err)))

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)

    print("  循环导航所有页面...")
    for target in ["recent", "sync", "collections", "home"]:
        navigate_to(page, target)
        page.wait_for_timeout(300)

    js_errors = [e for e in errors if "TypeError" in e or "ReferenceError" in e or "SyntaxError" in e]

    if js_errors:
        print(f"  [X] 发现 JS 错误: {js_errors}")
        pytest.fail(f"发现 JS 错误: {js_errors}")
    else:
        print("  [v] 无 JS 错误")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
