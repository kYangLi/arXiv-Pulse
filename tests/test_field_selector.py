"""Test field selector dialog with Playwright"""

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"


def test_create_collection_dialog():
    """Test that showCreateCollection dialog works (as comparison)"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        all_logs = []
        page.on("console", lambda msg: all_logs.append(f"[{msg.type}] {msg.text}"))

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # 检查是否在 setup 页面
        step1_next = page.locator("button:has-text('下一步')")
        if step1_next.is_visible():
            print("In setup, completing setup...")
            # Step 1: AI 配置 (直接点击下一步)
            step1_next.click()
            page.wait_for_timeout(300)

            # Step 2: 选择领域 (点击下一步，跳过)
            step2_next = page.locator("button:has-text('下一步')")
            if step2_next.is_visible():
                # 先选择一些领域
                area = page.locator("div[style*='cursor: pointer']").first
                if area.is_visible():
                    area.click()
                    page.wait_for_timeout(300)
                    # 点击确认
                    confirm_btn = page.locator("button:has-text('确认')")
                    if confirm_btn.count() > 0:
                        confirm_btn.first.click()
                        page.wait_for_timeout(300)
                step2_next.click()
                page.wait_for_timeout(300)

            # Step 3: 同步设置 (点击开始使用)
            step3_next = page.locator("button:has-text('开始使用')")
            if step3_next.is_visible():
                step3_next.click()
                page.wait_for_timeout(500)

        print(f"Current URL: {page.url}")

        # 检查是否完成了 setup
        bottom_nav = page.locator("div.bottom-nav")
        if bottom_nav.is_visible():
            print("Setup completed, navigating to collections...")
            # 点击收藏夹
            nav_items = page.locator("div.nav-item")
            if nav_items.count() >= 4:
                nav_items.nth(3).click()
                page.wait_for_timeout(300)

            # 点击创建收藏夹按钮
            create_btn = page.locator("button:has-text('创建收藏夹')")
            if create_btn.is_visible():
                print("Clicking create collection button...")
                create_btn.click()
                page.wait_for_timeout(500)

                el_dialog_count = page.locator(".el-dialog").count()
                el_overlay_count = page.locator(".el-overlay").count()
                print(f"After click create collection: el-dialog={el_dialog_count}, el-overlay={el_overlay_count}")
            else:
                print("Create collection button not visible")
        else:
            print("Still in setup mode")

        browser.close()


def test_field_selector_dialog():
    """Test field selector dialog opens on click"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        all_logs = []
        page.on("console", lambda msg: all_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: all_logs.append(f"[PAGE ERROR] {err}"))

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        print("Page loaded")

        step1_next = page.locator("button:has-text('下一步')")
        if step1_next.count() > 0 and step1_next.first.is_visible():
            print("In setup mode, going to step 2...")
            step1_next.first.click()
            page.wait_for_timeout(500)
            area = page.locator("div[style*='cursor: pointer']").first
        else:
            print("App already initialized, navigating to Settings...")
            bottom_nav = page.locator("div.bottom-nav")
            bottom_nav.hover()
            page.wait_for_timeout(300)

            nav_items = page.locator("div.nav-item")
            print(f"Nav items count: {nav_items.count()}")
            settings_index = nav_items.count() - 1
            nav_items.nth(settings_index).click()
            page.wait_for_timeout(1000)

            page_state = page.evaluate("""
            () => {
                const cursorEls = document.querySelectorAll('div[style*="cursor: pointer"]');
                return {
                    cursorPointers: cursorEls.length,
                    settingItems: document.querySelectorAll('.setting-item').length,
                    cursorElements: Array.from(cursorEls).map(el => ({
                        class: el.className,
                        text: el.textContent?.substring(0, 50),
                    })),
                };
            }
            """)
            print(f"Settings page state: {page_state}")

            area = page.locator("div[style*='cursor: pointer']").first

        print("\nClicking on the clickable area...")
        try:
            if area.count() > 0 and area.is_visible():
                area.click()
                page.wait_for_timeout(500)

                after = page.evaluate("""
                () => {
                    const dialog = document.querySelector('.el-dialog');
                    return {
                        hasDialog: !!dialog,
                        dialogDisplay: dialog ? getComputedStyle(dialog).display : null,
                        dialogVisible: dialog ? dialog.offsetParent !== null : false,
                    };
                }
                """)
                print(f"Dialog state: {after}")

                success = after["hasDialog"] and after["dialogVisible"]
                print(f"\nResult: {'✅ PASS' if success else '❌ FAIL'}")
            else:
                print("Clickable area not found!")
                success = False
        except Exception as e:
            print(f"Area click error: {e}")
            success = False

        if all_logs:
            print("\nConsole logs:")
            for log in all_logs:
                print(f"  {log}")

        browser.close()
        return success


def test_console_errors():
    """Check for JavaScript console errors"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        all_msgs = []
        page.on("console", lambda msg: all_msgs.append(f"[{msg.type}] {msg.text}"))

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # 等待一下确保 Vue 初始化完成
        page.wait_for_timeout(500)

        print("All console messages:")
        for msg in all_msgs:
            print(f"  {msg}")

        browser.close()
        return all_msgs


if __name__ == "__main__":
    print("=== Test Field Selector Dialog ===")
    success = test_field_selector_dialog()

    if success:
        print("\n✅ Field Selector Dialog test PASSED!")
    else:
        print("\n❌ Field Selector Dialog test FAILED!")
