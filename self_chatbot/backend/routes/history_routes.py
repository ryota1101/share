"""
History API routes for Multi-LLM Chat
Handles chat session and message history management
"""

import logging
from flask import Blueprint, request, jsonify
from sqlalchemy import desc, asc
from models.database import db
from models.chat_models import ChatSession, ChatMessage
from datetime import datetime

history_bp = Blueprint('history', __name__)
logger = logging.getLogger(__name__)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@history_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """
    Get all chat sessions with optional filtering
    Query params:
    - favorite: true/false (filter favorites)
    - limit: number of sessions to return
    - offset: pagination offset
    """
    try:
        # Parse query parameters
        favorite_filter = request.args.get('favorite')
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)
        
        # Build query
        query = ChatSession.query
        
        if favorite_filter is not None:
            is_favorite = favorite_filter.lower() == 'true'
            query = query.filter(ChatSession.is_favorite == is_favorite)
        
        # Order by updated_at (most recent first)
        query = query.order_by(desc(ChatSession.updated_at))
        
        # Apply pagination
        sessions = query.offset(offset).limit(limit).all()
        total_count = query.count()
        
        return jsonify({
            'sessions': [session.to_dict() for session in sessions],
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
    
    except Exception as e:
        logger.error(f"Get sessions error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@history_bp.route('/sessions', methods=['POST'])
def create_session():
    """
    Create a new chat session
    """
    try:
        data = request.get_json()
        
        session_name = data.get('session_name', 'New Chat')
        model_name = data.get('model_name', 'gpt-3.5-turbo')
        
        session = ChatSession(
            session_name=session_name,
            model_name=model_name
        )
        
        db.session.add(session)
        db.session.commit()
        
        logger.info(f"Created new session: {session.id}")
        
        return jsonify(session.to_dict()), 201
    
    except Exception as e:
        logger.error(f"Create session error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@history_bp.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """
    Get a specific session with all its messages
    """
    try:
        session = ChatSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify(session.to_dict_with_messages())
    
    except Exception as e:
        logger.error(f"Get session error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@history_bp.route('/sessions/<int:session_id>', methods=['PUT'])
def update_session(session_id):
    """
    Update session details (name, favorite status)
    """
    try:
        session = ChatSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        data = request.get_json()
        
        if 'session_name' in data:
            session.session_name = data['session_name']
        
        if 'is_favorite' in data:
            session.is_favorite = data['is_favorite']
        
        session.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Updated session: {session_id}")
        
        return jsonify(session.to_dict())
    
    except Exception as e:
        logger.error(f"Update session error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@history_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Delete a chat session and all its messages
    """
    try:
        session = ChatSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        db.session.delete(session)
        db.session.commit()
        
        logger.info(f"Deleted session: {session_id}")
        
        return jsonify({'message': 'Session deleted successfully'})
    
    except Exception as e:
        logger.error(f"Delete session error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MESSAGE MANAGEMENT
# ============================================================================

@history_bp.route('/sessions/<int:session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    """
    Get all messages for a specific session
    """
    try:
        # Check if session exists
        session = ChatSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get messages ordered by created_at
        messages = ChatMessage.query.filter_by(session_id=session_id)\
                                   .order_by(asc(ChatMessage.created_at))\
                                   .all()
        
        return jsonify({
            'session_id': session_id,
            'messages': [message.to_dict() for message in messages]
        })
    
    except Exception as e:
        logger.error(f"Get session messages error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@history_bp.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """
    Delete a specific message
    """
    try:
        message = ChatMessage.query.get(message_id)
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        session_id = message.session_id
        db.session.delete(message)
        db.session.commit()
        
        logger.info(f"Deleted message: {message_id} from session: {session_id}")
        
        return jsonify({'message': 'Message deleted successfully'})
    
    except Exception as e:
        logger.error(f"Delete message error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# FAVORITE MANAGEMENT
# ============================================================================

@history_bp.route('/sessions/<int:session_id>/favorite', methods=['POST'])
def toggle_favorite(session_id):
    """
    Toggle favorite status of a session
    """
    try:
        session = ChatSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.is_favorite = not session.is_favorite
        session.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Toggled favorite for session {session_id}: {session.is_favorite}")
        
        return jsonify({
            'session_id': session_id,
            'is_favorite': session.is_favorite
        })
    
    except Exception as e:
        logger.error(f"Toggle favorite error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@history_bp.route('/favorites', methods=['GET'])
def get_favorites():
    """
    Get all favorite sessions
    """
    try:
        favorite_sessions = ChatSession.query\
                                      .filter(ChatSession.is_favorite == True)\
                                      .order_by(desc(ChatSession.updated_at))\
                                      .all()
        
        return jsonify({
            'favorites': [session.to_dict() for session in favorite_sessions]
        })
    
    except Exception as e:
        logger.error(f"Get favorites error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SEARCH AND STATISTICS
# ============================================================================

@history_bp.route('/search', methods=['GET'])
def search_history():
    """
    Search through chat history
    Query params:
    - q: search query
    - model: filter by model name
    - limit: number of results
    """
    try:
        query_text = request.args.get('q', '').strip()
        model_filter = request.args.get('model')
        limit = request.args.get('limit', type=int, default=20)
        
        if not query_text:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Search in messages
        search_query = ChatMessage.query.filter(
            ChatMessage.content.ilike(f'%{query_text}%')
        )
        
        if model_filter:
            search_query = search_query.filter(ChatMessage.model_name == model_filter)
        
        messages = search_query.order_by(desc(ChatMessage.created_at))\
                              .limit(limit)\
                              .all()
        
        # Get associated session info
        results = []
        for message in messages:
            result = message.to_dict()
            result['session'] = message.session.to_dict()
            results.append(result)
        
        return jsonify({
            'query': query_text,
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@history_bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    Get chat history statistics
    """
    try:
        total_sessions = ChatSession.query.count()
        total_messages = ChatMessage.query.count()
        favorite_sessions = ChatSession.query.filter(ChatSession.is_favorite == True).count()
        
        # Get model usage stats
        model_stats = db.session.query(
            ChatMessage.model_name,
            db.func.count(ChatMessage.id).label('count')
        ).filter(
            ChatMessage.model_name.isnot(None)
        ).group_by(ChatMessage.model_name).all()
        
        model_usage = {model: count for model, count in model_stats}
        
        return jsonify({
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'favorite_sessions': favorite_sessions,
            'model_usage': model_usage
        })
    
    except Exception as e:
        logger.error(f"Get statistics error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500