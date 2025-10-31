"""
Markdown parser for extracting content, metadata, tags, and links
"""
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


class MarkdownParser:
    """Parse markdown files and extract metadata, content, tags, and links"""
    
    def __init__(self):
        # Regex patterns
        self.frontmatter_pattern = re.compile(r'^---\s*\n(.*?\n)---\s*\n', re.DOTALL)
        self.inline_tag_pattern = re.compile(r'(?:^|\s)#([\w\-/]+)')
        self.wikilink_pattern = re.compile(r'\[\[(.*?)\]\]')
        self.markdown_link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a markdown file and extract all relevant information
        
        Returns:
            Dict with: content, metadata, tags, links, title, file_path
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
            return None
            
        # Extract frontmatter
        metadata = self._extract_frontmatter(content)
        
        # Remove frontmatter from content
        content_without_fm = self.frontmatter_pattern.sub('', content)
        
        # Extract tags (from frontmatter and inline)
        tags = self._extract_tags(content_without_fm, metadata)
        
        # Extract links
        wikilinks = self._extract_wikilinks(content_without_fm)
        markdown_links = self._extract_markdown_links(content_without_fm)
        
        # Extract title (from frontmatter or first h1)
        title = self._extract_title(content_without_fm, metadata, file_path)
        
        # Get relative path from vault root
        relative_path = str(file_path)
        
        return {
            'content': content_without_fm.strip(),
            'metadata': metadata,
            'tags': tags,
            'wikilinks': wikilinks,
            'markdown_links': markdown_links,
            'title': title,
            'file_path': relative_path,
            'file_name': file_path.name,
            'modified_time': file_path.stat().st_mtime,
        }
    
    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter"""
        match = self.frontmatter_pattern.match(content)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as e:
                print(f"⚠️  YAML parse error: {e}")
                return {}
        return {}
    
    def _extract_tags(self, content: str, metadata: Dict[str, Any]) -> List[str]:
        """Extract tags from frontmatter and inline hashtags"""
        tags = set()
        
        # From frontmatter
        if 'tags' in metadata:
            fm_tags = metadata['tags']
            if isinstance(fm_tags, str):
                tags.add(fm_tags.lower())
            elif isinstance(fm_tags, list):
                tags.update(tag.lower() for tag in fm_tags if isinstance(tag, str))
        
        if 'tag' in metadata:
            tag = metadata['tag']
            if isinstance(tag, str):
                tags.add(tag.lower())
        
        # From inline hashtags
        inline_tags = self.inline_tag_pattern.findall(content)
        tags.update(tag.lower() for tag in inline_tags)
        
        return sorted(list(tags))
    
    def _extract_wikilinks(self, content: str) -> List[str]:
        """Extract wikilinks [[like this]]"""
        matches = self.wikilink_pattern.findall(content)
        links = []
        for match in matches:
            # Handle [[link|alias]] format
            link = match.split('|')[0].strip()
            # Handle [[link#heading]] format
            link = link.split('#')[0].strip()
            if link:
                links.append(link)
        return links
    
    def _extract_markdown_links(self, content: str) -> List[Dict[str, str]]:
        """Extract markdown links [text](url)"""
        matches = self.markdown_link_pattern.findall(content)
        return [{'text': text, 'url': url} for text, url in matches]
    
    def _extract_title(self, content: str, metadata: Dict[str, Any], file_path: Path) -> str:
        """Extract title from frontmatter, first H1, or filename"""
        # Try frontmatter
        if 'title' in metadata:
            return str(metadata['title'])
        
        # Try first H1
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Fall back to filename without extension
        return file_path.stem
    
    def chunk_content(self, content: str, chunk_size: int = 1000, 
                     overlap: int = 200) -> List[str]:
        """
        Split content into overlapping chunks
        Tries to break on paragraphs/sentences when possible
        """
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        max_iterations = len(content) // (chunk_size - overlap) + 10  # Safety limit
        iteration = 0
        
        while start < len(content):
            iteration += 1
            if iteration > max_iterations:
                print(f"⚠️ Chunking exceeded max iterations ({max_iterations}), breaking")
                break
            
            end = start + chunk_size
            
            # If not at the end, try to break at a good spot
            if end < len(content):
                # Try to break at paragraph
                break_point = content.rfind('\n\n', start, end)
                if break_point == -1:
                    # Try to break at sentence
                    break_point = content.rfind('. ', start, end)
                if break_point == -1:
                    # Try to break at any newline
                    break_point = content.rfind('\n', start, end)
                if break_point != -1 and break_point > start:
                    end = break_point
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            # BUGFIX: Ensure we always advance
            new_start = end - overlap if end < len(content) else end
            if new_start <= start:  # Safety: ensure progress
                new_start = start + max(1, chunk_size // 2)
            start = new_start
        
        return chunks


def test_parser():
    """Test the parser with a sample markdown file"""
    parser = MarkdownParser()
    
    test_content = """---
title: Test Note
tags:
  - python
  - testing
date: 2025-01-15
---

# Test Note

This is a test note with #inline-tags and [[wikilinks]].

Here's another paragraph with a [[link to another note]] and a #markdown tag.

You can also link like this: [external link](https://example.com)

## Section 2

More content here with [[another link#heading]].
"""
    
    # Create temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        temp_path = Path(f.name)
    
    try:
        result = parser.parse_file(temp_path)
        print("\n📄 Parse Result:")
        print(f"Title: {result['title']}")
        print(f"Tags: {result['tags']}")
        print(f"Wikilinks: {result['wikilinks']}")
        print(f"Metadata: {result['metadata']}")
        print(f"Content length: {len(result['content'])} chars")
        
        # Test chunking
        chunks = parser.chunk_content(result['content'], chunk_size=50, overlap=10)
        print(f"\nChunks: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {len(chunk)} chars")
    finally:
        temp_path.unlink()


if __name__ == '__main__':
    test_parser()

