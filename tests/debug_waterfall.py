#!/usr/bin/env python3
"""
Debug Waterfall Chart - Take screenshot and inspect rendering
"""
from playwright.sync_api import sync_playwright
import sys

def debug_waterfall():
    """Take screenshot of waterfall chart"""
    print("🌐 Opening browser to debug waterfall chart...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("📡 Navigating to http://frontend:80...")
            page.goto('http://frontend:80', wait_until='networkidle', timeout=15000)

            # Wait for page to load
            page.wait_for_timeout(2000)

            # Take full page screenshot
            print("📸 Taking full page screenshot...")
            page.screenshot(path='/test-results/waterfall-full-page.png', full_page=True)
            print("✅ Screenshot saved to: /test-results/waterfall-full-page.png")

            # Check if waterfall chart exists
            waterfall_exists = page.locator('text=Performance Waterfall').count() > 0
            print(f"\n📊 Waterfall Chart Found: {waterfall_exists}")

            # Get SVG elements (Recharts renders to SVG)
            svg_count = page.locator('svg').count()
            print(f"📊 SVG elements found: {svg_count}")

            # Get bar elements
            bar_count = page.locator('svg rect[class*="recharts-bar"]').count()
            print(f"📊 Bar elements found: {bar_count}")

            # Check for Cell elements
            cell_count = page.locator('svg path[class*="recharts-rectangle"]').count()
            print(f"📊 Rectangle path elements: {cell_count}")

            browser.close()
            return True

        except Exception as e:
            print(f"\n💥 Error during test: {e}")
            browser.close()
            return False

if __name__ == "__main__":
    success = debug_waterfall()
    sys.exit(0 if success else 1)

