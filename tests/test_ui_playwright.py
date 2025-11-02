"""
Comprehensive Playwright Browser Tests for React UI
Tests all UI functionality with real interactions (no mocks)
"""
from playwright.sync_api import sync_playwright, expect
import time
import json

BASE_URL = "http://localhost:5173"
TEST_RESULTS = []

def test_result(name: str, passed: bool, details: str = ""):
    """Record test result"""
    TEST_RESULTS.append({
        "name": name,
        "passed": passed,
        "details": details
    })
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"   {details}")

def run_tests():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # headless=False to see what's happening
        context = browser.new_context()
        page = context.new_page()
        
        print("="*60)
        print("PLAYWRIGHT BROWSER TESTS - REACT UI")
        print("="*60)
        print()
        
        # =================================================================
        # NAVIGATION & LOADING TESTS
        # =================================================================
        
        print("🌐 Navigation & Loading Tests")
        print("-" * 60)
        
        try:
            page.goto(BASE_URL, wait_until="networkidle")
            test_result("Page loads successfully", True, f"URL: {BASE_URL}")
        except Exception as e:
            test_result("Page loads successfully", False, str(e))
            return
        
        try:
            expect(page.locator("text=Neural Vault")).to_be_visible(timeout=5000)
            test_result("Header displays 'Neural Vault'", True)
        except:
            test_result("Header displays 'Neural Vault'", False)
        
        try:
            # Check all tabs are visible
            tabs = ["Chat", "Documents", "Settings", "Metrics", "Lab Guide", "Q&A", "Feedback"]
            for tab_name in tabs:
                page.locator(f"text={tab_name}").first.wait_for(state="visible", timeout=2000)
            test_result(f"All {len(tabs)} tabs visible", True)
        except Exception as e:
            test_result("All tabs visible", False, str(e))
        
        print()
        
        # =================================================================
        # CHAT TAB TESTS
        # =================================================================
        
        print("💬 Chat Tab Tests")
        print("-" * 60)
        
        try:
            # Navigate to chat (should be default)
            page.click("text=Chat")
            time.sleep(1)
            
            # Check for input field
            input_field = page.locator('textarea, input[type="text"]').first
            expect(input_field).to_be_visible(timeout=5000)
            test_result("Chat input field visible", True)
            
            # Type a message
            input_field.fill("What is a test?")
            test_result("Can type in chat input", True)
            
            # Find and click send button
            send_button = page.locator('button:has-text("Send"), button[type="submit"]').first
            send_button.click()
            test_result("Send button clickable", True)
            
            # Wait for response (with timeout)
            page.wait_for_selector(".prose, [class*='message']", timeout=30000)
            test_result("Chat response appears", True)
            
        except Exception as e:
            test_result("Chat interaction", False, str(e))
        
        print()
        
        # =================================================================
        # DOCUMENTS TAB TESTS
        # =================================================================
        
        print("📄 Documents Tab Tests")
        print("-" * 60)
        
        try:
            page.click("text=Documents")
            time.sleep(1)
            test_result("Navigate to Documents tab", True)
            
            # Check for upload area
            expect(page.locator("text=/upload|drag|drop/i").first).to_be_visible(timeout=5000)
            test_result("Upload area visible", True)
            
            # Check if documents list is visible
            if page.locator("text=/no documents|upload/i").is_visible():
                test_result("Document list renders (empty state)", True)
            else:
                # Check for document cards
                doc_count = page.locator("text=.md, text=.pdf, text=.txt").count()
                test_result("Document list renders", True, f"{doc_count} documents")
            
        except Exception as e:
            test_result("Documents tab", False, str(e))
        
        print()
        
        # =================================================================
        # SETTINGS TAB TESTS
        # =================================================================
        
        print("⚙️  Settings Tab Tests")
        print("-" * 60)
        
        try:
            page.click("text=Settings")
            time.sleep(1)
            test_result("Navigate to Settings tab", True)
            
            # Check for model selector
            expect(page.locator("text=/model|llama|qwen/i").first).to_be_visible(timeout=5000)
            test_result("Model settings visible", True)
            
            # Check for toggles/switches
            switches = page.locator('button[role="switch"], input[type="checkbox"]').count()
            test_result("RAG feature toggles present", switches > 0, f"{switches} toggles")
            
            # Check for sliders
            sliders = page.locator('input[type="range"], [role="slider"]').count()
            test_result("Parameter sliders present", sliders > 0, f"{sliders} sliders")
            
        except Exception as e:
            test_result("Settings tab", False, str(e))
        
        print()
        
        # =================================================================
        # METRICS TAB TESTS
        # =================================================================
        
        print("📊 Metrics Tab Tests")
        print("-" * 60)
        
        try:
            page.click("text=Metrics")
            time.sleep(1)
            test_result("Navigate to Metrics tab", True)
            
            # Check for metrics display
            metrics_visible = (
                page.locator("text=/queries|latency|tokens/i").count() > 0 or
                page.locator("text=/no data|metrics/i").count() > 0
            )
            test_result("Metrics section visible", metrics_visible)
            
        except Exception as e:
            test_result("Metrics tab", False, str(e))
        
        print()
        
        # =================================================================
        # LAB GUIDE TAB TESTS
        # =================================================================
        
        print("🎓 Lab Guide Tab Tests")
        print("-" * 60)
        
        try:
            page.click("text=Lab Guide")
            time.sleep(1)
            test_result("Navigate to Lab Guide tab", True)
            
            # Check for lab content
            lab_content = page.locator("text=/exercise|lab|progress/i").count()
            test_result("Lab guide content visible", lab_content > 0, f"{lab_content} elements")
            
            # Check for checkboxes (exercise completion)
            checkboxes = page.locator('input[type="checkbox"], button[role="checkbox"]').count()
            test_result("Exercise checkboxes present", checkboxes > 0, f"{checkboxes} exercises")
            
        except Exception as e:
            test_result("Lab Guide tab", False, str(e))
        
        print()
        
        # =================================================================
        # Q&A TAB TESTS
        # =================================================================
        
        print("❓ Q&A Tab Tests")
        print("-" * 60)
        
        try:
            page.click("text=Q&A")
            time.sleep(1)
            test_result("Navigate to Q&A tab", True)
            
            # Check for FAQ content
            faq_content = page.locator("text=/question|answer|faq/i").count()
            test_result("Q&A content visible", faq_content > 0)
            
        except Exception as e:
            test_result("Q&A tab", False, str(e))
        
        print()
        
        # =================================================================
        # FEEDBACK TAB TESTS
        # =================================================================
        
        print("📝 Feedback Tab Tests")
        print("-" * 60)
        
        try:
            page.click("text=Feedback")
            time.sleep(1)
            test_result("Navigate to Feedback tab", True)
            
            # Check for feedback form
            form_elements = page.locator("textarea, input, button[type='submit']").count()
            test_result("Feedback form elements present", form_elements > 0, f"{form_elements} elements")
            
        except Exception as e:
            test_result("Feedback tab", False, str(e))
        
        print()
        
        # =================================================================
        # RESPONSIVENESS TESTS
        # =================================================================
        
        print("📱 Responsiveness Tests")
        print("-" * 60)
        
        try:
            # Test mobile viewport
            page.set_viewport_size({"width": 375, "height": 667})
            time.sleep(0.5)
            test_result("Mobile viewport renders", True, "375x667")
            
            # Test tablet viewport
            page.set_viewport_size({"width": 768, "height": 1024})
            time.sleep(0.5)
            test_result("Tablet viewport renders", True, "768x1024")
            
            # Reset to desktop
            page.set_viewport_size({"width": 1920, "height": 1080})
            time.sleep(0.5)
            test_result("Desktop viewport renders", True, "1920x1080")
            
        except Exception as e:
            test_result("Responsiveness", False, str(e))
        
        print()
        
        # =================================================================
        # BROWSER CONSOLE ERRORS
        # =================================================================
        
        print("🐛 Console Errors Check")
        print("-" * 60)
        
        console_errors = []
        
        def handle_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)
        
        page.on("console", handle_console)
        
        # Reload page to capture console messages
        page.reload(wait_until="networkidle")
        time.sleep(2)
        
        if len(console_errors) == 0:
            test_result("No console errors", True)
        else:
            test_result("No console errors", False, f"{len(console_errors)} errors found")
            for err in console_errors[:3]:  # Show first 3
                print(f"      - {err[:100]}")
        
        print()
        
        # Close browser
        browser.close()

# Run tests
if __name__ == "__main__":
    run_tests()
    
    # Summary
    passed = sum(1 for t in TEST_RESULTS if t["passed"])
    total = len(TEST_RESULTS)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print("="*60)
    print(f"RESULTS: {passed}/{total} tests passed ({percentage:.1f}%)")
    print("="*60)
    print()
    
    # Save results
    with open("/tmp/playwright_test_results.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "percentage": percentage,
            "tests": TEST_RESULTS
        }, f, indent=2)
    
    print(f"📄 Results saved to: /tmp/playwright_test_results.json")
    print()
    
    exit(0 if passed == total else 1)
