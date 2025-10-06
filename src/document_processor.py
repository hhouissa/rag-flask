import os
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
from typing import List
from config import RAGConfig

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes PDF documents: loading, splitting, and preparing for vector storage."""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP
        )
        logger.info(f"DocumentProcessor initialized with chunk_size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP}")

    def load_and_split_pdf(self, pdf_path: str) -> List[Document]:
        """Load a PDF document and split it into chunks with metadata."""
        try:
            logger.info(f"Loading and splitting PDF: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            
            # Add metadata to each document
            for i, doc in enumerate(docs):
                doc.metadata["source"] = os.path.basename(pdf_path)
                doc.metadata["page"] = i + 1  # Page number (1-indexed)
            
            chunks = self.text_splitter.split_documents(docs)
            logger.info(f"{os.path.basename(pdf_path)} split into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            raise

    def load_and_split_all_pdfs(self, data_folder: str = None) -> List[Document]:
        """Load and split all PDF files in the specified directory."""
        if data_folder is None:
            data_folder = self.config.DATA_DIR
            
        logger.info(f"Loading all PDFs from: {data_folder}")
        all_chunks = []
        
        if not os.path.exists(data_folder):
            logger.warning(f"Data folder does not exist: {data_folder}")
            return all_chunks
            
        pdf_files = [f for f in os.listdir(data_folder) 
                    if f.lower().endswith(".pdf")]
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {data_folder}")
            return all_chunks
            
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for filename in pdf_files:
            try:
                pdf_path = os.path.join(data_folder, filename)
                chunks = self.load_and_split_pdf(pdf_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                continue
                
        logger.info(f"Total chunks from all PDFs: {len(all_chunks)}")
        return all_chunks
