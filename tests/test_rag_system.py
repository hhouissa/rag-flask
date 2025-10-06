# tests/test_rag_system.py
import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from config import RAGConfig
from src.rag_system import RAGSystem
from src.embeddings import EmbeddingsManager
from src.document_processor import DocumentProcessor
from src.vectorstore import VectorStoreManager
from src.rag_chain import RAGChain

class TestRAGSystem:
    """Test cases for RAG system components."""

    def setup_method(self):
        """Setup test environment."""
        self.config = RAGConfig()
        # Use temporary directories for testing
        self.temp_data_dir = tempfile.mkdtemp()
        self.temp_vector_dir = tempfile.mkdtemp()
        self.config.DATA_DIR = self.temp_data_dir
        self.config.VECTOR_STORE_DIR = self.temp_vector_dir

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_data_dir, ignore_errors=True)
        shutil.rmtree(self.temp_vector_dir, ignore_errors=True)

    def test_rag_system_initialization(self):
        """Test RAG system initialization."""
        rag_system = RAGSystem(self.config)
        assert rag_system.embeddings_manager is not None
        assert rag_system.s3_downloader is not None
        assert rag_system.document_processor is not None
        assert rag_system.vector_store_manager is not None

    @patch('src.embeddings.HuggingFaceEmbeddings')
    def test_embeddings_manager(self, mock_embeddings):
        """Test embeddings manager."""
        manager = EmbeddingsManager(self.config)
        mock_embedding_instance = Mock()
        mock_embeddings.return_value = mock_embedding_instance
        
        result = manager.initialize_embeddings()
        assert result == mock_embedding_instance
        mock_embeddings.assert_called_once_with(model_name=self.config.EMBEDDING_MODEL)

    def test_document_processor_initialization(self):
        """Test document processor initialization."""
        processor = DocumentProcessor(self.config)
        assert processor.config == self.config
        assert processor.text_splitter is not None

    def test_vector_store_manager_initialization(self):
        """Test vector store manager initialization."""
        manager = VectorStoreManager(self.config)
        assert manager.config == self.config
        assert manager.persist_directory == self.config.VECTOR_STORE_DIR

    def test_config_values(self):
        """Test configuration values."""
        assert self.config.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
        assert self.config.LLM_MODEL == "qwen2.5:3b-instruct"
        assert self.config.CHUNK_SIZE == 1000
        assert self.config.CHUNK_OVERLAP == 200

if __name__ == '__main__':
    pytest.main([__file__])
