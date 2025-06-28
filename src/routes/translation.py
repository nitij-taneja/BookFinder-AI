import requests
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

translation_bp = Blueprint('translation', __name__)

MYMEMORY_API = "https://api.mymemory.translated.net/get"

@translation_bp.route('/translate', methods=['POST'])
@cross_origin()
def translate_text():
    """Translate text using MyMemory API"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        source_lang = data.get('source_lang', 'ar')
        target_lang = data.get('target_lang', 'en')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Use MyMemory API for translation
        params = {
            'q': text,
            'langpair': f'{source_lang}|{target_lang}',
            'mt': 1,  # Enable machine translation
            'de': 'bookfinder@example.com'  # Contact email for higher limits
        }
        
        response = requests.get(MYMEMORY_API, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('responseStatus') == 200:
            translated_text = data.get('responseData', {}).get('translatedText', text)
            return jsonify({
                'translated_text': translated_text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'original_text': text
            })
        else:
            # If translation fails, return original text
            return jsonify({
                'translated_text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'original_text': text,
                'warning': 'Translation service unavailable, using original text'
            })
        
    except Exception as e:
        print(f"Translation error: {e}")
        # Return original text if translation fails
        return jsonify({
            'translated_text': data.get('text', ''),
            'source_lang': source_lang,
            'target_lang': target_lang,
            'original_text': data.get('text', ''),
            'error': 'Translation failed, using original text'
        })

@translation_bp.route('/detect-language', methods=['POST'])
@cross_origin()
def detect_language():
    """Simple language detection based on character patterns"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'language': 'en'})
        
        # Simple Arabic detection based on Unicode ranges
        arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F')
        total_chars = len([char for char in text if char.isalpha()])
        
        if total_chars > 0 and arabic_chars / total_chars > 0.3:
            return jsonify({'language': 'ar'})
        else:
            return jsonify({'language': 'en'})
            
    except Exception as e:
        print(f"Language detection error: {e}")
        return jsonify({'language': 'en'})  # Default to English

