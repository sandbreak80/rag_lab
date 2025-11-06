#!/usr/bin/env python3
"""
Test bstoner login through the UI
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

        print("🌐 Navigating to homepage...")
        await page.goto("http://frontend:80", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Click Sign In link if on register page
        try:
            sign_in = await page.query_selector('text=Sign In')
            if sign_in:
                await sign_in.click()
                await page.wait_for_timeout(1000)
        except:
            pass

        # Fill in login form
        print("\n🔐 Filling login form...")
        await page.fill('input[type="text"]', 'bstoner')
        await page.fill('input[type="password"]', '3Com3812')

        # Take screenshot before login
        await page.screenshot(path="/home/ubuntu/rag_lab/tests/before_login.png")
        print("📸 Before login screenshot saved")

        # Click login button
        login_btn = await page.query_selector('button[type="submit"]')
        if login_btn:
            await login_btn.click()
            print("✅ Login button clicked")
            await page.wait_for_timeout(3000)

        # Take screenshot after login
        await page.screenshot(path="/home/ubuntu/rag_lab/tests/after_login_bstoner.png")
        print("📸 After login screenshot saved")

        # Check if we're logged in by looking for chat interface
        chat_interface = await page.query_selector('textarea')
        if chat_interface:
            print("✅ Chat interface found - LOGIN SUCCESSFUL!")
        else:
            print("⚠️  Chat interface not found - checking for errors...")

        # Check for error messages
        error = await page.query_selector('text=/Invalid credentials|error|failed/i')
        if error:
            error_text = await error.text_content()
            print(f"❌ Error found: {error_text}")

        # Print any console errors
        errors = [msg for msg in console_messages if 'error' in msg.lower()]
        if errors:
            print("\n📋 Console errors:")
            for err in errors:
                print(f"  {err}")

        await browser.close()
        print("\n✅ Test complete")

if __name__ == "__main__":
    asyncio.run(main())

