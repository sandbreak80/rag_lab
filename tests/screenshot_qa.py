"""
Screenshot QA Test - Capture all tabs to verify layout
"""
import asyncio
from playwright.async_api import async_playwright
import os
from datetime import datetime

async def run_screenshot_qa():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # Navigate to UI
        url = "http://web-ui:5555"
        print(f"📸 Navigating to {url}")
        await page.goto(url, wait_until='domcontentloaded')
        await asyncio.sleep(5)  # Wait for JavaScript to initialize

        # Create screenshots directory
        screenshot_dir = "/workspace/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        tabs = ['chat', 'documents', 'settings', 'metrics', 'lab', 'qa', 'feedback']

        print("\n" + "="*60)
        print("📸 SCREENSHOT QA TEST")
        print("="*60)

        for tab_name in tabs:
            print(f"\n📸 Capturing tab: {tab_name.upper()}")

            # Switch tab using JavaScript directly
            await page.evaluate(f"switchTab('{tab_name}')")
            await asyncio.sleep(1)  # Wait for tab switch

            # Take screenshot
            screenshot_path = f"{screenshot_dir}/{timestamp}_{tab_name}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"   ✅ Saved: {screenshot_path}")

            # Check for lab guide visibility issue
            lab_panel = page.locator('#labGuidePanel')
            is_visible = await lab_panel.is_visible()

            if tab_name != 'lab' and is_visible:
                print(f"   ❌ BUG: Lab guide panel visible on {tab_name} tab!")
                bbox = await lab_panel.bounding_box()
                if bbox:
                    print(f"      Position: x={bbox['x']}, y={bbox['y']}")
                    print(f"      Size: {bbox['width']}x{bbox['height']}")
            elif tab_name == 'lab' and not is_visible:
                print(f"   ❌ BUG: Lab guide panel NOT visible on lab tab!")
            else:
                print(f"   ✅ Lab guide visibility correct")

            # Check tab content visibility
            tab_content = page.locator(f'#tab-{tab_name}')
            is_active = await tab_content.evaluate('el => el.classList.contains("active")')

            if is_active:
                print(f"   ✅ Tab content active class present")
            else:
                print(f"   ❌ BUG: Tab content missing active class!")

        print("\n" + "="*60)
        print("📸 Screenshot QA Complete")
        print(f"📁 Screenshots saved to: {screenshot_dir}")
        print("="*60 + "\n")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_screenshot_qa())

