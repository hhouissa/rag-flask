# config.py
import os
from dataclasses import dataclass

@dataclass
class RAGConfig:
    """Configuration class for RAG application."""
    
    # Model configurations
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5:3b-instruct")
    CONTEXT_WINDOW: int = int(os.getenv("CONTEXT_WINDOW", "4096"))
    
    # Document processing
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Storage paths
    VECTOR_STORE_DIR: str = os.getenv("VECTOR_STORE_DIR", "chroma_db")
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    
    # AWS S3 configurations
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "raggy-1")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    
    # Flask configurations
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def __post_init__(self):
        # Ensure directories exist
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.VECTOR_STORE_DIR, exist_ok=True)
