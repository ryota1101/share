"""
Database configuration and initialization
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import logging

db = SQLAlchemy()

def init_db():
    """Initialize database and create tables"""
    logger = logging.getLogger(__name__)
    
    try:
        # Create all tables
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Check if we can connect
        result = db.session.execute(text('SELECT 1'))
        logger.info("Database connection verified")
        
        # Check if tables exist and have data
        from models.chat_models import ChatSession, ChatMessage
        
        session_count = db.session.query(ChatSession).count()
        message_count = db.session.query(ChatMessage).count()
        
        logger.info(f"Current database state: {session_count} sessions, {message_count} messages")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise e