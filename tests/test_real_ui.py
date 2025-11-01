"""
Real UI interaction test - click tabs and verify what's actually shown
"""
import asyncio
from playwright.async_api import async_playwright

async def test_real_interactions():
    print("\n🎭 REAL USER INTERACTION TEST")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Navigate
            await page.goto('http://web-ui:5555', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            print("\n1️⃣ TESTING: Click each tab and check what's visible\n")
            
            tabs_to_test = [
                ('chat', 'messages', 'Chat messages container'),
                ('documents', 'upload-section', 'Upload section'),
                ('settings', 'settingsPanel', 'Settings panel'),
                ('metrics', 'metricsDashboard', 'Metrics dashboard'),
                ('lab', 'labGuidePanel', 'Lab guide panel')
            ]
            
            for tab_name, expected_element_id, description in tabs_to_test:
                print(f"\n📍 Clicking {tab_name.upper()} tab...")
                
                # Click tab
                tab_btn = await page.query_selector(f'[data-tab="{tab_name}"]')
                if not tab_btn:
                    print(f"  ❌ Tab button not found!")
                    continue
                    
                await tab_btn.click()
                await page.wait_for_timeout(500)
                
                # Check if expected element is visible
                element = await page.query_selector(f'#{expected_element_id}')
                if element:
                    is_visible = await element.is_visible()
                    # Get bounding box to verify it's actually rendered
                    bbox = await element.bounding_box()
                    
                    print(f"  Element '{expected_element_id}':")
                    print(f"    - Exists: ✅")
                    print(f"    - is_visible(): {'✅' if is_visible else '❌'}")
                    print(f"    - Has bounding box: {'✅' if bbox else '❌'}")
                    if bbox:
                        print(f"    - Position: x={bbox['x']:.0f}, y={bbox['y']:.0f}")
                        print(f"    - Size: {bbox['width']:.0f}x{bbox['height']:.0f}")
                    
                    # Try to get some text content
                    text = await element.inner_text()
                    text_preview = text[:100].replace('\n', ' ') if text else "NO TEXT"
                    print(f"    - Text preview: {text_preview}...")
                    
                    # Overall verdict
                    if bbox and bbox['width'] > 0 and bbox['height'] > 0:
                        print(f"  ✅ VISIBLE AND RENDERED")
                    else:
                        print(f"  ❌ NOT ACTUALLY VISIBLE")
                else:
                    print(f"  ❌ Element '{expected_element_id}' not found!")
            
            print("\n\n2️⃣ TESTING: Documents tab specifically\n")
            await page.click('[data-tab="documents"]')
            await page.wait_for_timeout(500)
            
            # Check if upload section moved to documents tab
            upload_in_documents = await page.query_selector('#tab-documents .upload-section')
            upload_anywhere = await page.query_selector('.upload-section')
            
            print(f"Upload section in Documents tab: {'✅' if upload_in_documents else '❌'}")
            print(f"Upload section exists somewhere: {'✅' if upload_anywhere else '❌'}")
            
            if upload_anywhere:
                parent = await upload_anywhere.evaluate('el => el.parentElement.id')
                print(f"Upload section parent ID: {parent}")
            
            print("\n\n3️⃣ TESTING: Taking screenshots of each tab\n")
            
            for tab_name in ['chat', 'documents', 'settings', 'metrics', 'lab']:
                await page.click(f'[data-tab="{tab_name}"]')
                await page.wait_for_timeout(500)
                filename = f'/workspace/screenshots/tab_{tab_name}.png'
                await page.screenshot(path=filename, full_page=True)
                print(f"  📸 {tab_name}: {filename}")
            
            print("\n\n4️⃣ TESTING: Check for JavaScript errors\n")
            errors = []
            page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
            
            # Trigger some interactions
            await page.click('[data-tab="settings"]')
            await page.wait_for_timeout(500)
            await page.click('#settingsToggle')  # Gear icon
            await page.wait_for_timeout(500)
            
            if errors:
                print(f"  ❌ JavaScript errors found:")
                for err in errors:
                    print(f"    - {err}")
            else:
                print(f"  ✅ No JavaScript errors")
            
            print("\n" + "="*60)
            print("✅ REAL INTERACTION TEST COMPLETE")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_real_interactions())

