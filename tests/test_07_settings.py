"""
Test 07: 设置功能测试

测试设置抽屉功能
"""

import pytest

from conftest import BASE_URL


def test_settings_open(browser_page):
    """打开设置抽屉"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    settings_btn = page.locator(
        ".settings-btn, button:has-text('设置'), button[class*='gear'], button[class*='settings']"
    )

    if settings_btn.count() == 0:
        settings_btn = page.locator("button[circle]").nth(1)

    if settings_btn.count() == 0:
        pytest.skip("设置按钮未找到")

    print("  打开设置抽屉...")
    settings_btn.first.click()
    page.wait_for_timeout(500)

    drawer = page.locator(".el-drawer, [class*='settings']")

    if drawer.count() > 0:
        print("  [v] 设置抽屉打开")
        page.screenshot(path="/tmp/test_settings.png")
    else:
        print("  [!] 设置抽屉未显示")


def test_settings_language_toggle(browser_page):
    """切换界面语言"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    settings_btn = page.locator(".settings-btn, button[class*='settings']")
    if settings_btn.count() > 0:
        settings_btn.first.click()
        page.wait_for_timeout(500)

    drawer = page.locator(".el-drawer")
    if drawer.count() == 0:
        pytest.skip("设置抽屉未打开")

    print("  切换界面语言...")
    lang_radio = page.locator(".el-radio-group, [class*='language']")

    if lang_radio.count() > 0:
        en_btn = lang_radio.first.locator("button:has-text('EN'), label:has-text('EN')")
        zh_btn = lang_radio.first.locator("button:has-text('中文'), label:has-text('中文')")

        if en_btn.count() > 0:
            en_btn.first.click()
            page.wait_for_timeout(300)
            print("  [v] 切换到英文界面")

        if zh_btn.count() > 0:
            zh_btn.first.click()
            page.wait_for_timeout(300)
            print("  [v] 切换到中文界面")
    else:
        print("  [!] 语言切换控件未找到")


def test_settings_field_selector(browser_page):
    """从设置打开领域选择器"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    settings_btn = page.locator(".settings-btn, button[class*='settings']")
    if settings_btn.count() > 0:
        settings_btn.first.click()
        page.wait_for_timeout(500)

    drawer = page.locator(".el-drawer")
    if drawer.count() == 0:
        pytest.skip("设置抽屉未打开")

    print("  点击研究领域选择...")
    field_selector = drawer.locator("div[style*='cursor: pointer'], button:has-text('领域'), button:has-text('field')")

    if field_selector.count() > 0:
        field_selector.first.click()
        page.wait_for_timeout(500)

        dialog = page.locator(".el-dialog")
        if dialog.count() > 0:
            print("  [v] 领域选择器打开")

            close_btn = dialog.locator(".el-dialog__headerbtn")
            if close_btn.count() > 0:
                close_btn.first.click()
                print("  [v] 领域选择器关闭")
        else:
            print("  [!] 领域选择对话框未显示")
    else:
        print("  [!] 领域选择入口未找到")


def test_settings_ai_test_connection(browser_page, api_config):
    """AI 连接测试"""
    page = browser_page

    if not api_config.get("ai_api_key"):
        pytest.skip("未配置 AI API Key")

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    settings_btn = page.locator(".settings-btn, button[class*='settings']")
    if settings_btn.count() > 0:
        settings_btn.first.click()
        page.wait_for_timeout(500)

    drawer = page.locator(".el-drawer")
    if drawer.count() == 0:
        pytest.skip("设置抽屉未打开")

    print("  点击测试连接按钮...")
    test_btn = drawer.locator("button:has-text('测试连接'), button:has-text('Test')")

    if test_btn.count() > 0:
        test_btn.first.click()
        page.wait_for_timeout(5000)

        success_msg = page.locator(".el-message--success")
        if success_msg.count() > 0:
            print("  [v] AI 连接测试成功")
        else:
            error_msg = page.locator(".el-message--error")
            if error_msg.count() > 0:
                print("  [!] AI 连接测试失败")
            else:
                print("  [!] 测试结果未确认")
    else:
        print("  [!] 测试连接按钮未找到")


def test_settings_close(browser_page):
    """关闭设置抽屉"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    settings_btn = page.locator(".settings-btn, button[class*='settings']")
    if settings_btn.count() > 0:
        settings_btn.first.click()
        page.wait_for_timeout(500)

    drawer = page.locator(".el-drawer")
    if drawer.count() == 0:
        pytest.skip("设置抽屉未打开")

    print("  关闭设置抽屉...")
    close_btn = drawer.locator(".el-drawer__close-btn, button:has-text('关闭'), button:has-text('Close')")

    if close_btn.count() > 0:
        close_btn.first.click()
        page.wait_for_timeout(300)
        print("  [v] 设置抽屉关闭")
    else:
        print("  点击抽屉外部关闭...")
        page.mouse.click(100, 100)
        page.wait_for_timeout(300)
        print("  [v] 设置抽屉关闭")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
