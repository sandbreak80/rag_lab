"""
User Models for Authentication Service
Fast Track Phase 7 - Week 9 Day 1-3
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import bcrypt
import os

Base = declarative_base()


class User(Base):
    """
    User model for authentication

    Fields:
    - id: Unique user ID
    - username: Unique username
    - email: Unique email address
    - password_hash: bcrypt hashed password
    - is_active: Account active status
    - is_admin: Admin privileges
    - created_at: Account creation timestamp
    - last_login: Last login timestamp
    - api_key: Optional API key for programmatic access
    """

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # API key for programmatic access
    api_key = Column(String(64), unique=True, nullable=True, index=True)

    def __repr__(self):
        return f'<User {self.username} ({self.email})>'

    def set_password(self, password: str):
        """Hash and set user password"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary (for JSON responses)"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        if include_sensitive and self.api_key:
            data['api_key'] = self.api_key

        return data


class RefreshToken(Base):
    """
    Refresh tokens for extended sessions

    Fields:
    - id: Token ID
    - user_id: Associated user
    - token: Refresh token string
    - expires_at: Token expiration
    - revoked: Token revocation status
    """

    __tablename__ = 'refresh_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<RefreshToken user_id={self.user_id} revoked={self.revoked}>'

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return not self.revoked and self.expires_at > datetime.utcnow()


# Database connection setup
def get_database_url():
    """Get database URL from environment or use default SQLite"""
    db_url = os.getenv('DATABASE_URL')

    if db_url:
        return db_url

    # Default: SQLite in /data directory
    db_path = os.getenv('DB_PATH', '/data/auth.db')
    return f'sqlite:///{db_path}'


def init_database():
    """Initialize database and create tables"""
    db_url = get_database_url()
    print(f"📦 Initializing database: {db_url}")

    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)

    print("✅ Database tables created successfully")

    return engine


def get_db_session():
    """Get database session"""
    db_url = get_database_url()
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing User Model")
    print("=" * 60)

    # Initialize database
    engine = init_database()
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test user
    test_user = User(
        username="testuser",
        email="test@example.com"
    )
    test_user.set_password("SecurePassword123!")

    # Add to database
    session.add(test_user)
    session.commit()

    print(f"✅ Created user: {test_user}")

    # Test password verification
    assert test_user.check_password("SecurePassword123!"), "Password should match"
    assert not test_user.check_password("WrongPassword"), "Wrong password should not match"

    print("✅ Password verification works")

    # Test to_dict
    user_dict = test_user.to_dict()
    print(f"✅ User dict: {user_dict}")

    # Cleanup
    session.query(User).delete()
    session.commit()
    session.close()

    print("\n✅ All tests passed!")

