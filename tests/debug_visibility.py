"""
Debug script to check actual computed styles
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_visibility():
    print("\n🔍 DEBUGGING TAB VISIBILITY")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Navigate
            await page.goto('http://web-ui:5555', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Click Settings tab
            print("\n🖱️  Clicking Settings tab...")
            await page.click('[data-tab="settings"]')
            await page.wait_for_timeout(1000)
            
            # Get computed style
            settings_tab = await page.query_selector('#tab-settings')
            if settings_tab:
                # Get all computed CSS
                computed_display = await settings_tab.evaluate('el => window.getComputedStyle(el).display')
                computed_visibility = await settings_tab.evaluate('el => window.getComputedStyle(el).visibility')
                computed_opacity = await settings_tab.evaluate('el => window.getComputedStyle(el).opacity')
                has_class_active = 'active' in await settings_tab.get_attribute('class')
                
                print(f"\n#tab-settings:")
                print(f"  - Has 'active' class: {has_class_active}")
                print(f"  - Computed display: {computed_display}")
                print(f"  - Computed visibility: {computed_visibility}")
                print(f"  - Computed opacity: {computed_opacity}")
                
                # Check if .active class is being applied
                active_display = await page.evaluate('''() => {
                    const style = document.querySelector('#tab-settings.active');
                    if (!style) return 'selector not matching';
                    return window.getComputedStyle(style).display;
                }''')
                print(f"  - #tab-settings.active selector display: {active_display}")
                
                # Check CSS rules
                css_rules = await page.evaluate('''() => {
                    const el = document.querySelector('#tab-settings');
                    const sheets = document.styleSheets;
                    const rules = [];
                    for (let sheet of sheets) {
                        try {
                            for (let rule of sheet.cssRules) {
                                if (rule.selectorText && (
                                    rule.selectorText.includes('#tab-settings') ||
                                    rule.selectorText.includes('.tab-content')
                                )) {
                                    rules.push({
                                        selector: rule.selectorText,
                                        display: rule.style.display || 'not set'
                                    });
                                }
                            }
                        } catch(e) {}
                    }
                    return rules;
                }''')
                print(f"\n  Relevant CSS rules:")
                for rule in css_rules:
                    print(f"    - {rule['selector']}: display={rule['display']}")
            
            # Check Lab tab too
            print("\n\n🖱️  Clicking Lab tab...")
            await page.click('[data-tab="lab"]')
            await page.wait_for_timeout(1000)
            
            lab_tab = await page.query_selector('#tab-lab')
            if lab_tab:
                computed_display = await lab_tab.evaluate('el => window.getComputedStyle(el).display')
                has_class_active = 'active' in await lab_tab.get_attribute('class')
                
                print(f"\n#tab-lab:")
                print(f"  - Has 'active' class: {has_class_active}")
                print(f"  - Computed display: {computed_display}")
            
            print("\n" + "="*60)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_visibility())

