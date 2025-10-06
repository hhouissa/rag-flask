# auth.py
from flask import request, jsonify, current_app
from flask_login import login_user, logout_user, current_user
from functools import wraps
from models import User, db
import jwt
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def require_api_key(f):
    """Decorator to require API key for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = None
        
        # Check for API key in header
        if 'X-API-Key' in request.headers:
            api_key = request.headers['X-API-Key']
        # Check for API key in query parameters
        elif 'api_key' in request.args:
            api_key = request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        
        # Verify API key
        user = User.query.filter_by(api_key=api_key, is_active=True).first()
        if not user:
            return jsonify({'error': 'Invalid or expired API key'}), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def require_auth(f):
    """Decorator to require user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated_function

def generate_token(user_id):
    """Generate JWT token for user."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def register_user(username, email, password, role='user'):
    """Register a new user."""
    try:
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return None, 'Username already exists'
        
        if User.query.filter_by(email=email).first():
            return None, 'Email already exists'
        
        # Create new user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        user.generate_api_key()
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User registered: {username}")
        return user, None
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering user {username}: {e}")
        return None, str(e)

def authenticate_user(username, password):
    """Authenticate user with username and password."""
    try:
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            return user
        return None
    except Exception as e:
        logger.error(f"Error authenticating user {username}: {e}")
        return None
