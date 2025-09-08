"""
Model API routes for Multi-LLM Chat
Handles AI model information and configuration
"""

import logging
from flask import Blueprint, jsonify
from utils.config_loader import ConfigLoader

model_bp = Blueprint('models', __name__)
logger = logging.getLogger(__name__)

@model_bp.route('/models', methods=['GET'])
def get_models():
    """
    Get all available AI models from configuration
    """
    try:
        config_loader = ConfigLoader()
        models = config_loader.get_models()
        
        if not models:
            logger.warning("No models found in configuration")
            return jsonify({
                'models': [],
                'message': 'No models configured'
            })
        
        # Format models for frontend
        formatted_models = []
        for model in models:
            formatted_model = {
                'name': model.get('name'),
                'display_name': model.get('display_name'),
                'provider': model.get('provider'),
                'capabilities': model.get('capabilities', {}),
                'description': model.get('description', ''),
                'settings': model.get('settings', {})
            }
            formatted_models.append(formatted_model)
        
        logger.info(f"Retrieved {len(formatted_models)} models")
        
        return jsonify({
            'models': formatted_models,
            'count': len(formatted_models)
        })
    
    except Exception as e:
        logger.error(f"Get models error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_bp.route('/models/<string:model_name>', methods=['GET'])
def get_model_details(model_name):
    """
    Get details for a specific model
    """
    try:
        config_loader = ConfigLoader()
        model = config_loader.get_model(model_name)
        
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        return jsonify(model)
    
    except Exception as e:
        logger.error(f"Get model details error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_bp.route('/models/providers', methods=['GET'])
def get_providers():
    """
    Get all configured providers
    """
    try:
        config_loader = ConfigLoader()
        providers = config_loader.get_providers()
        
        return jsonify({
            'providers': providers
        })
    
    except Exception as e:
        logger.error(f"Get providers error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_bp.route('/models/capabilities', methods=['GET'])
def get_model_capabilities():
    """
    Get capabilities summary for all models
    """
    try:
        config_loader = ConfigLoader()
        models = config_loader.get_models()
        
        capabilities_summary = {
            'text_input': [],
            'image_input': [],
            'image_output': [],
            'streaming': []
        }
        
        for model in models:
            model_name = model.get('name')
            capabilities = model.get('capabilities', {})
            
            for capability, supported in capabilities.items():
                if supported and capability in capabilities_summary:
                    capabilities_summary[capability].append({
                        'name': model_name,
                        'display_name': model.get('display_name'),
                        'provider': model.get('provider')
                    })
        
        return jsonify(capabilities_summary)
    
    except Exception as e:
        logger.error(f"Get capabilities error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@model_bp.route('/models/test/<string:model_name>', methods=['POST'])
def test_model(model_name):
    """
    Test if a model is available and working
    """
    try:
        config_loader = ConfigLoader()
        model = config_loader.get_model(model_name)
        
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        # For now, just return model configuration
        # TODO: Implement actual model testing when LLM clients are ready
        return jsonify({
            'model_name': model_name,
            'status': 'available',
            'configuration': model,
            'message': 'Model configuration is valid (actual testing not implemented yet)'
        })
    
    except Exception as e:
        logger.error(f"Test model error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500