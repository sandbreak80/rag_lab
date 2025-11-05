#!/usr/bin/env python3
"""
Authentication Service - User Management & JWT Tokens
Fast Track Phase 7 - Week 9 Day 1-3

Features:
- User registration and login
- JWT token generation and validation
- Password hashing with bcrypt
- Refresh tokens
- API key support
- Role-based access control
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
import os
import sys
import secrets

# Add common to path
sys.path.insert(0, '/workspace')
from services.common.config import *
from services.common.metrics import ServiceMetrics, timed
from services.common.health import HealthCheck

# Import models
from models import User, RefreshToken, init_database, get_db_session

app = Flask(__name__)
CORS(app)

# Configuration
SERVICE_NAME = os.getenv('SERVICE_NAME', 'auth-service')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8014))

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

jwt = JWTManager(app)

# Initialize metrics and health checks
metrics = ServiceMetrics(SERVICE_NAME)
health = HealthCheck(SERVICE_NAME)

# Initialize database
print("📦 Initializing authentication service...")
engine = init_database()
print("✅ Database ready")

# ============================================================
# Health & Info Endpoints
# ============================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        session = get_db_session()
        user_count = session.query(User).count()
        session.close()

        return jsonify({
            'status': 'healthy',
            'service': SERVICE_NAME,
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'user_count': user_count
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': SERVICE_NAME,
            'error': str(e)
        }), 500

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get service metrics"""
    return jsonify(metrics.get_stats())

@app.route('/')
def root():
    """Service info"""
    return jsonify({
        'service': 'Authentication Service',
        'version': '1.0.0',
        'status': 'operational',
        'features': [
            'User Registration',
            'JWT Authentication',
            'Password Hashing (bcrypt)',
            'Refresh Tokens',
            'API Keys',
            'Role-Based Access Control'
        ],
        'endpoints': {
            'health': '/health',
            'metrics': '/metrics',
            'register': '/register',
            'login': '/login',
            'refresh': '/refresh',
            'validate': '/validate',
            'profile': '/profile',
            'change_password': '/change_password',
            'users': '/users (admin only)'
        }
    })

# ============================================================
# Authentication Endpoints
# ============================================================

@app.route('/register', methods=['POST'])
@timed(metrics, 'register')
def register():
    """
    Register a new user

    Request:
    {
        "username": "johndoe",
        "email": "john@example.com",
        "password": "SecurePassword123!"
    }

    Response:
    {
        "success": true,
        "user": {...},
        "message": "User registered successfully"
    }
    """
    try:
        data = request.json

        # Validate input
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not username or len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400

        if not email or '@' not in email:
            return jsonify({'error': 'Invalid email address'}), 400

        if not password or len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        # Check if user already exists
        session = get_db_session()

        if session.query(User).filter_by(username=username).first():
            session.close()
            return jsonify({'error': 'Username already exists'}), 409

        if session.query(User).filter_by(email=email).first():
            session.close()
            return jsonify({'error': 'Email already registered'}), 409

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)

        # First user is admin
        user_count = session.query(User).count()
        if user_count == 0:
            user.is_admin = True
            print(f"✨ First user '{username}' created as admin")

        session.add(user)
        session.commit()

        user_dict = user.to_dict()
        session.close()

        metrics.increment('user_registrations')

        return jsonify({
            'success': True,
            'user': user_dict,
            'message': 'User registered successfully'
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
@timed(metrics, 'login')
def login():
    """
    Login and get JWT tokens

    Request:
    {
        "username": "johndoe",  # or "email": "john@example.com"
        "password": "SecurePassword123!"
    }

    Response:
    {
        "success": true,
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "user": {...}
    }
    """
    try:
        data = request.json

        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not password:
            return jsonify({'error': 'Password required'}), 400

        if not username and not email:
            return jsonify({'error': 'Username or email required'}), 400

        # Find user
        session = get_db_session()

        if username:
            user = session.query(User).filter_by(username=username).first()
        else:
            user = session.query(User).filter_by(email=email).first()

        if not user:
            session.close()
            metrics.increment('login_failures')
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.check_password(password):
            session.close()
            metrics.increment('login_failures')
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            session.close()
            return jsonify({'error': 'Account is disabled'}), 403

        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()

        # Create JWT tokens
        identity = {
            'user_id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }

        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)

        # Store refresh token in database
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        session.add(refresh_token_obj)
        session.commit()

        user_dict = user.to_dict()
        session.close()

        metrics.increment('login_success')

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_dict
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@timed(metrics, 'refresh_token')
def refresh():
    """
    Refresh access token using refresh token

    Headers:
    Authorization: Bearer <refresh_token>

    Response:
    {
        "access_token": "eyJ..."
    }
    """
    try:
        identity = get_jwt_identity()

        # Create new access token
        access_token = create_access_token(identity=identity)

        metrics.increment('token_refreshes')

        return jsonify({
            'access_token': access_token
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/validate', methods=['POST'])
@jwt_required()
@timed(metrics, 'validate_token')
def validate():
    """
    Validate JWT token and get user info

    Headers:
    Authorization: Bearer <access_token>

    Response:
    {
        "valid": true,
        "user_id": 1,
        "username": "johndoe",
        "is_admin": false
    }
    """
    try:
        identity = get_jwt_identity()

        metrics.increment('token_validations')

        return jsonify({
            'valid': True,
            **identity
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 401

# ============================================================
# User Profile Endpoints
# ============================================================

@app.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile"""
    try:
        identity = get_jwt_identity()
        user_id = identity['user_id']

        session = get_db_session()
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            session.close()
            return jsonify({'error': 'User not found'}), 404

        user_dict = user.to_dict()
        session.close()

        return jsonify({'user': user_dict})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile"""
    try:
        identity = get_jwt_identity()
        user_id = identity['user_id']
        data = request.json

        session = get_db_session()
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            session.close()
            return jsonify({'error': 'User not found'}), 404

        # Update allowed fields
        if 'email' in data:
            email = data['email'].strip().lower()
            if email != user.email:
                # Check if email already exists
                if session.query(User).filter_by(email=email).first():
                    session.close()
                    return jsonify({'error': 'Email already in use'}), 409
                user.email = email

        session.commit()
        user_dict = user.to_dict()
        session.close()

        return jsonify({
            'success': True,
            'user': user_dict
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/change_password', methods=['POST'])
@jwt_required()
def change_password():
    """Change current user's password"""
    try:
        identity = get_jwt_identity()
        user_id = identity['user_id']
        data = request.json

        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')

        if not old_password or not new_password:
            return jsonify({'error': 'Old and new passwords required'}), 400

        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400

        session = get_db_session()
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            session.close()
            return jsonify({'error': 'User not found'}), 404

        # Verify old password
        if not user.check_password(old_password):
            session.close()
            return jsonify({'error': 'Invalid old password'}), 401

        # Set new password
        user.set_password(new_password)
        session.commit()
        session.close()

        metrics.increment('password_changes')

        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# Admin Endpoints
# ============================================================

@app.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """List all users (admin only)"""
    try:
        identity = get_jwt_identity()

        if not identity.get('is_admin', False):
            return jsonify({'error': 'Admin access required'}), 403

        session = get_db_session()
        users = session.query(User).all()

        users_list = [user.to_dict() for user in users]
        session.close()

        return jsonify({
            'users': users_list,
            'count': len(users_list)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# Error Handlers
# ============================================================

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token"""
    return jsonify({
        'error': 'Token has expired',
        'message': 'Please login again or use refresh token'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid token"""
    return jsonify({
        'error': 'Invalid token',
        'message': 'Please provide a valid token'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """Handle missing token"""
    return jsonify({
        'error': 'Authorization required',
        'message': 'Please provide an access token'
    }), 401

# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print(f"🔐 Starting {SERVICE_NAME} on port {SERVICE_PORT}...")
    print(f"📊 Metrics available at http://localhost:{SERVICE_PORT}/metrics")
    print(f"💚 Health check at http://localhost:{SERVICE_PORT}/health")

    app.run(
        host='0.0.0.0',
        port=SERVICE_PORT,
        debug=False
    )

