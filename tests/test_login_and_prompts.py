#!/usr/bin/env python3
"""
Test login issue and baseline prompts
"""
import asyncio
from playwright.async_api import async_playwright
import json

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
        
        # Take screenshot
        await page.screenshot(path="/home/ubuntu/rag_lab/tests/homepage.png")
        print("📸 Homepage screenshot saved")
        
        # Check for baseline prompts
        print("\n🔍 Checking for baseline prompts...")
        low_prompt = await page.query_selector('text=🟢 Low')
        medium_prompt = await page.query_selector('text=🟡 Medium')
        high_prompt = await page.query_selector('text=🔴 High')
        
        print(f"✓ Low prompt found: {low_prompt is not None}")
        print(f"✓ Medium prompt found: {medium_prompt is not None}")
        print(f"✓ High prompt found: {high_prompt is not None}")
        
        # Try to register a new user
        print("\n📝 Testing registration...")
        try:
            register_btn = await page.query_selector('text=Create Account')
            if register_btn:
                await register_btn.click()
                await page.wait_for_timeout(1000)
                
                # Fill registration form
                username = f"testuser_{int(asyncio.get_event_loop().time())}"
                await page.fill('input[type="text"]', username)
                await page.fill('input[type="email"]', f"{username}@test.com")
                password_fields = await page.query_selector_all('input[type="password"]')
                if len(password_fields) >= 1:
                    await password_fields[0].fill("TestPassword123!")
                
                # Click register submit
                submit_btn = await page.query_selector('button[type="submit"]')
                if submit_btn:
                    await submit_btn.click()
                    await page.wait_for_timeout(2000)
                    
                    # Take screenshot after registration
                    await page.screenshot(path="/home/ubuntu/rag_lab/tests/after_register.png")
                    print("✓ Registration attempted")
        except Exception as e:
            print(f"⚠️  Registration error: {e}")
        
        # Try to login
        print("\n🔐 Testing login with existing account...")
        try:
            # Go back to login if needed
            login_link = await page.query_selector('text=Sign In')
            if login_link:
                await login_link.click()
                await page.wait_for_timeout(1000)
            
            # Fill login form - try with a known account
            username_input = await page.query_selector('input[type="text"]')
            if username_input:
                await username_input.fill("testuser")
            
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill("testpass123")
            
            # Click login button
            login_btn = await page.query_selector('button[type="submit"]')
            if login_btn:
                await login_btn.click()
                await page.wait_for_timeout(2000)
                
                # Take screenshot after login attempt
                await page.screenshot(path="/home/ubuntu/rag_lab/tests/after_login.png")
                print("✓ Login attempted")
        except Exception as e:
            print(f"⚠️  Login error: {e}")
        
        # Print console messages
        if console_messages:
            print("\n📋 Console messages:")
            for msg in console_messages[-20:]:
                print(f"  {msg}")
        
        await browser.close()
        print("\n✅ Test complete - check screenshots in /home/ubuntu/rag_lab/tests/")

if __name__ == "__main__":
    asyncio.run(main())

