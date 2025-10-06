import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from typing import Optional

logger = logging.getLogger(__name__)

class RAGChain:
    """Builds and manages the RAG question-answering chain."""

    def __init__(self, config, vector_store: Chroma):
        self.config = config
        self.vector_store = vector_store
        self.chain = None
        logger.info(f"RAGChain initialized with model: {config.LLM_MODEL}")

    def build_chain(self):
        """Build the RAG chain for question answering."""
        try:
            logger.info("Building RAG chain")
            llm = ChatOllama(model=self.config.LLM_MODEL, num_ctx=self.config.CONTEXT_WINDOW)
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )

            template = """You are a helpful assistant. First, try to answer using only the context below. 
If the context does not contain sufficient information to answer the question, 
indicate this clearly and then use your general knowledge to provide a helpful response.

Context:
{context}

Question: {question}

Answer:
"""
            prompt = ChatPromptTemplate.from_template(template)
            self.chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            logger.info("RAG chain built successfully")
            return self.chain
        except Exception as e:
            logger.error(f"Failed to build RAG chain: {e}")
            raise

    def query(self, question: str) -> str:
        """Query the RAG chain with a question."""
        # Input validation
        if not isinstance(question, str) or len(question.strip()) < 3:
            raise ValueError("Question must be a non-empty string with at least 3 characters.")
            
        if not self.chain:
            self.build_chain()

        logger.info(f"Processing question: {question}")
        try:
            answer = self.chain.invoke(question)
            logger.info("Question processed successfully")
            return answer
        except Exception as e:
            logger.error(f"Error processing question '{question}': {e}")
            raise
