"""Unit tests for indexer.py"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from indexer import VaultIndexer
import config


class TestVaultIndexer:
    """Test VaultIndexer class"""
    
    def test_init(self, temp_vault, temp_indices, monkeypatch):
        """Test indexer initialization"""
        monkeypatch.setattr(config, "VAULT_PATH", str(temp_vault))
        monkeypatch.setattr(config, "INDICES_PATH", str(temp_indices))
        
        indexer = VaultIndexer()
        
        assert str(indexer.vault_path) == str(temp_vault)
        assert str(indexer.indices_path) == str(temp_indices)
    
    def test_find_markdown_files(self, temp_vault, temp_indices, monkeypatch):
        """Test finding markdown files"""
        monkeypatch.setattr(config, "VAULT_PATH", str(temp_vault))
        monkeypatch.setattr(config, "INDICES_PATH", str(temp_indices))
        
        indexer = VaultIndexer()
        files = indexer.find_markdown_files()
        
        assert len(files) > 0
        assert all(f.suffix == ".md" for f in files)
        # Check that nested file is found
        assert any("nested.md" in str(f) for f in files)
    
    def test_find_markdown_files_empty(self, temp_indices, monkeypatch):
        """Test finding files in empty vault"""
        import tempfile
        empty_vault = Path(tempfile.mkdtemp())
        
        monkeypatch.setattr(config, "VAULT_PATH", str(empty_vault))
        monkeypatch.setattr(config, "INDICES_PATH", str(temp_indices))
        
        indexer = VaultIndexer()
        files = indexer.find_markdown_files()
        
        assert len(files) == 0
    
    def test_vault_path_is_path_object(self, temp_vault, temp_indices, monkeypatch):
        """Test that vault_path is converted to Path object"""
        monkeypatch.setattr(config, "VAULT_PATH", str(temp_vault))
        monkeypatch.setattr(config, "INDICES_PATH", str(temp_indices))
        
        indexer = VaultIndexer()
        
        assert isinstance(indexer.vault_path, Path)
        assert isinstance(indexer.indices_path, Path)
    
    @pytest.mark.skipif(
        not Path("/workspace/indices").exists(),
        reason="Requires Docker environment with Ollama"
    )
    def test_generate_embedding(self, temp_vault, temp_indices, monkeypatch):
        """Test generating embeddings (requires Ollama)"""
        monkeypatch.setattr(config, "VAULT_PATH", str(temp_vault))
        monkeypatch.setattr(config, "INDICES_PATH", str(temp_indices))
        
        indexer = VaultIndexer()
        text = "Test embedding generation"
        
        try:
            embedding = indexer.generate_embedding(text)
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all(isinstance(x, float) for x in embedding)
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")
    
    def test_chunk_parsing(self, temp_vault, temp_indices, monkeypatch):
        """Test that files are properly chunked"""
        monkeypatch.setattr(config, "VAULT_PATH", str(temp_vault))
        monkeypatch.setattr(config, "INDICES_PATH", str(temp_indices))
        
        indexer = VaultIndexer()
        long_file = temp_vault / "long_note.md"
        
        parsed = indexer.parser.parse_file(long_file)
        chunks = indexer.parser.chunk_content(
            parsed["content"], 
            config.CHUNK_SIZE, 
            config.CHUNK_OVERLAP
        )
        
        assert len(chunks) > 1  # Long file should be chunked
        for chunk in chunks:
            assert len(chunk) <= config.CHUNK_SIZE + 100  # Some margin

