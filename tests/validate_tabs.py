"""
Simple Playwright test to validate tab functionality
Run this locally: python3 tests/validate_tabs.py
"""
import asyncio
import sys
from playwright.async_api import async_playwright

async def validate_ui():
    print("\n" + "="*60)
    print("🧪 VALIDATING RAG LAB UI")
    print("="*60)

    async with async_playwright() as p:
        # Launch browser (headless=True for Docker)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # Navigate to app (use web-ui hostname in Docker network)
            print("\n📍 Navigating to http://web-ui:5555...")
            await page.goto('http://web-ui:5555', wait_until='networkidle')
            print("✅ Page loaded")

            # Wait a bit for everything to initialize
            await page.wait_for_timeout(2000)

            # Test 1: Check if tabs exist
            print("\n" + "-"*60)
            print("TEST 1: Tab Buttons")
            print("-"*60)
            tabs = ['chat', 'settings', 'metrics', 'lab']
            for tab in tabs:
                button = await page.query_selector(f'[data-tab="{tab}"]')
                print(f"  {tab.capitalize()} tab button: {'✅ Found' if button else '❌ Missing'}")

            # Test 2: Click each tab and check content
            print("\n" + "-"*60)
            print("TEST 2: Tab Content Visibility")
            print("-"*60)

            for tab_name in tabs:
                # Click the tab
                await page.click(f'[data-tab="{tab_name}"]')
                await page.wait_for_timeout(1000)

                # Check if tab content is visible
                tab_content = await page.query_selector(f'#tab-{tab_name}')
                if tab_content:
                    is_visible = await tab_content.is_visible()
                    has_active = 'active' in await tab_content.get_attribute('class')

                    # Get actual content
                    inner_html = await tab_content.inner_html()
                    has_content = len(inner_html.strip()) > 100

                    print(f"\n  {tab_name.upper()} Tab:")
                    print(f"    - Content div exists: ✅")
                    print(f"    - Is visible: {'✅' if is_visible else '❌'}")
                    print(f"    - Has active class: {'✅' if has_active else '❌'}")
                    print(f"    - Has content: {'✅' if has_content else '❌ (only ' + str(len(inner_html.strip())) + ' chars)'}")

                    # Show preview of content
                    text_content = await tab_content.inner_text()
                    preview = text_content[:150].replace('\n', ' ')
                    print(f"    - Preview: {preview}...")
                else:
                    print(f"\n  {tab_name.upper()} Tab: ❌ Content div not found!")

            # Test 3: Check specific elements in Settings tab
            print("\n" + "-"*60)
            print("TEST 3: Settings Tab Content")
            print("-"*60)

            await page.click('[data-tab="settings"]')
            await page.wait_for_timeout(1000)

            settings_elements = {
                'Settings Panel': '#settingsPanel',
                'Query Expansion Toggle': '#use-query-expansion',
                'BM25 Toggle': '#use-bm25',
                'Hybrid Toggle': '#use-hybrid',
                'Graph Toggle': '#use-graph',
                'Reranking Toggle': '#use-reranking',
                'Top-K Slider': '#top-k',
                'Model Selector': '#llm-model',
            }

            for name, selector in settings_elements.items():
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    print(f"  {name}: {'✅ Visible' if is_visible else '⚠️  Exists but hidden'}")
                else:
                    print(f"  {name}: ❌ Not found")

            # Test 4: Check Metrics tab
            print("\n" + "-"*60)
            print("TEST 4: Metrics Tab Content")
            print("-"*60)

            await page.click('[data-tab="metrics"]')
            await page.wait_for_timeout(1000)

            metrics_elements = {
                'Metrics Dashboard': '#metricsDashboard',
                'Latency Metric': '#metric-latency',
                'Results Metric': '#metric-results',
                'Precision Metric': '#metric-precision',
            }

            for name, selector in metrics_elements.items():
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    print(f"  {name}: {'✅ Visible' if is_visible else '⚠️  Exists but hidden'}")
                else:
                    print(f"  {name}: ❌ Not found")

            # Test 5: Check Lab Guide tab
            print("\n" + "-"*60)
            print("TEST 5: Lab Guide Tab Content")
            print("-"*60)

            await page.click('[data-tab="lab"]')
            await page.wait_for_timeout(1000)

            lab_elements = {
                'Lab Guide Panel': '#labGuidePanel',
                'Lab Section 1': '#lab-section-1',
                'Lab Section 2': '#lab-section-2',
            }

            for name, selector in lab_elements.items():
                element = await page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    print(f"  {name}: {'✅ Visible' if is_visible else '⚠️  Exists but hidden'}")
                else:
                    print(f"  {name}: ❌ Not found")

            # Test 6: Check gear and lab icons
            print("\n" + "-"*60)
            print("TEST 6: Icon Functionality")
            print("-"*60)

            # Test gear icon
            gear_icon = await page.query_selector('#settingsToggle')
            if gear_icon:
                print("  Gear icon: ✅ Found")
                await gear_icon.click()
                await page.wait_for_timeout(500)
                settings_tab_active = 'active' in await (await page.query_selector('#tab-settings')).get_attribute('class')
                print(f"    - Clicking opens Settings tab: {'✅' if settings_tab_active else '❌'}")
            else:
                print("  Gear icon: ❌ Not found")

            # Test lab icon
            lab_icon = await page.query_selector('#labGuideToggle')
            if lab_icon:
                print("  Lab icon: ✅ Found")
                await lab_icon.click()
                await page.wait_for_timeout(500)
                lab_tab_active = 'active' in await (await page.query_selector('#tab-lab')).get_attribute('class')
                print(f"    - Clicking opens Lab tab: {'✅' if lab_tab_active else '❌'}")
            else:
                print("  Lab icon: ❌ Not found")

            # Take screenshot
            print("\n" + "-"*60)
            await page.screenshot(path='/tmp/rag_lab_validation.png', full_page=True)
            print("📸 Full page screenshot saved to /tmp/rag_lab_validation.png")

            print("\n" + "="*60)
            print("✅ VALIDATION COMPLETE")
            print("="*60)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    print("\n🚀 Starting validation...")
    print("Make sure the app is running at http://localhost:5555")
    asyncio.run(validate_ui())

