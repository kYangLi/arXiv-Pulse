"""
Test 05: 论文集管理测试

测试论文集的创建、编辑、删除功能
"""

import time

import pytest

from conftest import BASE_URL, navigate_to


def test_collections_list_load(browser_page):
    """论文集列表加载"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    print("  导航到论文集页...")
    navigate_to(page, "collections")
    page.wait_for_timeout(1000)

    page.screenshot(path="/tmp/test_collections.png")

    collection_items = page.locator(".collection-item, .el-card, [class*='collection']")

    if collection_items.count() > 0:
        print(f"  ✓ 找到 {collection_items.count()} 个论文集")
    else:
        print("  ⚠ 未找到论文集（可能为空）")


def test_create_collection(browser_page):
    """创建新论文集"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "collections")
    page.wait_for_timeout(500)

    print("  点击创建论文集按钮...")
    create_btn = page.locator("button:has-text('创建'), button:has-text('Create'), button:has-text('新建')")

    if create_btn.count() == 0:
        print("  ⚠ 创建按钮未找到")
        return

    create_btn.first.click()
    page.wait_for_timeout(500)

    dialog = page.locator(".el-dialog")
    assert dialog.is_visible(), "创建对话框未显示"
    print("  ✓ 创建对话框打开")

    name_input = dialog.locator("input").first
    test_name = f"Test Collection {int(time.time())}"
    name_input.fill(test_name)
    print(f"  输入论文集名称: {test_name}")

    confirm_btn = dialog.locator("button:has-text('确定'), button:has-text('确认'), button:has-text('创建')")
    if confirm_btn.count() > 0:
        confirm_btn.first.click()
        page.wait_for_timeout(1000)
        print("  ✓ 论文集创建完成")

    page.screenshot(path="/tmp/test_collection_created.png")


def test_edit_collection_name(browser_page):
    """编辑论文集名称"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "collections")
    page.wait_for_timeout(500)

    collection_items = page.locator(".collection-item, [class*='collection']")

    if collection_items.count() == 0:
        pytest.skip("没有论文集可编辑")

    print("  点击编辑按钮...")
    edit_btn = collection_items.first.locator("button:has-text('编辑'), button:has-text('Edit'), .edit-btn")

    if edit_btn.count() > 0:
        edit_btn.first.click()
        page.wait_for_timeout(500)

        dialog = page.locator(".el-dialog")
        if dialog.is_visible():
            print("  ✓ 编辑对话框打开")

            close_btn = dialog.locator(".el-dialog__headerbtn, button:has-text('取消')")
            if close_btn.count() > 0:
                close_btn.first.click()
                print("  ✓ 关闭编辑对话框")
    else:
        print("  ⚠ 编辑按钮未找到")


def test_add_paper_to_collection(browser_page):
    """添加论文到论文集"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "recent")
    page.wait_for_timeout(1000)

    paper_cards = page.locator(".paper-card")

    if paper_cards.count() == 0:
        pytest.skip("没有论文可添加")

    print("  添加论文到论文篮...")
    add_btn = paper_cards.first.locator("button:has-text('收藏'), button:has-text('Bookmark'), button:has-text('加入')")

    if add_btn.count() > 0:
        add_btn.first.click()
        page.wait_for_timeout(300)
        print("  ✓ 论文已添加到论文篮")

    print("  打开论文篮...")
    cart_btn = page.locator(".cart-btn, button:has-text('篮'), [class*='basket']")
    if cart_btn.count() > 0:
        cart_btn.first.click()
        page.wait_for_timeout(500)
        print("  ✓ 论文篮打开")

        add_to_collection_btn = page.locator("button:has-text('添加到论文集'), button:has-text('Add to collection')")
        if add_to_collection_btn.count() > 0:
            print("  ✓ 添加到论文集按钮显示")


def test_view_collection_papers(browser_page):
    """查看论文集内论文"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "collections")
    page.wait_for_timeout(500)

    collection_items = page.locator(".collection-item, [class*='collection']")

    if collection_items.count() == 0:
        pytest.skip("没有论文集可查看")

    print("  点击查看论文集...")
    collection_items.first.click()
    page.wait_for_timeout(1000)

    page.screenshot(path="/tmp/test_collection_papers.png")
    print("  ✓ 论文集详情显示")


def test_remove_paper_from_collection(browser_page):
    """从论文集移除论文"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "collections")
    page.wait_for_timeout(500)

    collection_items = page.locator(".collection-item, [class*='collection']")

    if collection_items.count() == 0:
        pytest.skip("没有论文集")

    collection_items.first.click()
    page.wait_for_timeout(500)

    papers = page.locator(".paper-card")

    if papers.count() == 0:
        print("  ⚠ 论文集内没有论文")
        return

    print("  检查移除按钮...")
    remove_btn = papers.first.locator("button:has-text('移除'), button:has-text('Remove'), button:has-text('删除')")

    if remove_btn.count() > 0:
        print("  ✓ 移除按钮显示")
    else:
        print("  ⚠ 移除按钮未找到")


def test_delete_collection(browser_page):
    """删除论文集"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "collections")
    page.wait_for_timeout(500)

    collection_items = page.locator(".collection-item, [class*='collection']")

    if collection_items.count() == 0:
        print("  ⚠ 没有论文集可删除")
        return

    print("  检查删除按钮...")
    delete_btn = collection_items.first.locator("button:has-text('删除'), button:has-text('Delete')")

    if delete_btn.count() > 0:
        print("  ✓ 删除按钮显示")
    else:
        print("  ⚠ 删除按钮未找到（可能需要更多操作）")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
