#!/usr/bin/env python3
"""
Detailed Frontend Check - Identify 404 errors
"""
from playwright.sync_api import sync_playwright
import sys

def check_frontend_detailed():
    """Check frontend and identify all failed requests"""
    print("🔍 Detailed Frontend Check...")

    failed_requests = []
    console_messages = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture all console messages with full details
        def handle_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            })

        page.on('console', handle_console)

        # Capture all failed requests
        def handle_request_failed(request):
            failed_requests.append({
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type,
                'failure': request.failure
            })

        page.on('requestfailed', handle_request_failed)

        # Also track responses
        responses = []
        def handle_response(response):
            responses.append({
                'url': response.url,
                'status': response.status,
                'ok': response.ok
            })

        page.on('response', handle_response)

        try:
            print("📡 Loading http://frontend:80...")
            page.goto('http://frontend:80', wait_until='networkidle', timeout=15000)
            page.wait_for_timeout(2000)

            # Check root content
            root = page.locator('#root')
            root_html = root.inner_html()

            print(f"\n📊 Status:")
            print(f"   Root div characters: {len(root_html)}")
            print(f"   Has app content: {len(root_html) > 100}")

            # Report console messages
            print(f"\n📝 Console Messages:")
            for msg in console_messages:
                icon = '🔴' if msg['type'] == 'error' else '⚠️' if msg['type'] == 'warning' else '📘'
                print(f"   {icon} [{msg['type'].upper()}] {msg['text']}")

            # Report failed requests
            if failed_requests:
                print(f"\n❌ Failed Requests:")
                for req in failed_requests:
                    print(f"   URL: {req['url']}")
                    print(f"   Type: {req['resource_type']}")
                    print(f"   Failure: {req['failure']}")

            # Report 404s
            not_found = [r for r in responses if r['status'] == 404]
            if not_found:
                print(f"\n🚫 404 Not Found Responses:")
                for resp in not_found:
                    print(f"   {resp['url']}")

            # Take screenshot
            page.screenshot(path='/test-results/frontend-screenshot.png', full_page=True)
            print(f"\n📸 Screenshot saved: /test-results/frontend-screenshot.png")

            browser.close()
            return True

        except Exception as e:
            print(f"\n💥 Error: {e}")
            browser.close()
            return False

if __name__ == "__main__":
    success = check_frontend_detailed()
    sys.exit(0 if success else 1)

