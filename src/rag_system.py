import os
import shutil
import logging
from typing import List, Optional
from config import RAGConfig
from src.embeddings import EmbeddingsManager
from src.s3_loader import S3Downloader
from src.document_processor import DocumentProcessor
from src.vectorstore import VectorStoreManager
from src.rag_chain import RAGChain
from src.utils import timing_decorator

logger = logging.getLogger(__name__)

class RAGSystem:
    """Main class that orchestrates the entire RAG system."""

    def __init__(self, config: RAGConfig):
        self.config = config
        logger.info("Initializing RAG System Components...")
        self.embeddings_manager = EmbeddingsManager(config)
        self.s3_downloader = S3Downloader(config)
        self.document_processor = DocumentProcessor(config)
        self.vector_store_manager = VectorStoreManager(config)
        self.rag_chain = None
        logger.info("RAG System Components Initialized.")

    @timing_decorator
    def initialize_system(self, download_new: bool = False, pdf_filename: Optional[str] = None, force_rebuild: bool = False):
        """Initialize the complete RAG system with detailed logging."""

        logger.info("STARTING RAG SYSTEM INITIALIZATION")

        # === STEP 1: Initialize Embeddings ===
        logger.info("Initializing Embeddings Model")
        embeddings = self.embeddings_manager.initialize_embeddings()

        # === STEP 2: Handle PDF Download (Optional) ===
        if download_new and pdf_filename:
            logger.info(f"DOWNLOADING '{pdf_filename}' FROM S3...")
            pdf_path = self.s3_downloader.download_pdf(pdf_filename)
            logger.info(f"Successfully downloaded: {pdf_path}")
        else:
            logger.info("Skipping S3 download. Using existing local PDFs...")

        # === STEP 3: Check Local PDFs ===
        logger.info(f"SCANNING FOR PDF FILES IN: {os.path.abspath(self.config.DATA_DIR)}")

        pdf_files = [
            f for f in os.listdir(self.config.DATA_DIR)
            if os.path.isfile(os.path.join(self.config.DATA_DIR, f)) and f.lower().endswith(".pdf")
        ]

        if not pdf_files:
            logger.error(f"NO PDF FILES FOUND in '{self.config.DATA_DIR}'!")
            raise FileNotFoundError(f"No PDFs found in {self.config.DATA_DIR}")

        logger.info(f"FOUND {len(pdf_files)} PDF FILE(S): {pdf_files}")

        # === STEP 4: Load & Split All PDFs ===
        logger.info("LOADING AND SPLITTING PDFs INTO TEXT CHUNKS...")
        chunks = self.document_processor.load_and_split_all_pdfs()
        if not chunks:
            raise ValueError("No text chunks generated from PDFs.")
        logger.info(f"SUCCESSFULLY PROCESSED {len(chunks)} TEXT CHUNKS.")

        # === STEP 5: Load or Create Vector Store ===
        logger.info("LOADING OR CREATING VECTOR STORE (ChromaDB)...")
        vector_store = None

        if not force_rebuild:
            try:
                vector_store = self.vector_store_manager.load_vector_store(embeddings)
                logger.info("Loaded existing vector store from disk.")
            except Exception as e:
                logger.warning(f"No existing vector store found: {str(e)[:100]}... Creating new one...")

        if vector_store is None or force_rebuild:
            try:
                # Delete old vector store if forcing rebuild
                if force_rebuild and os.path.exists(self.vector_store_manager.persist_directory):
                    logger.info("Deleting old vector store for clean rebuild...")
                    self.vector_store_manager.clear_vector_store()
                vector_store = self.vector_store_manager.create_vector_store(chunks, embeddings)
                logger.info("Created and persisted new vector store.")
            except Exception as create_error:
                logger.error(f"FAILED TO CREATE VECTOR STORE: {create_error}")
                raise

        # === STEP 6: Build RAG Chain ===
        logger.info(f"BUILDING RAG CHAIN WITH LLM: {self.config.LLM_MODEL}...")
        self.rag_chain = RAGChain(self.config, vector_store)
        self.rag_chain.build_chain()
        logger.info("RAG Chain built successfully.")

        logger.info("RAG SYSTEM INITIALIZATION COMPLETE!")
        return self.rag_chain

    def run_queries(self, questions: List[str]):
        """Run a series of queries on the RAG system."""
        if not self.rag_chain:
            logger.error("RAG system not initialized. Call initialize_system() first.")
            return

        logger.info(f"RUNNING {len(questions)} QUERIES...")
        results = []
        for i, question in enumerate(questions, 1):
            logger.info(f"[QUERY {i}/{len(questions)}] {question}")
            try:
                answer = self.rag_chain.query(question)
                results.append({"question": question, "answer": answer})
                logger.info(f"Answer: {answer}")
            except Exception as e:
                logger.error(f"Error on question '{question}': {e}")
                results.append({"question": question, "error": str(e)})
        logger.info("All queries completed.")
        return results
