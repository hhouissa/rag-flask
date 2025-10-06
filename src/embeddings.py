import logging
from langchain_huggingface import HuggingFaceEmbeddings
from config import RAGConfig

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    """Manages the embeddings model for vector operations."""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.embeddings = None
        logger.info("EmbeddingsManager initialized")

    def initialize_embeddings(self) -> HuggingFaceEmbeddings:
        """Initialize and return the embeddings model."""
        try:
            logger.info(f"Initializing embeddings model: {self.config.EMBEDDING_MODEL}")
            self.embeddings = HuggingFaceEmbeddings(model_name=self.config.EMBEDDING_MODEL)
            logger.info("Embeddings model loaded successfully")
            return self.embeddings
        except Exception as e:
            logger.error(f"Failed to initialize embeddings model: {e}")
            raise
