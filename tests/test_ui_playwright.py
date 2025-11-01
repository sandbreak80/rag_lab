"""
Playwright E2E Tests for RAG Lab UI
Tests microservices architecture with headless Chrome
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://rag-web-ui:5555"

def test_homepage_loads(page: Page):
    """Test that the homepage loads successfully"""
    page.goto(BASE_URL)

    # Wait for page to load
    page.wait_for_load_state("networkidle")

    # Check title
    expect(page).to_have_title("🧠 Neural Vault - AI-Powered Knowledge")

    # Check for main elements
    expect(page.locator("h1")).to_contain_text("Neural Vault")
    expect(page.locator("#question-input")).to_be_visible()
    expect(page.locator("#ask-button")).to_be_visible()

    # Take screenshot
    page.screenshot(path="/screenshots/01_homepage.png")
    print("✅ Homepage loaded successfully")

def test_stats_display(page: Page):
    """Test that stats are displayed"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Wait for stats to load
    page.wait_for_selector("#chunk-count", timeout=10000)

    # Check stats elements
    chunk_count = page.locator("#chunk-count").inner_text()
    model_name = page.locator("#model-name").inner_text()

    assert chunk_count is not None
    assert model_name is not None

    print(f"✅ Stats loaded: {chunk_count} chunks, model: {model_name}")

    # Screenshot with stats
    page.screenshot(path="/screenshots/02_stats_loaded.png")

def test_empty_state(page: Page):
    """Test empty state display"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Check for empty state
    expect(page.locator(".empty-state")).to_be_visible()
    expect(page.locator(".empty-state h2")).to_contain_text("Ready to explore")

    # Check suggestions
    suggestions = page.locator(".suggestion")
    expect(suggestions).to_have_count(3)

    page.screenshot(path="/screenshots/03_empty_state.png")
    print("✅ Empty state displayed correctly")

def test_input_field_interaction(page: Page):
    """Test input field interaction"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Type in input field
    input_field = page.locator("#question-input")
    input_field.click()
    input_field.fill("What is machine learning?")

    # Check that text was entered
    expect(input_field).to_have_value("What is machine learning?")

    # Screenshot with input
    page.screenshot(path="/screenshots/04_input_filled.png")
    print("✅ Input field works correctly")

def test_suggestion_click(page: Page):
    """Test clicking a suggestion"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Click first suggestion
    page.locator(".suggestion").first.click()

    # Check that input was filled
    input_field = page.locator("#question-input")
    input_value = input_field.input_value()

    assert len(input_value) > 0
    print(f"✅ Suggestion clicked: {input_value}")

    page.screenshot(path="/screenshots/05_suggestion_clicked.png")

def test_ask_button_state(page: Page):
    """Test ask button states"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    ask_button = page.locator("#ask-button")

    # Button should be visible and enabled initially
    expect(ask_button).to_be_visible()
    expect(ask_button).to_be_enabled()

    # Check button text
    button_text = page.locator("#button-text").inner_text()
    assert button_text == "Ask"

    print("✅ Ask button in correct initial state")
    page.screenshot(path="/screenshots/06_ask_button_ready.png")

def test_responsive_design(page: Page):
    """Test responsive design at different viewports"""
    # Test desktop
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.screenshot(path="/screenshots/07_desktop_view.png")
    print("✅ Desktop view rendered")

    # Test tablet
    page.set_viewport_size({"width": 768, "height": 1024})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.screenshot(path="/screenshots/08_tablet_view.png")
    print("✅ Tablet view rendered")

    # Test mobile
    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.screenshot(path="/screenshots/09_mobile_view.png")
    print("✅ Mobile view rendered")

def test_api_integration(page: Page):
    """Test that API calls are being made"""
    page.goto(BASE_URL)

    # Listen for API calls
    requests = []
    page.on("request", lambda request: requests.append(request.url))

    page.wait_for_load_state("networkidle")

    # Check that stats API was called
    stats_called = any("/api/stats" in url for url in requests)
    assert stats_called, "Stats API should be called"

    print(f"✅ API integration working: {len(requests)} requests made")
    print(f"   Stats API called: {stats_called}")

def test_console_errors(page: Page):
    """Test for console errors"""
    console_messages = []
    page.on("console", lambda msg: console_messages.append({
        "type": msg.type,
        "text": msg.text
    }))

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Check for errors
    errors = [msg for msg in console_messages if msg["type"] == "error"]

    if errors:
        print(f"⚠️  Console errors found: {len(errors)}")
        for error in errors:
            print(f"   - {error['text']}")
    else:
        print("✅ No console errors")

    # Take screenshot
    page.screenshot(path="/screenshots/10_console_check.png")

def test_network_requests(page: Page):
    """Test network requests and responses"""
    page.goto(BASE_URL)

    # Intercept network requests
    responses = []

    def handle_response(response):
        responses.append({
            "url": response.url,
            "status": response.status,
            "ok": response.ok
        })

    page.on("response", handle_response)
    page.wait_for_load_state("networkidle")

    # Wait a bit for all requests
    time.sleep(2)

    # Check responses
    failed = [r for r in responses if not r["ok"]]

    print(f"✅ Network requests: {len(responses)} total")
    print(f"   Successful: {len(responses) - len(failed)}")
    print(f"   Failed: {len(failed)}")

    if failed:
        for resp in failed:
            print(f"   ❌ {resp['status']}: {resp['url']}")

# Pytest configuration
@pytest.fixture(scope="function")
def page(browser):
    """Create a new page for each test"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    page.close()
    context.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

