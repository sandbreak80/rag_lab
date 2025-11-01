"""
Playwright tests for tab switching and UI validation
"""
import asyncio
from playwright.async_api import async_playwright, Page

async def test_tab_switching():
    """Test that tabs properly switch content"""
    print("\n🧪 Testing tab switching...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate to the app
        await page.goto('http://localhost:5555')
        await page.wait_for_load_state('networkidle')

        print("✅ Page loaded")

        # Test clicking each tab
        tabs = ['chat', 'settings', 'metrics', 'lab']

        for tab_name in tabs:
            print(f"\n🔍 Testing {tab_name} tab...")

            # Click the tab button
            tab_button = await page.query_selector(f'[data-tab="{tab_name}"]')
            if tab_button:
                await tab_button.click()
                await page.wait_for_timeout(500)  # Wait for animation

                # Check if tab button has active class
                classes = await tab_button.get_attribute('class')
                is_active = 'active' in classes
                print(f"   Tab button active: {is_active}")

                # Check if tab content is visible
                tab_content = await page.query_selector(f'#tab-{tab_name}')
                if tab_content:
                    is_visible = await tab_content.is_visible()
                    classes = await tab_content.get_attribute('class')
                    has_active = 'active' in classes
                    print(f"   Tab content visible: {is_visible}")
                    print(f"   Tab content has active class: {has_active}")

                    # Get content text to see what's actually shown
                    content_text = await tab_content.inner_text()
                    preview = content_text[:200] if content_text else "EMPTY"
                    print(f"   Content preview: {preview}...")
                else:
                    print(f"   ❌ Tab content #{tab_name} not found!")
            else:
                print(f"   ❌ Tab button for {tab_name} not found!")

        # Take a screenshot
        await page.screenshot(path='/tmp/tabs_test.png')
        print("\n📸 Screenshot saved to /tmp/tabs_test.png")

        await browser.close()

async def test_settings_content():
    """Test that Settings tab has controls"""
    print("\n🧪 Testing Settings tab content...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto('http://localhost:5555')
        await page.wait_for_load_state('networkidle')

        # Click Settings tab
        settings_tab = await page.query_selector('[data-tab="settings"]')
        if settings_tab:
            await settings_tab.click()
            await page.wait_for_timeout(500)

            # Look for setting controls
            controls = {
                'query_expansion': await page.query_selector('#use-query-expansion'),
                'bm25': await page.query_selector('#use-bm25'),
                'hybrid': await page.query_selector('#use-hybrid'),
                'graph': await page.query_selector('#use-graph'),
                'reranking': await page.query_selector('#use-reranking'),
                'web_search': await page.query_selector('#use-web-search'),
                'top_k': await page.query_selector('#top-k'),
            }

            print("\n📋 Settings controls found:")
            for name, element in controls.items():
                print(f"   {name}: {'✅ Found' if element else '❌ Missing'}")

        await browser.close()

async def test_metrics_dashboard():
    """Test that Metrics tab shows dashboard"""
    print("\n🧪 Testing Metrics tab content...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto('http://localhost:5555')
        await page.wait_for_load_state('networkidle')

        # Click Metrics tab
        metrics_tab = await page.query_selector('[data-tab="metrics"]')
        if metrics_tab:
            await metrics_tab.click()
            await page.wait_for_timeout(500)

            # Look for metrics dashboard
            dashboard = await page.query_selector('#metricsDashboard')
            dashboard_visible = await dashboard.is_visible() if dashboard else False

            print(f"\n📊 Metrics dashboard:")
            print(f"   Found: {'✅ Yes' if dashboard else '❌ No'}")
            print(f"   Visible: {'✅ Yes' if dashboard_visible else '❌ No'}")

            # Look for specific metric cards
            metric_cards = await page.query_selector_all('.metric-card')
            print(f"   Metric cards found: {len(metric_cards)}")

        await browser.close()

async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🐛 BUG INVESTIGATION - Tab Switching Issues")
    print("=" * 60)

    await test_tab_switching()
    await test_settings_content()
    await test_metrics_dashboard()

    print("\n" + "=" * 60)
    print("✅ Investigation complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_tests())

