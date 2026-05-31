import os
import json
import logging
from flask import request, current_app

logger = logging.getLogger(__name__)
_translations_cache = None

def load_translations_file():
    global _translations_cache
    if _translations_cache is not None:
        return _translations_cache

    try:
        # Resolve path to static/js/translation.json relative to app root
        root_path = current_app.root_path
        json_path = os.path.join(root_path, 'static', 'js', 'translation.json')
        
        with open(json_path, 'r', encoding='utf-8') as f:
            _translations_cache = json.load(f)
            return _translations_cache
    except Exception as e:
        logger.error(f"Error loading translation.json: {str(e)}")
        return {}

def translate(key):
    """Retrieves translation based on current cookie language from translation.json.
    Supports dot notation, e.g., 'common.loading' or 'login.title'.
    """
    lang = request.cookies.get('lang', 'ar')  # default to Arabic
    data = load_translations_file()
    
    # Navigate nested JSON keys
    keys = key.split('.')
    value = data.get(lang, {})
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Fallback to key itself if not found
            return key
            
    return value if isinstance(value, str) else key
