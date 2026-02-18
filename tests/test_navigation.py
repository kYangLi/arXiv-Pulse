"""Test page navigation with Playwright"""

from playwright.sync_api import sync_playwright

BASE_URL = "http://192.168.219.3:33033"


def test_navigation():
    """Test navigating to all pages"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        errors = []
        page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda err: errors.append(f"[PAGE ERROR] {err}"))

        print("Loading page...")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        # Check for setup mode
        step1_next = page.locator("button:has-text('下一步')")
        if step1_next.is_visible():
            print("In setup mode, completing setup...")
            # Step 1: AI 配置
            step1_next.click()
            page.wait_for_timeout(300)

            # Step 2: 选择领域
            step2_next = page.locator("button:has-text('下一步')")
            if step2_next.is_visible():
                step2_next.click()
                page.wait_for_timeout(300)

                # Step 3: 高级设置
                step3_next = page.locator("button:has-text('开始同步')")
                if step3_next.is_visible():
                    step3_next.click()
                    # Wait for sync to complete or timeout
                    page.wait_for_timeout(3000)

        # Clear any errors from setup
        errors.clear()

        # Test 1: Navigate to Collections
        print("\n=== Test 1: Navigate to Collections ===")
        # First hover over bottom-nav to expand it
        bottom_nav = page.locator(".bottom-nav")
        if bottom_nav.is_visible():
            bottom_nav.hover()
            page.wait_for_timeout(300)
        collections_btn = page.locator("text=收藏集")
        if collections_btn.is_visible():
            collections_btn.click()
            page.wait_for_timeout(1000)

            # Check for errors
            if errors:
                print(f"  ❌ FAILED - Errors after navigating to Collections:")
                for e in errors:
                    print(f"    {e}")
                return False
            else:
                print("  ✓ No errors on Collections page")
        else:
            print("  ⚠ Collections button not found")

        errors.clear()

        # Test 2: Navigate to Recent Papers
        print("\n=== Test 2: Navigate to Recent Papers ===")
        if bottom_nav.is_visible():
            bottom_nav.hover()
            page.wait_for_timeout(300)
        recent_btn = page.locator("text=近期论文")
        if recent_btn.is_visible():
            recent_btn.click()
            page.wait_for_timeout(1000)

            if errors:
                print(f"  ❌ FAILED - Errors after navigating to Recent Papers:")
                for e in errors:
                    print(f"    {e}")
                return False
            else:
                print("  ✓ No errors on Recent Papers page")
        else:
            print("  ⚠ Recent Papers button not found")

        errors.clear()

        # Test 3: Navigate to Sync
        print("\n=== Test 3: Navigate to Sync ===")
        if bottom_nav.is_visible():
            bottom_nav.hover()
            page.wait_for_timeout(300)
        sync_btn = page.locator("text=同步")
        if sync_btn.is_visible():
            sync_btn.click()
            page.wait_for_timeout(1000)

            if errors:
                print(f"  ❌ FAILED - Errors after navigating to Sync:")
                for e in errors:
                    print(f"    {e}")
                return False
            else:
                print("  ✓ No errors on Sync page")
        else:
            print("  ⚠ Sync button not found")

        errors.clear()

        # Test 4: Navigate to Settings
        print("\n=== Test 4: Navigate to Settings ===")
        settings_btn = page.locator("text=设置")
        if settings_btn.is_visible():
            settings_btn.click()
            page.wait_for_timeout(1000)

            if errors:
                print(f"  ❌ FAILED - Errors after navigating to Settings:")
                for e in errors:
                    print(f"    {e}")
                return False
            else:
                print("  ✓ No errors on Settings page")
        else:
            print("  ⚠ Settings button not found")

        errors.clear()

        # Test 5: Navigate back to Home
        print("\n=== Test 5: Navigate to Home ===")
        if bottom_nav.is_visible():
            bottom_nav.hover()
            page.wait_for_timeout(300)
        home_btn = page.locator("text=首页")
        if home_btn.is_visible():
            home_btn.click()
            page.wait_for_timeout(1000)

            if errors:
                print(f"  ❌ FAILED - Errors after navigating to Home:")
                for e in errors:
                    print(f"    {e}")
                return False
            else:
                print("  ✓ No errors on Home page")

        # Final check
        if errors:
            print(f"\n❌ OVERALL FAILED - Total errors: {len(errors)}")
            for e in errors:
                print(f"  {e}")
            return False

        print("\n✅ All navigation tests PASSED!")
        browser.close()
        return True


if __name__ == "__main__":
    test_navigation()
