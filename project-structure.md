rag-flask-app/
├── app.py                          # Main Flask application
├── auth.py                         # Authentication module
├── config.py                       # Configuration management
├── models.py                       # Database models
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container definition
├── .dockerignore                   # Docker ignore file
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore file
├── README.md                       # Project documentation
├── check_requirements.py           # Dependency checker
├── tests/
│   ├── __init__.py
│   ├── test_rag_system.py         # RAG system tests
│   └── test_flask_app.py          # Flask application tests
├── src/
│   ├── __init__.py
│   ├── rag_system.py              # Main RAG orchestrator
│   ├── embeddings.py              # Embeddings management
│   ├── vectorstore.py             # Vector store management
│   ├── rag_chain.py               # RAG chain implementation
│   ├── document_processor.py      # Document processing
│   ├── s3_loader.py               # S3 file operations
│   └── utils.py                   # Utility functions
├── templates/
│   ├── base.html                  # Base template
│   ├── index.html                 # Home page
│   ├── ask.html                   # Question asking page
│   ├── upload.html                # Document upload page
│   ├── login.html                 # User login page
│   ├── register.html              # User registration page
│   ├── profile.html               # User profile page
│   └── results.html               # Query results page
├── static/
│   ├── swagger.json               # Swagger API documentation
│   └── css/
│       └── style.css              # Custom styles
├── data/                          # Local PDF storage (created automatically)
├── chroma_db/                     # Vector database (created automatically)
└── migrations/                    # Database migrations
