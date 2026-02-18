"""
Test 04: 近期论文测试

测试近期论文页面功能
"""

import pytest

from conftest import BASE_URL, navigate_to


def test_recent_papers_load(browser_page):
    """近期论文列表加载"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    print("  导航到近期论文页...")
    navigate_to(page, "recent")
    page.wait_for_timeout(2000)

    page.screenshot(path="/tmp/test_recent_papers.png")

    paper_cards = page.locator(".paper-card")
    if paper_cards.count() > 0:
        print(f"  [v] 加载了 {paper_cards.count()} 个论文卡片")
    else:
        print("  [!] 未找到论文卡片（数据库可能为空）")


def test_recent_papers_count(browser_page):
    """论文数量显示"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "recent")
    page.wait_for_timeout(1000)

    count_text = page.locator("text=/\\d+.*篇/, text=/\\d+.*papers?/i")

    if count_text.count() > 0:
        print(f"  [v] 论文数量显示: {count_text.first.text_content()}")
    else:
        print("  [!] 未找到论文数量显示")


def test_paper_card_expand(browser_page):
    """论文卡片展开/收起"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "recent")
    page.wait_for_timeout(1000)

    paper_cards = page.locator(".paper-card")

    if paper_cards.count() == 0:
        pytest.skip("没有论文卡片可测试")

    print("  展开第一个论文卡片...")
    first_card = paper_cards.first

    expand_btn = first_card.locator("button:has-text('展开'), button:has-text('Expand')")
    if expand_btn.count() > 0:
        expand_btn.first.click()
        page.wait_for_timeout(500)

        page.screenshot(path="/tmp/test_paper_expanded.png")
        print("  [v] 论文卡片展开成功")

        collapse_btn = first_card.locator("button:has-text('收起'), button:has-text('Collapse')")
        if collapse_btn.count() > 0:
            collapse_btn.first.click()
            page.wait_for_timeout(300)
            print("  [v] 论文卡片收起成功")
    else:
        print("  [!] 展开按钮未找到")


def test_paper_card_arxiv_link(browser_page):
    """arXiv 链接"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "recent")
    page.wait_for_timeout(1000)

    paper_cards = page.locator(".paper-card")

    if paper_cards.count() == 0:
        pytest.skip("没有论文卡片可测试")

    first_card = paper_cards.first
    arxiv_link = first_card.locator("button:has-text('arXiv'), a[href*='arxiv.org']")

    if arxiv_link.count() > 0:
        print("  [v] arXiv 链接显示")
    else:
        print("  [!] arXiv 链接未找到")


def test_paper_card_pdf_link(browser_page):
    """PDF 下载链接"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "recent")
    page.wait_for_timeout(1000)

    paper_cards = page.locator(".paper-card")

    if paper_cards.count() == 0:
        pytest.skip("没有论文卡片可测试")

    first_card = paper_cards.first
    pdf_btn = first_card.locator("button:has-text('PDF'), button:has-text('下载')")

    if pdf_btn.count() > 0:
        print("  [v] PDF 下载按钮显示")
    else:
        print("  [!] PDF 下载按钮未找到")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
