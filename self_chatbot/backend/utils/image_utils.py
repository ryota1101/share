"""
Image processing utilities for Multi-LLM Chat
Handle image uploads, validation, and processing for AI models
"""

import base64
import io
import logging
from PIL import Image
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_FORMATS = {'PNG', 'JPEG', 'JPG', 'GIF', 'WEBP'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSIONS = (4096, 4096)  # Max width/height

def process_image(base64_data: str) -> Dict[str, any]:
    """
    Process base64 encoded image data
    
    Args:
        base64_data: Base64 encoded image string
    
    Returns:
        Dict containing processed image info
    """
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            header, base64_data = base64_data.split(',', 1)
        
        # Decode base64 data
        try:
            image_bytes = base64.b64decode(base64_data)
        except Exception as e:
            raise ValueError(f"Invalid base64 data: {e}")
        
        # Check file size
        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise ValueError(f"Image too large: {len(image_bytes)} bytes (max: {MAX_IMAGE_SIZE})")
        
        # Load image with PIL
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.load()  # Verify image integrity
        except Exception as e:
            raise ValueError(f"Invalid image data: {e}")
        
        # Get image info
        format = image.format.upper() if image.format else 'UNKNOWN'
        width, height = image.size
        
        # Validate format
        if format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported image format: {format}. Supported: {', '.join(SUPPORTED_FORMATS)}")
        
        # Check dimensions
        if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
            logger.info(f"Resizing large image: {width}x{height} -> {MAX_DIMENSIONS}")
            image = resize_image(image, MAX_DIMENSIONS)
            width, height = image.size
            
            # Re-encode to base64 after resizing
            buffer = io.BytesIO()
            image.save(buffer, format=format)
            base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Determine MIME type
        mime_type = get_mime_type(format)
        
        result = {
            'type': mime_type,
            'format': format,
            'width': width,
            'height': height,
            'size': len(base64.b64decode(base64_data)),
            'base64': base64_data,
            'processed': True
        }
        
        logger.info(f"Processed image: {format} {width}x{height} ({result['size']} bytes)")
        
        return result
    
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise e

def resize_image(image: Image.Image, max_dimensions: Tuple[int, int]) -> Image.Image:
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: PIL Image object
        max_dimensions: (max_width, max_height)
    
    Returns:
        Resized PIL Image object
    """
    max_width, max_height = max_dimensions
    width, height = image.size
    
    # Calculate aspect ratio
    aspect_ratio = width / height
    
    # Calculate new dimensions
    if width > height:
        new_width = min(max_width, width)
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(max_height, height)
        new_width = int(new_height * aspect_ratio)
    
    # Ensure we don't exceed maximum dimensions
    if new_width > max_width:
        new_width = max_width
        new_height = int(new_width / aspect_ratio)
    
    if new_height > max_height:
        new_height = max_height
        new_width = int(new_height * aspect_ratio)
    
    # Resize image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
    
    return resized_image

def get_mime_type(format: str) -> str:
    """
    Get MIME type for image format
    
    Args:
        format: Image format (PNG, JPEG, etc.)
    
    Returns:
        MIME type string
    """
    mime_types = {
        'PNG': 'image/png',
        'JPEG': 'image/jpeg',
        'JPG': 'image/jpeg',
        'GIF': 'image/gif',
        'WEBP': 'image/webp'
    }
    
    return mime_types.get(format.upper(), 'image/unknown')

def validate_image_data(base64_data: str) -> Tuple[bool, str]:
    """
    Validate base64 image data without full processing
    
    Args:
        base64_data: Base64 encoded image string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Basic base64 validation
        if not base64_data:
            return False, "Empty image data"
        
        # Remove data URL prefix if present
        if ',' in base64_data:
            header, base64_data = base64_data.split(',', 1)
        
        # Try to decode
        image_bytes = base64.b64decode(base64_data, validate=True)
        
        # Check size
        if len(image_bytes) > MAX_IMAGE_SIZE:
            return False, f"Image too large: {len(image_bytes)} bytes"
        
        # Try to load with PIL
        image = Image.open(io.BytesIO(image_bytes))
        format = image.format
        
        if not format or format.upper() not in SUPPORTED_FORMATS:
            return False, f"Unsupported format: {format}"
        
        return True, "Valid image"
    
    except Exception as e:
        return False, f"Invalid image data: {str(e)}"

def create_thumbnail(base64_data: str, max_size: Tuple[int, int] = (200, 200)) -> str:
    """
    Create thumbnail from base64 image data
    
    Args:
        base64_data: Base64 encoded image string
        max_size: Maximum thumbnail dimensions
    
    Returns:
        Base64 encoded thumbnail data
    """
    try:
        # Process original image
        processed = process_image(base64_data)
        
        # Decode image
        image_bytes = base64.b64decode(processed['base64'])
        image = Image.open(io.BytesIO(image_bytes))
        
        # Create thumbnail
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convert back to base64
        buffer = io.BytesIO()
        format = image.format or 'PNG'
        image.save(buffer, format=format)
        thumbnail_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        logger.info(f"Created thumbnail: {image.size}")
        
        return thumbnail_b64
    
    except Exception as e:
        logger.error(f"Thumbnail creation failed: {e}")
        raise e

def get_image_info(base64_data: str) -> Dict[str, any]:
    """
    Get image information without full processing
    
    Args:
        base64_data: Base64 encoded image string
    
    Returns:
        Dict containing basic image info
    """
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            header, base64_data = base64_data.split(',', 1)
        
        # Decode and load image
        image_bytes = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        return {
            'format': image.format,
            'width': image.size[0],
            'height': image.size[1],
            'mode': image.mode,
            'size_bytes': len(image_bytes),
            'mime_type': get_mime_type(image.format or 'UNKNOWN')
        }
    
    except Exception as e:
        logger.error(f"Failed to get image info: {e}")
        raise e