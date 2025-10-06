import os
import shutil
import logging
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List, Optional
from config import RAGConfig

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages the vector store for document storage and retrieval."""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.persist_directory = config.VECTOR_STORE_DIR
        self.vector_store = None
        logger.info(f"VectorStoreManager initialized with directory: {self.persist_directory}")

    def create_vector_store(self, chunks: List[Document], embeddings_model: HuggingFaceEmbeddings) -> Chroma:
        """Create a new vector store from document chunks."""
        try:
            logger.info(f"Creating vector store with {len(chunks)} chunks")
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings_model,
                persist_directory=self.persist_directory
            )
            self.vector_store.persist()
            logger.info("Vector store created and persisted successfully")
            return self.vector_store
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise

    def load_vector_store(self, embeddings_model: HuggingFaceEmbeddings) -> Chroma:
        """Load an existing vector store from disk."""
        try:
            logger.info("Loading existing vector store from disk")
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=embeddings_model
            )
            logger.info("Vector store loaded successfully")
            return self.vector_store
        except Exception as e:
            logger.warning(f"Failed to load vector store: {e}")
            raise

    def clear_vector_store(self):
        """Clear the existing vector store."""
        try:
            if os.path.exists(self.persist_directory):
                logger.info("Clearing existing vector store")
                shutil.rmtree(self.persist_directory)
                os.makedirs(self.persist_directory, exist_ok=True)
                logger.info("Vector store cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            raise
