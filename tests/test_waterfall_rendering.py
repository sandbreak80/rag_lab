#!/usr/bin/env python3
"""
Test Waterfall Chart Rendering - Send query and wait for response
"""
from playwright.sync_api import sync_playwright
import sys

def test_waterfall():
    """Send query and debug waterfall rendering"""
    print("🌐 Opening browser...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console messages
        console_msgs = []
        page.on('console', lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))
        page.on('pageerror', lambda err: console_msgs.append(f"[ERROR] {err}"))

        try:
            print("📡 Navigating to http://frontend:80...")
            page.goto('http://frontend:80', wait_until='networkidle', timeout=15000)
            page.wait_for_timeout(2000)
            
            # Find and fill the textarea
            print("💬 Looking for input...")
            textarea = page.locator('textarea')
            if textarea.count() == 0:
                print("❌ No textarea found!")
                browser.close()
                return False
                
            print("💬 Sending query: 'What is RAG?'")
            textarea.fill('What is RAG?')
            
            # Click send button
            send_button = page.locator('button:has-text("Send")') if page.locator('button:has-text("Send")').count() > 0 else page.locator('button[type="submit"]')
            
            if send_button.count() > 0:
                print("🔘 Clicking send button...")
                send_button.click()
            else:
                print("⌨️  Pressing Enter...")
                textarea.press('Enter')
            
            # Wait for loading to start (optional)
            page.wait_for_timeout(1000)
            
            # Wait for response - look for "Performance Waterfall" text
            print("⏳ Waiting for response (up to 30s)...")
            try:
                page.wait_for_selector('text=Performance Waterfall', timeout=30000)
                print("✅ Response received! Waterfall chart appeared.")
            except:
                print("⚠️  Timeout waiting for waterfall, checking page state...")
            
            page.wait_for_timeout(2000)
            
            # Take screenshot
            print("📸 Taking screenshot...")
            page.screenshot(path='/test-results/waterfall-after-query.png', full_page=True)
            print("✅ Screenshot: /test-results/waterfall-after-query.png")
            
            # Check for waterfall
            waterfall_exists = page.locator('text=Performance Waterfall').count() > 0
            print(f"\n📊 Waterfall Found: {waterfall_exists}")
            
            if waterfall_exists:
                # Count SVG elements
                svg_count = page.locator('svg').count()
                print(f"📊 SVG elements: {svg_count}")
                
                # Get all rect elements with dimensions
                rects = page.locator('svg rect').all()
                print(f"📊 Total rect elements: {len(rects)}")
                
                if len(rects) > 0:
                    print("\n📏 Rect dimensions (first 15):")
                    visible_bars = 0
                    for i, rect in enumerate(rects[:15]):
                        width = rect.get_attribute('width')
                        height = rect.get_attribute('height')
                        x = rect.get_attribute('x')
                        y = rect.get_attribute('y')
                        fill = rect.get_attribute('fill')
                        class_name = rect.get_attribute('class')
                        
                        # Check if it's a visible bar (width > 1)
                        try:
                            width_num = float(width) if width else 0
                            if width_num > 1:
                                visible_bars += 1
                                print(f"   ✅ Rect {i}: width={width}, height={height}, x={x}, fill={fill}")
                            else:
                                print(f"   ⚠️  Rect {i}: width={width} (TOO SMALL!), height={height}, x={x}, fill={fill}")
                        except:
                            print(f"   ❓ Rect {i}: width={width}, height={height}, class={class_name}")
                    
                    print(f"\n📊 Visible bars (width > 1px): {visible_bars}/{len(rects)}")
                    
                    if visible_bars == 0:
                        print("🚨 PROBLEM: All bars have width <= 1px (rendering as lines!)")
                else:
                    print("⚠️  No rect elements found in SVG")
            
            # Print console messages
            if console_msgs:
                print(f"\n📝 Console Messages ({len(console_msgs)}):")
                for msg in console_msgs[:20]:
                    print(f"   {msg}")
            
            browser.close()
            return waterfall_exists

        except Exception as e:
            print(f"\n💥 Error: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path='/test-results/waterfall-error.png')
            browser.close()
            return False

if __name__ == "__main__":
    success = test_waterfall()
    sys.exit(0 if success else 1)

