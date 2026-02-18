"""
Test 01: 首次运行设置向导测试

测试首次运行时的初始化向导流程
使用独立的服务实例和数据库
"""

import time

import pytest

from conftest import BASE_URL, expand_bottom_nav


def test_init_page_visible(init_server, clean_browser_page, api_config):
    """首次访问显示设置向导"""
    page = clean_browser_page
    url = init_server["url"]

    print(f"\n访问 {url} ...")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    page.screenshot(path="/tmp/init_page.png")

    step_indicator = page.locator(".setup-steps")
    assert step_indicator.is_visible(), "设置向导步骤指示器未显示"

    print("  ✓ 设置向导页面显示")


def test_init_step1_elements(init_server, clean_browser_page, api_config):
    """步骤1：AI 配置页面元素检查"""
    page = clean_browser_page
    url = init_server["url"]

    print(f"\n访问 {url} ...")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    print("  检查步骤1元素...")

    assert page.locator("input[placeholder*='openai']").is_visible(), "API Base URL 输入框未显示"
    print("  ✓ API Base URL 输入框")

    assert page.locator("input[type='password']").is_visible(), "API Key 输入框未显示"
    print("  ✓ API Key 输入框")

    assert page.locator("button:has-text('测试连接')").is_visible(), "测试连接按钮未显示"
    print("  ✓ 测试连接按钮")

    next_btn = page.locator("button:has-text('下一步')")
    assert next_btn.is_visible(), "下一步按钮未显示"
    print("  ✓ 下一步按钮")


def test_init_step1_test_connection(init_server, clean_browser_page, api_config):
    """步骤1：测试 AI 连接功能"""
    page = clean_browser_page
    url = init_server["url"]

    if not api_config.get("ai_api_key"):
        pytest.skip("未配置 AI API Key")

    print(f"\n访问 {url} ...")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    print("  填写 API 配置...")

    base_url_input = page.locator("input[placeholder*='openai']")
    base_url_input.fill(api_config.get("ai_base_url", "https://api.openai.com/v1"))

    api_key_input = page.locator("input[type='password']")
    api_key_input.fill(api_config["ai_api_key"])

    if api_config.get("ai_model"):
        model_inputs = page.locator("input")
        for inp in model_inputs.all():
            placeholder = inp.get_attribute("placeholder") or ""
            if "DeepSeek" in placeholder or "model" in placeholder.lower():
                inp.fill(api_config["ai_model"])
                break

    print("  点击测试连接...")
    test_btn = page.locator("button:has-text('测试连接')")
    test_btn.click()

    page.wait_for_timeout(3000)

    success_indicator = page.locator(".el-message--success")
    if success_indicator.count() > 0:
        print("  ✓ AI 连接测试成功")
    else:
        print("  ⚠ AI 连接测试结果未确认（可能需要检查控制台）")


def test_init_step2_field_selector(init_server, clean_browser_page, api_config):
    """步骤2：领域选择器功能"""
    page = clean_browser_page
    url = init_server["url"]

    print(f"\n访问 {url} ...")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    print("  跳转到步骤2...")
    page.locator("button:has-text('下一步')").click()
    page.wait_for_timeout(500)

    print("  点击选择领域...")
    field_selector = page.locator("div[style*='cursor: pointer']").first
    field_selector.click()
    page.wait_for_timeout(500)

    dialog = page.locator(".el-dialog")
    assert dialog.is_visible(), "领域选择对话框未显示"
    print("  ✓ 领域选择对话框打开")

    close_btn = page.locator(".el-dialog__headerbtn")
    if close_btn.is_visible():
        close_btn.click()
        page.wait_for_timeout(300)
        print("  ✓ 对话框可关闭")


def test_init_step3_sync_settings(init_server, clean_browser_page, api_config):
    """步骤3：同步参数设置"""
    page = clean_browser_page
    url = init_server["url"]

    print(f"\n访问 {url} ...")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    print("  跳转到步骤3...")
    page.locator("button:has-text('下一步')").click()
    page.wait_for_timeout(300)
    page.locator("button:has-text('下一步')").click()
    page.wait_for_timeout(500)

    print("  检查同步参数设置...")

    selects = page.locator("select, .el-select")
    assert selects.count() >= 1, "年份选择器未显示"
    print("  ✓ 年份选择器显示")

    number_inputs = page.locator("input[type='number'], .el-input-number input")
    assert number_inputs.count() >= 3, "数值输入框未显示"
    print("  ✓ 同步参数输入框显示")


def test_init_step4_start_sync(init_server, clean_browser_page, api_config):
    """步骤4：开始同步按钮"""
    page = clean_browser_page
    url = init_server["url"]

    print(f"\n访问 {url} ...")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    print("  跳转到步骤4...")
    for _ in range(3):
        next_btn = page.locator("button:has-text('下一步')")
        if next_btn.count() > 0 and next_btn.first.is_visible():
            next_btn.first.click()
            page.wait_for_timeout(300)

    start_btn = page.locator("button:has-text('开始同步'), button:has-text('开始使用')")
    if start_btn.count() > 0:
        print("  ✓ 开始同步按钮显示")
    else:
        print("  ⚠ 开始同步按钮未找到")


def test_init_navigation_blocked(init_server, clean_browser_page, api_config):
    """初始化前导航被阻止"""
    page = clean_browser_page
    url = init_server["url"]

    print(f"\n访问 {url} ...")
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    setup_container = page.locator(".setup-container")
    assert setup_container.is_visible(), "设置向导未显示"

    bottom_nav = page.locator(".bottom-nav")
    assert not bottom_nav.is_visible(), "底部导航栏不应显示（初始化未完成）"
    print("  ✓ 初始化前导航正确阻止")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
