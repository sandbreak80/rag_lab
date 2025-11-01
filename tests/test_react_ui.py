"""
Playwright tests for React UI
Run against dev server: http://localhost:5173
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5173"

def test_homepage_loads(page: Page):
    """Test that the homepage loads successfully"""
    page.goto(BASE_URL)

    # Check for main header
    expect(page.locator("text=Neural Vault")).to_be_visible()

    # Check for tab navigation
    expect(page.locator("text=Chat")).to_be_visible()
    expect(page.locator("text=Documents")).to_be_visible()
    expect(page.locator("text=Settings")).to_be_visible()
    expect(page.locator("text=Metrics")).to_be_visible()
    expect(page.locator("text=Lab Guide")).to_be_visible()


def test_all_tabs_accessible(page: Page):
    """Test that all tabs can be accessed"""
    page.goto(BASE_URL)

    tabs = [
        ("Chat", "Ask questions about your documents"),
        ("Documents", "Upload and manage your documents"),
        ("Settings", "Configure your RAG system"),
        ("Metrics", "Performance Metrics"),
        ("Lab Guide", "RAG Systems Lab Guide"),
        ("Q&A", "Frequently Asked Questions"),
        ("Feedback", "Your Feedback"),
    ]

    for tab_name, expected_content in tabs:
        print(f"\nTesting {tab_name} tab...")

        # Click tab
        page.click(f"text={tab_name}")
        page.wait_for_timeout(500)  # Wait for tab to load

        # Check that content is visible
        expect(page.locator(f"text={expected_content}")).to_be_visible(timeout=5000)

        print(f"✅ {tab_name} tab loads correctly")


def test_chat_tab_elements(page: Page):
    """Test chat tab has required elements"""
    page.goto(BASE_URL)
    page.click("text=Chat")
    page.wait_for_timeout(500)

    # Should show empty state or message input
    # Check for input area or empty state message
    chat_interface = page.locator(".chat-interface, textarea, text=Start a conversation")
    expect(chat_interface.first).to_be_visible(timeout=5000)

    print("✅ Chat interface renders")


def test_documents_tab_elements(page: Page):
    """Test documents tab has upload functionality"""
    page.goto(BASE_URL)
    page.click("text=Documents")
    page.wait_for_timeout(500)

    # Should have upload area
    expect(page.locator("text=Upload Documents, text=Drag")).to_be_visible(timeout=5000)

    print("✅ Documents upload area present")


def test_settings_tab_elements(page: Page):
    """Test settings tab has configuration options"""
    page.goto(BASE_URL)
    page.click("text=Settings")
    page.wait_for_timeout(500)

    # Should have settings controls
    # Look for common settings terms
    settings_content = page.locator("text=Model, text=Temperature, text=Settings")
    expect(settings_content.first).to_be_visible(timeout=5000)

    print("✅ Settings panel visible")


def test_metrics_tab_elements(page: Page):
    """Test metrics tab displays analytics"""
    page.goto(BASE_URL)
    page.click("text=Metrics")
    page.wait_for_timeout(500)

    # Should show metrics dashboard
    expect(page.locator("text=Performance, text=Queries, text=Metrics")).to_be_visible(timeout=5000)

    print("✅ Metrics dashboard present")


def test_lab_guide_tab_elements(page: Page):
    """Test lab guide has educational content"""
    page.goto(BASE_URL)
    page.click("text=Lab Guide")
    page.wait_for_timeout(500)

    # Should show lab content
    expect(page.locator("text=RAG, text=Lab")).to_be_visible(timeout=5000)

    print("✅ Lab guide content present")


def test_responsive_design(page: Page):
    """Test that UI is responsive"""
    page.goto(BASE_URL)

    # Test mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    page.wait_for_timeout(500)

    # Header should still be visible
    expect(page.locator("text=Neural Vault")).to_be_visible()

    # Desktop viewport
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.wait_for_timeout(500)

    expect(page.locator("text=Neural Vault")).to_be_visible()

    print("✅ Responsive design works")


def test_stats_in_header(page: Page):
    """Test that stats are displayed in header"""
    page.goto(BASE_URL)

    # Should show model name and stats
    expect(page.locator("text=Model:, text=llama")).to_be_visible(timeout=5000)

    print("✅ Stats displayed in header")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

