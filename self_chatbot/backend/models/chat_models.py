"""
SQLAlchemy models for chat functionality
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.database import db

class ChatSession(db.Model):
    """Chat session model"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(255), nullable=False, default='New Chat')
    model_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_favorite = db.Column(db.Boolean, default=False)
    
    # Relationship to messages
    messages = relationship('ChatMessage', back_populates='session', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'session_name': self.session_name,
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_favorite': self.is_favorite,
            'message_count': len(self.messages) if self.messages else 0
        }
    
    def to_dict_with_messages(self):
        """Convert model to dictionary including messages"""
        data = self.to_dict()
        data['messages'] = [msg.to_dict() for msg in self.messages] if self.messages else []
        return data

class ChatMessage(db.Model):
    """Chat message model"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    image_data = db.Column(db.Text)  # Base64 encoded image data
    image_type = db.Column(db.String(50))  # image/png, image/jpeg, etc.
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    model_name = db.Column(db.String(100))
    
    # Relationship to session
    session = relationship('ChatSession', back_populates='messages')
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'message_type': self.message_type,
            'content': self.content,
            'image_data': self.image_data,
            'image_type': self.image_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'model_name': self.model_name
        }
    
    @classmethod
    def create_user_message(cls, session_id, content, image_data=None, image_type=None):
        """Create a user message"""
        return cls(
            session_id=session_id,
            message_type='user',
            content=content,
            image_data=image_data,
            image_type=image_type
        )
    
    @classmethod
    def create_assistant_message(cls, session_id, content, model_name, image_data=None, image_type=None):
        """Create an assistant message"""
        return cls(
            session_id=session_id,
            message_type='assistant',
            content=content,
            model_name=model_name,
            image_data=image_data,
            image_type=image_type
        )