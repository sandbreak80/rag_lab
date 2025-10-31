"""
Playwright UI tests for the RAG Chat web interface
"""
import pytest
import time
from playwright.sync_api import Page, expect


# Base URL for the web app
BASE_URL = "http://localhost:5555"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "en-US",
    }


class TestWebAppUI:
    """Test suite for web UI"""
    
    def test_homepage_loads(self, page: Page):
        """Test that the homepage loads successfully"""
        page.goto(BASE_URL)
        
        # Check title
        expect(page).to_have_title("RAG Chat - Ask Your Vault")
        
        # Check header is visible
        header = page.locator("h1")
        expect(header).to_be_visible()
        expect(header).to_contain_text("RAG Chat")
    
    def test_stats_display(self, page: Page):
        """Test that vault statistics are displayed"""
        page.goto(BASE_URL)
        
        # Wait for stats to load
        page.wait_for_selector("#chunk-count")
        
        # Check chunk count is displayed
        chunk_count = page.locator("#chunk-count")
        expect(chunk_count).to_be_visible()
        expect(chunk_count).not_to_contain_text("Loading")
        
        # Check model name is displayed
        model_name = page.locator("#model-name")
        expect(model_name).to_be_visible()
        expect(model_name).not_to_contain_text("Loading")
    
    def test_input_elements_present(self, page: Page):
        """Test that input elements are present and functional"""
        page.goto(BASE_URL)
        
        # Check input box
        input_box = page.locator("#question-input")
        expect(input_box).to_be_visible()
        expect(input_box).to_be_enabled()
        expect(input_box).to_have_attribute("placeholder", "Ask a question about your notes...")
        
        # Check ask button
        ask_button = page.locator("#ask-button")
        expect(ask_button).to_be_visible()
        expect(ask_button).to_be_enabled()
        expect(ask_button).to_contain_text("Ask")
    
    def test_empty_state_displayed(self, page: Page):
        """Test that empty state is shown initially"""
        page.goto(BASE_URL)
        
        # Check for empty state
        empty_state = page.locator(".empty-state")
        expect(empty_state).to_be_visible()
        expect(empty_state).to_contain_text("Ready to help")
    
    def test_input_validation(self, page: Page):
        """Test that empty questions are not submitted"""
        page.goto(BASE_URL)
        
        # Try to submit empty question
        ask_button = page.locator("#ask-button")
        initial_message_count = page.locator(".message").count()
        
        ask_button.click()
        
        # Should not create any messages
        time.sleep(0.5)
        final_message_count = page.locator(".message").count()
        assert initial_message_count == final_message_count
    
    def test_user_message_displayed(self, page: Page):
        """Test that user message is displayed when question is asked"""
        page.goto(BASE_URL)
        
        # Type a question
        question = "What is AI?"
        input_box = page.locator("#question-input")
        input_box.fill(question)
        
        # Submit
        ask_button = page.locator("#ask-button")
        ask_button.click()
        
        # Check user message appears
        user_message = page.locator(".message.user").first
        expect(user_message).to_be_visible()
        expect(user_message).to_contain_text(question)
        
        # Check empty state is removed
        empty_state = page.locator(".empty-state")
        expect(empty_state).not_to_be_visible()
    
    def test_loading_indicator_appears(self, page: Page):
        """Test that loading indicator appears while processing"""
        page.goto(BASE_URL)
        
        # Ask a question
        input_box = page.locator("#question-input")
        input_box.fill("Test question")
        
        ask_button = page.locator("#ask-button")
        ask_button.click()
        
        # Check loading indicator appears
        loading = page.locator(".loading")
        expect(loading).to_be_visible(timeout=2000)
    
    def test_input_disabled_during_processing(self, page: Page):
        """Test that input is disabled while processing"""
        page.goto(BASE_URL)
        
        # Ask a question
        input_box = page.locator("#question-input")
        input_box.fill("Test question")
        
        ask_button = page.locator("#ask-button")
        ask_button.click()
        
        # Check input and button are disabled
        expect(input_box).to_be_disabled(timeout=1000)
        expect(ask_button).to_be_disabled(timeout=1000)
    
    @pytest.mark.slow
    def test_answer_appears(self, page: Page):
        """Test that AI answer appears (may be slow)"""
        page.goto(BASE_URL)
        
        # Ask a simple question
        input_box = page.locator("#question-input")
        input_box.fill("What are AI prompting techniques?")
        
        ask_button = page.locator("#ask-button")
        ask_button.click()
        
        # Wait for assistant message (may take a while)
        assistant_message = page.locator(".message.assistant .message-content")
        expect(assistant_message).to_be_visible(timeout=180000)  # 3 minutes
        
        # Check it has content (not just loading)
        expect(assistant_message).not_to_contain_text("loading-dot")
    
    @pytest.mark.slow
    def test_sources_displayed(self, page: Page):
        """Test that sources are displayed with answers"""
        page.goto(BASE_URL)
        
        # Ask a question
        input_box = page.locator("#question-input")
        input_box.fill("What is prompt engineering?")
        
        ask_button = page.locator("#ask-button")
        ask_button.click()
        
        # Wait for sources to appear
        sources = page.locator(".sources")
        expect(sources).to_be_visible(timeout=180000)  # 3 minutes
        
        # Check sources have content
        expect(sources).to_contain_text("Sources")
        
        # Check for source scores
        source_score = page.locator(".source-score").first
        expect(source_score).to_be_visible()
    
    @pytest.mark.slow
    def test_multiple_questions(self, page: Page):
        """Test asking multiple questions in sequence (requires AI responses)"""
        page.goto(BASE_URL)
        
        questions = [
            "What is AI?",
            "What is machine learning?",
        ]
        
        for i, question in enumerate(questions):
            # Wait for input to be enabled (from previous question)
            input_box = page.locator("#question-input")
            if i > 0:
                # For subsequent questions, wait longer for previous one to finish
                expect(input_box).to_be_enabled(timeout=60000)
            
            # Ask question
            input_box.fill(question)
            
            ask_button = page.locator("#ask-button")
            ask_button.click()
            
            # Wait for user message to appear
            user_messages = page.locator(".message.user")
            expect(user_messages.last).to_contain_text(question)
        
        # Check we have multiple user messages
        user_message_count = page.locator(".message.user").count()
        assert user_message_count == len(questions)
    
    def test_enter_key_submits(self, page: Page):
        """Test that pressing Enter submits the question"""
        page.goto(BASE_URL)
        
        # Type and press Enter
        input_box = page.locator("#question-input")
        input_box.fill("Test question")
        input_box.press("Enter")
        
        # Check user message appears
        user_message = page.locator(".message.user").first
        expect(user_message).to_be_visible()
    
    def test_responsive_design(self, page: Page):
        """Test that UI works on mobile viewport"""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(BASE_URL)
        
        # Check essential elements are still visible
        expect(page.locator("h1")).to_be_visible()
        expect(page.locator("#question-input")).to_be_visible()
        expect(page.locator("#ask-button")).to_be_visible()
    
    def test_api_stats_endpoint(self, page: Page):
        """Test that API stats endpoint returns data"""
        response = page.request.get(f"{BASE_URL}/api/stats")
        
        assert response.ok
        data = response.json()
        
        assert "total_chunks" in data
        assert "embedding_model" in data
        assert "chat_model" in data
        assert data["total_chunks"] > 0
    
    def test_api_search_endpoint(self, page: Page):
        """Test that API search endpoint works"""
        response = page.request.post(
            f"{BASE_URL}/api/search",
            data={"query": "AI", "limit": 5}
        )
        
        assert response.ok
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) > 0
        
        # Check result structure
        result = data["results"][0]
        assert "title" in result
        assert "file" in result
        assert "score" in result
        assert "content" in result


class TestWebAppAccessibility:
    """Accessibility tests"""
    
    def test_page_has_proper_semantics(self, page: Page):
        """Test that page has proper semantic HTML"""
        page.goto(BASE_URL)
        
        # Check for header
        expect(page.locator("header")).to_be_visible()
        
        # Check for main content area
        expect(page.locator("h1")).to_be_visible()
        
        # Check inputs have proper attributes
        input_box = page.locator("#question-input")
        expect(input_box).to_have_attribute("type", "text")
        # Check placeholder exists (value doesn't matter)
        placeholder = input_box.get_attribute("placeholder")
        assert placeholder is not None and len(placeholder) > 0
    
    def test_buttons_are_keyboard_accessible(self, page: Page):
        """Test that buttons can be accessed via keyboard"""
        page.goto(BASE_URL)
        
        # Tab to the input
        page.keyboard.press("Tab")
        
        # Check input is focused
        input_box = page.locator("#question-input")
        expect(input_box).to_be_focused()


class TestWebAppPerformance:
    """Performance tests"""
    
    def test_page_loads_quickly(self, page: Page):
        """Test that page loads in reasonable time"""
        start_time = time.time()
        page.goto(BASE_URL)
        
        # Wait for main content
        page.wait_for_selector("h1")
        
        load_time = time.time() - start_time
        
        # Should load in less than 3 seconds
        assert load_time < 3.0, f"Page took {load_time:.2f}s to load"
    
    def test_stats_load_quickly(self, page: Page):
        """Test that stats load in reasonable time"""
        page.goto(BASE_URL)
        
        start_time = time.time()
        
        # Wait for stats to update
        page.wait_for_function(
            "document.getElementById('chunk-count').textContent !== 'Loading...'"
        )
        
        load_time = time.time() - start_time
        
        # Should load in less than 2 seconds
        assert load_time < 2.0, f"Stats took {load_time:.2f}s to load"


@pytest.mark.visual
class TestWebAppVisual:
    """Visual regression tests"""
    
    def test_homepage_screenshot(self, page: Page):
        """Take screenshot of homepage"""
        page.goto(BASE_URL)
        page.wait_for_selector("h1")
        
        # Take screenshot
        page.screenshot(path="tests/screenshots/homepage.png")
    
    def test_chat_with_message_screenshot(self, page: Page):
        """Take screenshot of chat with a message"""
        page.goto(BASE_URL)
        
        # Add a message
        input_box = page.locator("#question-input")
        input_box.fill("What is AI?")
        
        ask_button = page.locator("#ask-button")
        ask_button.click()
        
        # Wait for user message
        page.wait_for_selector(".message.user")
        
        # Take screenshot
        page.screenshot(path="tests/screenshots/chat_with_message.png")

