"""Unit tests for parser.py"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parser import MarkdownParser


class TestMarkdownParser:
    """Test MarkdownParser class"""
    
    def test_init(self):
        """Test parser initialization"""
        parser = MarkdownParser()
        assert parser is not None
    
    def test_extract_frontmatter_valid(self):
        """Test extracting valid frontmatter"""
        parser = MarkdownParser()
        content = """---
title: Test
tags: [one, two]
date: 2025-01-01
---

Body content"""
        
        metadata = parser._extract_frontmatter(content)
        
        assert metadata["title"] == "Test"
        assert metadata["tags"] == ["one", "two"]
        # Note: YAML parses dates as date objects
        assert str(metadata["date"]) == "2025-01-01"
    
    def test_extract_frontmatter_none(self):
        """Test content without frontmatter"""
        parser = MarkdownParser()
        content = "# Title\n\nNo frontmatter here"
        
        metadata = parser._extract_frontmatter(content)
        
        assert metadata == {}
    
    def test_extract_frontmatter_invalid(self):
        """Test invalid frontmatter"""
        parser = MarkdownParser()
        content = """---
invalid: yaml: syntax:
---

Body"""
        
        metadata = parser._extract_frontmatter(content)
        
        assert metadata == {}
    
    def test_extract_tags_frontmatter(self):
        """Test extracting tags from frontmatter"""
        parser = MarkdownParser()
        content = "test content"
        metadata = {"tags": ["tag1", "tag2"]}
        
        tags = parser._extract_tags(content, metadata)
        
        assert "tag1" in tags
        assert "tag2" in tags
    
    def test_extract_tags_inline(self):
        """Test extracting inline tags"""
        parser = MarkdownParser()
        content = "This has #inline-tag and #another-tag"
        metadata = {}
        
        tags = parser._extract_tags(content, metadata)
        
        assert "inline-tag" in tags
        assert "another-tag" in tags
    
    def test_extract_tags_mixed(self):
        """Test extracting both frontmatter and inline tags"""
        parser = MarkdownParser()
        content = "Content with #inline-tag"
        metadata = {"tags": ["frontmatter-tag"]}
        
        tags = parser._extract_tags(content, metadata)
        
        assert "frontmatter-tag" in tags
        assert "inline-tag" in tags
        assert len(tags) == 2
    
    def test_extract_wikilinks(self):
        """Test extracting wikilinks"""
        parser = MarkdownParser()
        content = "See [[Note One]] and [[Note Two|Alias]]"
        
        links = parser._extract_wikilinks(content)
        
        assert "Note One" in links
        assert "Note Two" in links
        assert len(links) == 2
    
    def test_extract_wikilinks_with_heading(self):
        """Test wikilinks with heading anchors"""
        parser = MarkdownParser()
        content = "See [[Note#Section]]"
        
        links = parser._extract_wikilinks(content)
        
        assert "Note" in links
        assert len(links) == 1
    
    def test_extract_markdown_links(self):
        """Test extracting markdown links"""
        parser = MarkdownParser()
        content = "Check [Example](https://example.com) and [Another](http://test.com)"
        
        links = parser._extract_markdown_links(content)
        
        assert len(links) == 2
        assert links[0]["text"] == "Example"
        assert links[0]["url"] == "https://example.com"
    
    def test_extract_title_from_frontmatter(self):
        """Test extracting title from frontmatter"""
        parser = MarkdownParser()
        content = "# Heading\n\nContent"
        metadata = {"title": "Frontmatter Title"}
        file_path = Path("test.md")
        
        title = parser._extract_title(content, metadata, file_path)
        
        assert title == "Frontmatter Title"
    
    def test_extract_title_from_h1(self):
        """Test extracting title from H1"""
        parser = MarkdownParser()
        content = "# Main Heading\n\nContent"
        metadata = {}
        file_path = Path("test.md")
        
        title = parser._extract_title(content, metadata, file_path)
        
        assert title == "Main Heading"
    
    def test_extract_title_from_filename(self):
        """Test extracting title from filename"""
        parser = MarkdownParser()
        content = "No headings"
        metadata = {}
        file_path = Path("my-note.md")
        
        title = parser._extract_title(content, metadata, file_path)
        
        assert title == "my-note"
    
    def test_chunk_content_small(self):
        """Test chunking content smaller than chunk_size"""
        parser = MarkdownParser()
        content = "Small content"
        
        chunks = parser.chunk_content(content, chunk_size=1000, overlap=200)
        
        assert len(chunks) == 1
        assert chunks[0] == content
    
    def test_chunk_content_large(self):
        """Test chunking large content"""
        parser = MarkdownParser()
        content = "Word " * 500  # ~2500 chars
        
        chunks = parser.chunk_content(content, chunk_size=1000, overlap=200)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 1200  # chunk_size + some margin
    
    def test_chunk_content_overlap(self):
        """Test that chunks have proper overlap"""
        parser = MarkdownParser()
        content = "A " * 1000  # Long content
        
        chunks = parser.chunk_content(content, chunk_size=100, overlap=20)
        
        # Check that consecutive chunks overlap
        for i in range(len(chunks) - 1):
            # Some content should appear in both chunks
            assert len(chunks[i]) > 0
            assert len(chunks[i+1]) > 0
    
    def test_parse_file_simple(self, temp_vault):
        """Test parsing a simple file"""
        parser = MarkdownParser()
        file_path = temp_vault / "simple.md"
        
        result = parser.parse_file(file_path)
        
        assert result is not None
        assert result["title"] == "Simple Note"
        assert "simple" in result["content"]
        assert result["file_path"] == str(file_path)
    
    def test_parse_file_with_frontmatter(self, temp_vault):
        """Test parsing file with frontmatter"""
        parser = MarkdownParser()
        file_path = temp_vault / "with_frontmatter.md"
        
        result = parser.parse_file(file_path)
        
        assert result["title"] == "Test Note"
        assert "test" in result["tags"]
        assert "example" in result["tags"]
        # YAML parses dates as date objects
        assert str(result["metadata"]["date"]) == "2025-01-01"
    
    def test_parse_file_with_links(self, temp_vault):
        """Test parsing file with links"""
        parser = MarkdownParser()
        file_path = temp_vault / "with_links.md"
        
        result = parser.parse_file(file_path)
        
        assert "wikilink" in result["wikilinks"]
        assert "internal link" in result["wikilinks"]
        assert len(result["markdown_links"]) > 0
    
    def test_parse_file_nonexistent(self):
        """Test parsing nonexistent file"""
        parser = MarkdownParser()
        file_path = Path("/nonexistent/file.md")
        
        result = parser.parse_file(file_path)
        
        assert result is None
    
    def test_parse_file_empty(self, temp_vault):
        """Test parsing empty file"""
        parser = MarkdownParser()
        empty_file = temp_vault / "empty.md"
        empty_file.write_text("")
        
        result = parser.parse_file(empty_file)
        
        assert result is not None
        assert result["content"] == ""

