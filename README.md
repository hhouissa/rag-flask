# RAG Document Q&A System

A production-ready RAG (Retrieval-Augmented Generation) application that allows users to ask questions about PDF documents and get AI-powered answers.

## Features

- **Document Processing**: PDF loading, text extraction, and chunking
- **Semantic Search**: Vector embeddings and similarity search
- **AI Integration**: Ollama LLM for contextual responses
- **Web Interface**: Flask-based web application with Bootstrap UI
- **API Endpoints**: RESTful API for programmatic access
- **Authentication**: User management and API key authentication
- **Cloud Integration**: AWS S3 for document storage
- **Docker Support**: Containerized deployment

## Prerequisites

- Python 3.10+
- Git
- Docker (optional)
- Ollama (for local LLM)

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/rag-flask-app.git
cd rag-flask-app

1- create the virtual environment:
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
2- Install dependencies:
pip install -r requirements.txt

3-  Configure environment:
# Edit .env with your configuration

4- Start Ollama and download models:
ollama serve  # In separate terminal
ollama pull qwen2.5:3b-instruct
ollama pull all-MiniLM-L6-v2

5- python app.py
The application will be available at http://localhost:5000

==============================================================
Configuration
Environment Variables
EMBEDDING_MODEL: HuggingFace embedding model (default: "all-MiniLM-L6-v2")
LLM_MODEL: Ollama LLM model (default: "qwen2.5:3b-instruct")
CHUNK_SIZE: Document chunk size (default: 1000)
CHUNK_OVERLAP: Chunk overlap size (default: 200)
S3_BUCKET_NAME: AWS S3 bucket name
SECRET_KEY: Flask secret key
API Endpoints
GET /api/docs - Swagger API documentation
POST /api/ask - Ask a question about documents
GET /api/documents - List indexed documents
POST /api/upload - Upload documents via API
POST /api/rebuild - Rebuild vector store (admin only)
GET /health - Health check endpoint
Usage
Upload PDF documents through the web interface
Ask questions about your documents
Get AI-powered answers with source attribution
Use API endpoints for programmatic access
Deployment
Docker
bash


1
2
docker build -t rag-app .
docker run -p 5000:5000 rag-app
Production
Use a production WSGI server (Gunicorn, uWSGI)
Configure a production database (PostgreSQL, MySQL)
Set up reverse proxy (Nginx)
Configure SSL certificates
Implement proper logging and monitoring
Security
API key authentication
CSRF protection
Input validation
Password hashing
Session management
Role-based access control
Architecture
The application follows a modular architecture with clear separation of concerns:

src/ - Core RAG components
templates/ - Web interface templates
static/ - Static assets
tests/ - Unit and integration tests
Contributing
Fork the repository
Create a feature branch
Make your changes
Add tests for new functionality
Submit a pull request
