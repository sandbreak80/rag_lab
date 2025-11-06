#!/usr/bin/env python3
"""
Frontend Console Error Checker - Uses Playwright to capture browser errors
"""
from playwright.sync_api import sync_playwright
import sys
import json

def check_frontend_console():
    """Check frontend for console errors using Playwright"""
    print("🌐 Opening browser to check frontend...")

    console_messages = []
    errors = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console messages
        page.on('console', lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location
        }))

        # Capture page errors
        page.on('pageerror', lambda err: page_errors.append(str(err)))

        # Capture failed requests
        page.on('requestfailed', lambda request: errors.append(f"Failed request: {request.url}"))

        try:
            print("📡 Navigating to http://frontend:80...")
            response = page.goto('http://frontend:80', wait_until='networkidle', timeout=15000)

            print(f"✅ Page loaded with status: {response.status}")

            # Wait for React to render
            page.wait_for_timeout(3000)

            # Check if root div has content
            root_content = page.locator('#root').inner_html()
            has_content = len(root_content.strip()) > 0

            print(f"\n📊 Root div has content: {has_content}")
            if has_content:
                print(f"   Content length: {len(root_content)} characters")
            else:
                print("   ❌ Root div is EMPTY!")

            # Report console messages
            print(f"\n📝 Console Messages ({len(console_messages)}):")
            for msg in console_messages:
                icon = '🔴' if msg['type'] == 'error' else '⚠️' if msg['type'] == 'warning' else '📘'
                print(f"   {icon} [{msg['type'].upper()}] {msg['text'][:200]}")

            # Report page errors
            if page_errors:
                print(f"\n🚨 JavaScript Errors ({len(page_errors)}):")
                for err in page_errors:
                    print(f"   ❌ {err}")

            # Report failed requests
            if errors:
                print(f"\n🌐 Failed Requests ({len(errors)}):")
                for err in errors:
                    print(f"   ❌ {err}")

            # Take screenshot if there are errors
            if page_errors or not has_content:
                screenshot_path = '/test-results/frontend-error.png'
                page.screenshot(path=screenshot_path)
                print(f"\n📸 Screenshot saved to: {screenshot_path}")

            browser.close()

            # Return exit code
            has_errors = len(page_errors) > 0 or not has_content
            if has_errors:
                print("\n❌ FRONTEND HAS ERRORS!")
                return False
            else:
                print("\n✅ Frontend loaded successfully!")
                return True

        except Exception as e:
            print(f"\n💥 Error during test: {e}")
            browser.close()
            return False

if __name__ == "__main__":
    success = check_frontend_console()
    sys.exit(0 if success else 1)

