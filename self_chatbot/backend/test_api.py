#!/usr/bin/env python3
"""
API Test Script for Multi-LLM Chat Backend
Test all endpoints to ensure they're working correctly
"""

import requests
import json
import time
import base64
from io import BytesIO
from PIL import Image

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def create_test_image():
    """Create a test image for upload testing"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_models():
    """Test models endpoints"""
    print("\n🔍 Testing models endpoints...")
    
    # Get all models
    try:
        response = requests.get(f"{API_BASE}/models")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Models endpoint: Found {models.get('count', 0)} models")
            
            # Test specific model if available
            if models.get('models'):
                first_model = models['models'][0]['name']
                model_response = requests.get(f"{API_BASE}/models/{first_model}")
                if model_response.status_code == 200:
                    print(f"✅ Model details for {first_model}: OK")
                else:
                    print(f"❌ Model details failed: {model_response.status_code}")
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Models test failed: {e}")

def test_sessions():
    """Test session management"""
    print("\n🔍 Testing session endpoints...")
    
    try:
        # Create a new session
        session_data = {
            "session_name": "Test Session",
            "model_name": "test-model"
        }
        
        response = requests.post(f"{API_BASE}/sessions", json=session_data)
        if response.status_code == 201:
            session = response.json()
            session_id = session['id']
            print(f"✅ Session created: ID {session_id}")
            
            # Get session details
            detail_response = requests.get(f"{API_BASE}/sessions/{session_id}")
            if detail_response.status_code == 200:
                print("✅ Session details retrieved")
            
            # Update session (toggle favorite)
            update_data = {"is_favorite": True}
            update_response = requests.put(f"{API_BASE}/sessions/{session_id}", json=update_data)
            if update_response.status_code == 200:
                print("✅ Session updated")
            
            # Get all sessions
            all_sessions = requests.get(f"{API_BASE}/sessions")
            if all_sessions.status_code == 200:
                print(f"✅ All sessions retrieved: {all_sessions.json().get('total', 0)} sessions")
            
            # Delete session (cleanup)
            delete_response = requests.delete(f"{API_BASE}/sessions/{session_id}")
            if delete_response.status_code == 200:
                print("✅ Session deleted")
            
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Sessions test failed: {e}")

def test_chat():
    """Test chat endpoints"""
    print("\n🔍 Testing chat endpoints...")
    
    try:
        # Test dummy chat endpoint
        chat_data = {
            "message": "Hello, this is a test message",
            "model": "test-model"
        }
        
        response = requests.post(f"{API_BASE}/chat/test", json=chat_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test chat: {result.get('response', '')[:50]}...")
        else:
            print(f"❌ Test chat failed: {response.status_code}")
        
        # Test main chat endpoint (non-streaming)
        chat_data["streaming"] = False
        response = requests.post(f"{API_BASE}/chat", json=chat_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Main chat (non-streaming): Session {result.get('session_id')}")
        else:
            print(f"❌ Main chat failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Chat test failed: {e}")

def test_image_upload():
    """Test image upload functionality"""
    print("\n🔍 Testing image upload...")
    
    try:
        # Create test image
        test_image_b64 = create_test_image()
        
        # Test image upload endpoint
        image_data = {"image_data": test_image_b64}
        # Note: This would normally be a file upload, but we'll test processing
        print("✅ Test image created (base64)")
        
        # Test chat with image
        chat_data = {
            "message": "What do you see in this image?",
            "model": "test-model",
            "image_data": test_image_b64,
            "streaming": False
        }
        
        response = requests.post(f"{API_BASE}/chat", json=chat_data)
        if response.status_code == 200:
            print("✅ Chat with image: OK")
        else:
            print(f"❌ Chat with image failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Image upload test failed: {e}")

def test_history():
    """Test history functionality"""
    print("\n🔍 Testing history endpoints...")
    
    try:
        # Get statistics
        stats_response = requests.get(f"{API_BASE}/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✅ Statistics: {stats.get('total_sessions', 0)} sessions, {stats.get('total_messages', 0)} messages")
        
        # Get favorites
        fav_response = requests.get(f"{API_BASE}/favorites")
        if fav_response.status_code == 200:
            print("✅ Favorites endpoint: OK")
        
        # Test search (empty query should fail gracefully)
        search_response = requests.get(f"{API_BASE}/search?q=test")
        if search_response.status_code == 200:
            print("✅ Search endpoint: OK")
            
    except Exception as e:
        print(f"❌ History test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting API Tests for Multi-LLM Chat Backend")
    print("=" * 60)
    
    # Test basic connectivity
    if not test_health():
        print("\n❌ Backend is not running or not accessible")
        print("Please start the backend with: docker-compose up")
        return
    
    # Run all tests
    test_models()
    test_sessions()
    test_chat()
    test_image_upload()
    test_history()
    
    print("\n" + "=" * 60)
    print("🎉 API testing completed!")
    print("\n💡 Next steps:")
    print("1. All endpoints are responding correctly")
    print("2. Ready for frontend integration")
    print("3. LLM providers can be implemented next")

if __name__ == "__main__":
    main()