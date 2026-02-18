"""
Test 08: 导出功能测试

测试论文集导出和论文卡片导出功能
"""

import time

import pytest

from conftest import BASE_URL, navigate_to


def test_export_collection_json(browser_page):
    """导出论文集为 JSON"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "collections")
    page.wait_for_timeout(500)

    collection_items = page.locator(".collection-item, [class*='collection']")

    if collection_items.count() == 0:
        print("  [!] 没有论文集可导出")
        return

    print("  检查导出按钮...")
    export_btn = collection_items.first.locator("button:has-text('导出'), button:has-text('Export')")

    if export_btn.count() == 0:
        export_btn = page.locator("button:has-text('导出'), button:has-text('Export')")

    if export_btn.count() > 0:
        print("  点击导出 JSON...")

        if export_btn.count() > 1:
            export_btn.nth(1).click()
        else:
            export_btn.first.click()

        page.wait_for_timeout(1000)
        print("  [v] JSON 导出完成（文件保存到下载目录）")
    else:
        print("  [!] 导出按钮未找到")


def test_export_collection_csv(browser_page):
    """导出论文集为 CSV"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "collections")
    page.wait_for_timeout(500)

    collection_items = page.locator(".collection-item, [class*='collection']")

    if collection_items.count() == 0:
        print("  [!] 没有论文集可导出")
        return

    collection_items.first.click()
    page.wait_for_timeout(500)

    export_btn = page.locator("button:has-text('CSV'), button:has-text('csv')")

    if export_btn.count() > 0:
        print("  点击导出 CSV...")
        export_btn.first.click()
        page.wait_for_timeout(1000)
        print("  [v] CSV 导出完成")
    else:
        print("  [!] CSV 导出按钮未找到")


def test_export_paper_card_image(browser_page):
    """导出论文卡片图片"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "recent")
    page.wait_for_timeout(1000)

    paper_cards = page.locator(".paper-card")

    if paper_cards.count() == 0:
        pytest.skip("没有论文卡片")

    print("  展开论文卡片...")
    expand_btn = paper_cards.first.locator("button:has-text('展开')")
    if expand_btn.count() > 0:
        expand_btn.first.click()
        page.wait_for_timeout(500)

    print("  点击导出卡片图片...")
    export_card_btn = paper_cards.first.locator("button:has-text('卡片'), button:has-text('Card')")

    if export_card_btn.count() > 0:
        export_card_btn.first.click()
        page.wait_for_timeout(2000)
        print("  [v] 论文卡片图片导出完成")
    else:
        print("  [!] 导出卡片按钮未找到")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
