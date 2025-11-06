#!/usr/bin/env python3
"""
Check what the homepage shows
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to homepage...")
        await page.goto("http://frontend:80", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Get page title
        title = await page.title()
        print(f"📄 Page title: {title}")

        # Get page URL
        url = page.url
        print(f"🔗 Current URL: {url}")

        # Take screenshot
        await page.screenshot(path="/home/ubuntu/rag_lab/tests/homepage_check.png", full_page=True)
        print("📸 Screenshot saved")

        # Check for various elements
        elements = {
            'Login form': 'input[type="password"]',
            'Chat interface': 'textarea',
            'Sign In link': 'text=Sign In',
            'Create Account link': 'text=Create Account',
            'Username input': 'input[placeholder*="username" i]',
            'Email input': 'input[type="email"]',
        }

        print("\n🔍 Checking for elements:")
        for name, selector in elements.items():
            element = await page.query_selector(selector)
            print(f"  {name}: {'✅ Found' if element else '❌ Not found'}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

