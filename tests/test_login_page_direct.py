#!/usr/bin/env python3
"""
Test login by navigating to /login directly
"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))

        print("🌐 Navigating to /login...")
        await page.goto("http://frontend:80/login", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Check for login form
        username_field = await page.query_selector('input[placeholder*="username" i], input[name="username"]')
        password_field = await page.query_selector('input[type="password"]')

        if not username_field or not password_field:
            print("❌ Login form not found")
            await page.screenshot(path="/home/ubuntu/rag_lab/tests/login_page_missing.png")
            return

        print("✅ Login form found")

        # Fill in credentials
        print("\n🔐 Filling login form...")
        await username_field.fill('bstoner')
        await password_field.fill('3Com3812')

        # Take screenshot before submit
        await page.screenshot(path="/home/ubuntu/rag_lab/tests/login_filled.png")
        print("📸 Form filled screenshot saved")

        # Submit form
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
            await submit_btn.click()
            print("✅ Submit clicked, waiting for response...")
            await page.wait_for_timeout(3000)

        # Check result
        current_url = page.url
        print(f"\n🔗 Current URL after login: {current_url}")

        # Check if redirected to home
        if current_url == "http://frontend/" or current_url == "http://frontend":
            print("✅ LOGIN SUCCESSFUL - Redirected to home!")
        elif "login" in current_url:
            print("⚠️  Still on login page - checking for errors...")
            error = await page.query_selector('[class*="error"], [class*="alert"]')
            if error:
                error_text = await error.text_content()
                print(f"❌ Error: {error_text}")

        # Take final screenshot
        await page.screenshot(path="/home/ubuntu/rag_lab/tests/after_login_final.png")
        print("📸 Final screenshot saved")

        # Check for console errors
        errors = [msg for msg in console_messages if 'error' in msg.lower()]
        if errors:
            print("\n📋 Console errors:")
            for err in errors[-5:]:
                print(f"  {err}")

        await browser.close()
        print("\n✅ Test complete")

if __name__ == "__main__":
    asyncio.run(main())

