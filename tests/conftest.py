"""Pytest configuration and fixtures"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_vault():
    """Create a temporary vault with test markdown files"""
    vault_dir = tempfile.mkdtemp()
    vault_path = Path(vault_dir)
    
    # Create test files
    (vault_path / "simple.md").write_text("# Simple Note\n\nThis is a simple note.")
    
    (vault_path / "with_frontmatter.md").write_text("""---
title: Test Note
tags: [test, example]
date: 2025-01-01
---

# Frontmatter Note

This note has frontmatter metadata.
""")
    
    (vault_path / "with_links.md").write_text("""# Links Note

This has a [[wikilink]] and another [[internal link]].

Also has [external link](https://example.com).
""")
    
    (vault_path / "with_tags.md").write_text("""# Tagged Note

This note has #inline-tag and #another-tag.
""")
    
    (vault_path / "long_note.md").write_text("""# Long Note

""" + "\n\n".join([f"Paragraph {i}: " + ("Content " * 50) for i in range(10)]))
    
    # Create subdirectory
    subdir = vault_path / "subfolder"
    subdir.mkdir()
    (subdir / "nested.md").write_text("# Nested Note\n\nThis is in a subfolder.")
    
    yield vault_path
    
    # Cleanup
    shutil.rmtree(vault_dir)


@pytest.fixture
def temp_indices():
    """Create temporary indices directory"""
    indices_dir = tempfile.mkdtemp()
    yield Path(indices_dir)
    shutil.rmtree(indices_dir)


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing"""
    return {
        "simple": "# Test\n\nSimple content.",
        "with_frontmatter": """---
title: Test
tags: [one, two]
---

# Content

Body text.
""",
        "with_tags": "# Note\n\nThis has #tag1 and #tag2.",
        "with_links": "# Links\n\nSee [[other note]] and [external](https://example.com).",
        "long": "# Long\n\n" + ("A " * 1000),  # Long content for chunking tests
    }


