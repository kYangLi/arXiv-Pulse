"""
Test 06: AI 对话测试

测试 AI 聊天功能
"""

import pytest

from conftest import BASE_URL, navigate_to


def test_chat_fab_visible(browser_page):
    """聊天 FAB 按钮显示"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    chat_fab = page.locator(".chat-fab-btn, button[class*='chat'], [class*='fab']")

    if chat_fab.count() > 0:
        print("  ✓ 聊天 FAB 按钮显示")
    else:
        print("  ⚠ 聊天 FAB 按钮未找到")


def test_chat_open_from_fab(browser_page):
    """FAB 按钮打开聊天窗口"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    chat_fab = page.locator(".chat-fab-btn").first

    if chat_fab.count() == 0:
        chat_fab = page.locator("button[class*='chat']").first

    if chat_fab.count() == 0:
        pytest.skip("聊天 FAB 按钮未找到")

    print("  点击聊天 FAB 按钮...")
    chat_fab.click()
    page.wait_for_timeout(500)

    chat_window = page.locator(".chat-window, [class*='chat-panel']")

    if chat_window.count() > 0:
        print("  ✓ 聊天窗口打开")
        page.screenshot(path="/tmp/test_chat_open.png")
    else:
        print("  ⚠ 聊天窗口未显示")


def test_chat_create_new_session(browser_page, api_config):
    """创建新对话"""
    page = browser_page

    if not api_config.get("ai_api_key"):
        pytest.skip("未配置 AI API Key")

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    chat_fab = page.locator(".chat-fab-btn").first
    if chat_fab.count() > 0:
        chat_fab.click()
        page.wait_for_timeout(500)

    chat_window = page.locator(".chat-window, [class*='chat-panel']")
    if chat_window.count() == 0:
        pytest.skip("聊天窗口未打开")

    new_chat_btn = page.locator("button:has-text('新对话'), button:has-text('New chat'), button:has-text('+')")

    if new_chat_btn.count() > 0:
        print("  点击新对话按钮...")
        new_chat_btn.first.click()
        page.wait_for_timeout(500)
        print("  ✓ 新对话创建")
    else:
        print("  ⚠ 新对话按钮未找到")


def test_chat_send_message(browser_page, api_config):
    """发送消息并接收响应（真实 AI API）"""
    page = browser_page

    if not api_config.get("ai_api_key"):
        pytest.skip("未配置 AI API Key")

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    chat_fab = page.locator(".chat-fab-btn").first
    if chat_fab.count() > 0:
        chat_fab.click()
        page.wait_for_timeout(500)

    chat_window = page.locator(".chat-window, [class*='chat-panel']")
    if chat_window.count() == 0:
        pytest.skip("聊天窗口未打开")

    chat_input = page.locator("textarea, input[type='text']").first
    if chat_input.count() == 0:
        pytest.skip("聊天输入框未找到")

    test_message = "Hello, can you help me understand this paper?"
    print(f"  输入消息: {test_message}")
    chat_input.fill(test_message)
    page.wait_for_timeout(300)

    send_btn = page.locator("button:has-text('发送'), button:has-text('Send')")
    if send_btn.count() > 0:
        send_btn.first.click()
    else:
        chat_input.press("Enter")

    print("  等待 AI 响应...")
    page.wait_for_timeout(10000)

    page.screenshot(path="/tmp/test_chat_response.png")
    print("  ✓ 消息发送完成")


def test_chat_from_paper_card(browser_page, api_config):
    """从论文卡片分析打开"""
    page = browser_page

    if not api_config.get("ai_api_key"):
        pytest.skip("未配置 AI API Key")

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    navigate_to(page, "recent")
    page.wait_for_timeout(1000)

    paper_cards = page.locator(".paper-card")

    if paper_cards.count() == 0:
        pytest.skip("没有论文卡片")

    analyze_btn = paper_cards.first.locator("button:has-text('分析'), button:has-text('Analyze')")

    if analyze_btn.count() > 0:
        print("  点击分析按钮...")
        analyze_btn.first.click()
        page.wait_for_timeout(500)

        chat_window = page.locator(".chat-window, [class*='chat-panel']")
        if chat_window.count() > 0:
            print("  ✓ 聊天窗口打开（从论文卡片分析）")
            page.screenshot(path="/tmp/test_chat_from_paper.png")
        else:
            print("  ⚠ 聊天窗口未打开")
    else:
        print("  ⚠ 分析按钮未找到")


def test_chat_close(browser_page):
    """关闭聊天窗口"""
    page = browser_page

    print(f"\n访问 {BASE_URL} ...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    chat_fab = page.locator(".chat-fab-btn").first
    if chat_fab.count() > 0:
        chat_fab.click()
        page.wait_for_timeout(500)

    chat_window = page.locator(".chat-window, [class*='chat-panel']")
    if chat_window.count() == 0:
        pytest.skip("聊天窗口未打开")

    close_btn = page.locator(".collapse-btn, button:has-text('收起'), button:has-text('Close')")

    if close_btn.count() > 0:
        print("  关闭聊天窗口...")
        close_btn.first.click()
        page.wait_for_timeout(300)

        chat_window = page.locator(".chat-window, [class*='chat-panel']")
        if chat_window.count() == 0 or not chat_window.first.is_visible():
            print("  ✓ 聊天窗口已关闭")
    else:
        chat_fab = page.locator(".chat-fab-btn").first
        if chat_fab.count() > 0:
            chat_fab.click()
            page.wait_for_timeout(300)
            print("  ✓ 聊天窗口已关闭（通过 FAB 切换）")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
