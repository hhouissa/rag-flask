# app.py
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

import logging
from flask import Flask, request, render_template, redirect, url_for, jsonify, flash
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from config import RAGConfig
from src.rag_system import RAGSystem
from models import db, User
from auth import require_api_key, require_admin, register_user, authenticate_user
import shutil

# Configure logging
logging.basicConfig(
    level=getattr(logging, RAGConfig().LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.RAGConfig')
app.secret_key = app.config['SECRET_KEY']

if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rag_app.db'

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

# Enable CORS
CORS(app)

# Initialize RAG system
config = RAGConfig()
rag_system = RAGSystem(config)

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "RAG Document Q&A API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def initialize_rag_system():
    """Initialize the RAG system if not already initialized."""
    try:
        if not hasattr(rag_system, 'rag_chain') or rag_system.rag_chain is None:
            rag_system.initialize_system()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        return False

first_request = True

@app.before_request
def create_tables():
    """Create database tables."""
    db.create_all()
    
    # Create default admin user if none exists
    if User.query.count() == 0:
        admin_user, error = register_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        if admin_user:
            logger.info("Default admin user created")
        else:
            logger.error(f"Failed to create default admin user: {error}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
        user, error = register_user(username, email, password)
        if user:
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(error or 'Registration failed', 'error')
    
    return render_template('register.html')

@app.route('/')
@login_required
def index():
    """Home page."""
    vector_store_loaded = hasattr(rag_system, 'rag_chain') and rag_system.rag_chain is not None
    document_count = 0
    if vector_store_loaded:
        try:
            # Count documents in data directory
            data_dir = config.DATA_DIR
            if os.path.exists(data_dir):
                document_count = len([f for f in os.listdir(data_dir) if f.lower().endswith('.pdf')])
        except Exception:
            pass
    
    return render_template(
        'index.html',
        vector_store_loaded=vector_store_loaded,
        document_count=document_count,
        llm_model=config.LLM_MODEL,
        current_user=current_user
    )

@app.route('/ask', methods=['GET', 'POST'])
@login_required
def ask():
    """Ask a question page."""
    global rag_system
    
    # Ensure RAG system is initialized
    if not hasattr(rag_system, 'rag_chain') or rag_system.rag_chain is None:
        try:
            rag_system.initialize_system()
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            flash('RAG system not initialized. Please check logs.', 'error')
            return render_template('ask.html')
    
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if not question:
            flash('Please enter a question', 'error')
            return render_template('ask.html')
        
        try:
            # Initialize RAG system if needed
            if not initialize_rag_system():
                flash('RAG system not initialized. Please check logs.', 'error')
                return render_template('ask.html')
            
            answer = rag_system.rag_chain.query(question)
            return render_template('ask.html', question=question, answer=answer)
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            flash(f'Error processing question: {str(e)}', 'error')
            return render_template('ask.html')
    
    return render_template('ask.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload documents page."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return render_template('upload.html')
        
        files = request.files.getlist('file')
        uploaded_files = []
        
        for file in files:
            if file and file.filename:
                if file.filename.lower().endswith('.pdf'):
                    filepath = os.path.join(config.DATA_DIR, file.filename)
                    file.save(filepath)
                    uploaded_files.append(file.filename)
                    logger.info(f"Uploaded file: {file.filename}")
                else:
                    flash(f'Invalid file type for {file.filename}. Only PDF files are allowed.', 'error')
                    return render_template('upload.html')
        
        if uploaded_files:
            message = f"Successfully uploaded {len(uploaded_files)} file(s)"
            # Rebuild vector store
            try:
                rag_system.initialize_system(force_rebuild=True)
                flash('Vector store rebuilt successfully with new documents', 'success')
            except Exception as e:
                logger.error(f"Failed to rebuild vector store: {e}")
                flash(f'Uploaded files but failed to rebuild vector store: {str(e)}', 'warning')
        else:
            message = "No valid files uploaded"
        
        return render_template('upload.html', message=message, uploaded_files=uploaded_files)
    
    return render_template('upload.html')

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html', user=current_user)

@app.route('/health')
def health():
    """Health check endpoint."""
    vector_store_status = hasattr(rag_system, 'rag_chain') and rag_system.rag_chain is not None
    return jsonify({
        'status': 'healthy',
        'vector_store_loaded': vector_store_status,
        'model': config.LLM_MODEL,
        'data_dir': config.DATA_DIR,
        'vector_store_dir': config.VECTOR_STORE_DIR,
        'authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False
    })

# API Routes with Authentication

@app.route('/api/ask', methods=['POST'])
@require_api_key
def api_ask():
    """API endpoint to ask a question."""
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'Question is required'}), 400
        
        question = data['question']
        if not isinstance(question, str) or len(question.strip()) < 3:
            return jsonify({'error': 'Question must be a non-empty string with at least 3 characters'}), 400
        
        # Initialize RAG system if needed
        if not initialize_rag_system():
            return jsonify({'error': 'RAG system not initialized'}), 500
        
        answer = rag_system.rag_chain.query(question)
        return jsonify({'question': question, 'answer': answer})
    
    except Exception as e:
        logger.error(f"API error processing question: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
@require_api_key
def api_list_documents():
    """API endpoint to list documents."""
    try:
        documents = []
        if os.path.exists(config.DATA_DIR):
            documents = [f for f in os.listdir(config.DATA_DIR) if f.lower().endswith('.pdf')]
        return jsonify({'documents': documents})
    except Exception as e:
        logger.error(f"API error listing documents: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rebuild', methods=['POST'])
@require_api_key
@require_admin
def api_rebuild():
    """API endpoint to rebuild vector store (admin only)."""
    try:
        rag_system.initialize_system(force_rebuild=True)
        return jsonify({'status': 'success', 'message': 'Vector store rebuilt successfully'})
    except Exception as e:
        logger.error(f"API error rebuilding vector store: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@require_api_key
def api_upload():
    """API endpoint to upload documents."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400
        
        filepath = os.path.join(config.DATA_DIR, file.filename)
        file.save(filepath)
        logger.info(f"API uploaded file: {file.filename}")
        
        return jsonify({'status': 'success', 'filename': file.filename})
    except Exception as e:
        logger.error(f"API error uploading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/me', methods=['GET'])
@require_api_key
def api_user_profile():
    """API endpoint to get current user profile."""
    user = getattr(request, 'current_user', None)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict())

@app.route('/api/users/me/apikey', methods=['POST'])
@require_api_key
def api_regenerate_api_key():
    """API endpoint to regenerate API key."""
    user = getattr(request, 'current_user', None)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        user.generate_api_key()
        db.session.commit()
        return jsonify({'api_key': user.api_key})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error regenerating API key: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize RAG system on startup
    try:
        logger.info("Initializing RAG system on startup...")
        rag_system.initialize_system()
        logger.info("RAG system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG system on startup: {e}")
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=app.config['FLASK_DEBUG']
    )
