"""
Chat API routes for Multi-LLM Chat
"""

import json
import base64
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from models.database import db
from models.chat_models import ChatSession, ChatMessage
from utils.llm_client import LLMClient
from utils.image_utils import process_image
import time

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint
    Handles text and image inputs, returns streaming or non-streaming responses
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'message' not in data or 'model' not in data:
            return jsonify({'error': 'Missing required fields: message, model'}), 400
        
        message = data['message']
        model_name = data['model']
        session_id = data.get('session_id')
        image_data = data.get('image_data')  # Base64 encoded image
        streaming = data.get('streaming', True)
        
        logger.info(f"Chat request - Model: {model_name}, Session: {session_id}, Streaming: {streaming}")
        
        # Get or create session
        if session_id:
            session = ChatSession.query.get(session_id)
            if not session:
                return jsonify({'error': 'Session not found'}), 404
        else:
            # Create new session
            session = ChatSession(
                session_name=f"Chat with {model_name}",
                model_name=model_name
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            logger.info(f"Created new session: {session_id}")
        
        # Process image if provided
        processed_image = None
        if image_data:
            try:
                processed_image = process_image(image_data)
                logger.info("Image processed successfully")
            except Exception as e:
                logger.error(f"Image processing failed: {e}")
                return jsonify({'error': 'Invalid image data'}), 400
        
        # Save user message
        user_message = ChatMessage.create_user_message(
            session_id=session_id,
            content=message,
            image_data=image_data if image_data else None,
            image_type=processed_image.get('type') if processed_image else None
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Get LLM client and generate response
        llm_client = LLMClient()
        
        if streaming:
            return Response(
                stream_with_context(
                    generate_streaming_response(
                        llm_client, model_name, message, session_id, processed_image
                    )
                ),
                content_type='text/plain; charset=utf-8'
            )
        else:
            # Non-streaming response (for testing/fallback)
            response_text = llm_client.generate_response(
                model_name=model_name,
                message=message,
                image_data=processed_image
            )
            
            # Save assistant response
            assistant_message = ChatMessage.create_assistant_message(
                session_id=session_id,
                content=response_text,
                model_name=model_name
            )
            db.session.add(assistant_message)
            db.session.commit()
            
            return jsonify({
                'response': response_text,
                'session_id': session_id,
                'model': model_name
            })
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def generate_streaming_response(llm_client, model_name, message, session_id, image_data=None):
    """
    Generator for streaming chat responses
    """
    try:
        response_chunks = []
        
        # Generate streaming response from LLM
        for chunk in llm_client.generate_streaming_response(
            model_name=model_name,
            message=message,
            image_data=image_data
        ):
            response_chunks.append(chunk)
            
            # Format as JSON for frontend
            chunk_data = {
                'type': 'chunk',
                'content': chunk,
                'session_id': session_id,
                'model': model_name
            }
            yield f"data: {json.dumps(chunk_data)}\n\n"
        
        # Save complete response to database
        full_response = ''.join(response_chunks)
        if full_response.strip():  # Only save non-empty responses
            assistant_message = ChatMessage.create_assistant_message(
                session_id=session_id,
                content=full_response,
                model_name=model_name
            )
            db.session.add(assistant_message)
            db.session.commit()
        
        # Send completion signal
        completion_data = {
            'type': 'complete',
            'session_id': session_id,
            'model': model_name,
            'message_id': assistant_message.id if 'assistant_message' in locals() else None
        }
        yield f"data: {json.dumps(completion_data)}\n\n"
        
    except Exception as e:
        logger.error(f"Streaming response error: {e}", exc_info=True)
        error_data = {
            'type': 'error',
            'error': str(e),
            'session_id': session_id
        }
        yield f"data: {json.dumps(error_data)}\n\n"

@chat_bp.route('/chat/upload-image', methods=['POST'])
def upload_image():
    """
    Upload and process image for chat
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # Read and encode image
        image_data = file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Process image
        processed = process_image(base64_image)
        
        return jsonify({
            'image_data': base64_image,
            'image_type': processed['type'],
            'size': processed['size']
        })
    
    except Exception as e:
        logger.error(f"Image upload error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/chat/test', methods=['POST'])
def test_chat():
    """
    Test endpoint with dummy response (for development)
    """
    try:
        data = request.get_json()
        message = data.get('message', 'Hello')
        model_name = data.get('model', 'test-model')
        
        # Simulate processing time
        time.sleep(1)
        
        dummy_response = f"This is a test response from {model_name} for message: '{message}'"
        
        return jsonify({
            'response': dummy_response,
            'model': model_name,
            'timestamp': time.time()
        })
    
    except Exception as e:
        logger.error(f"Test chat error: {e}")
        return jsonify({'error': str(e)}), 500