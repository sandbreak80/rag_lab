#!/usr/bin/env python3
"""
Debug Waterfall Chart - Send query first, then inspect
"""
from playwright.sync_api import sync_playwright
import sys
import time

def debug_waterfall():
    """Send query and screenshot waterfall chart"""
    print("🌐 Opening browser...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("📡 Navigating to http://frontend:80...")
            page.goto('http://frontend:80', wait_until='networkidle', timeout=15000)
            page.wait_for_timeout(2000)

            # Send a test query to trigger waterfall
            print("💬 Sending test query...")
            page.fill('textarea[placeholder*="Ask a question"]', 'What is RAG?')
            page.click('button[type="submit"]', timeout=5000) if page.locator('button[type="submit"]').count() > 0 else page.keyboard.press('Enter')

            # Wait for response
            print("⏳ Waiting for response...")
            page.wait_for_timeout(10000)

            # Take screenshot
            print("📸 Taking screenshot...")
            page.screenshot(path='/test-results/waterfall-with-query.png', full_page=True)
            print("✅ Screenshot saved")

            # Check for waterfall
            waterfall_exists = page.locator('text=Performance Waterfall').count() > 0
            print(f"\n📊 Waterfall Chart Found: {waterfall_exists}")

            # Count SVG elements
            svg_count = page.locator('svg').count()
            print(f"📊 Total SVG elements: {svg_count}")

            # Check for bar/rect elements in all SVGs
            rect_count = page.locator('svg rect').count()
            print(f"📊 Total rect elements in SVGs: {rect_count}")

            # Check for specific Recharts classes
            recharts_bars = page.locator('[class*="recharts-bar"]').count()
            recharts_layer = page.locator('[class*="recharts-layer"]').count()
            print(f"📊 Recharts bar elements: {recharts_bars}")
            print(f"📊 Recharts layer elements: {recharts_layer}")

            # Get actual bar dimensions if they exist
            if rect_count > 0:
                print("\n📏 Inspecting rect elements...")
                rects = page.locator('svg rect').all()
                for i, rect in enumerate(rects[:10]):  # First 10
                    width = rect.get_attribute('width')
                    height = rect.get_attribute('height')
                    fill = rect.get_attribute('fill')
                    print(f"   Rect {i}: width={width}, height={height}, fill={fill}")

            browser.close()
            return True

        except Exception as e:
            print(f"\n💥 Error: {e}")
            import traceback
            traceback.print_exc()
            browser.close()
            return False

if __name__ == "__main__":
    success = debug_waterfall()
    sys.exit(0 if success else 1)

