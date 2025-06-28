import requests
import os
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

book_bp = Blueprint('book', __name__)

# API endpoints
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
GUTENDEX_API = "https://gutendex.com/books"
OPEN_LIBRARY_COVERS = "https://covers.openlibrary.org/b"

@book_bp.route('/search', methods=['POST'])
@cross_origin()
def search_books():
    """Search for books using multiple APIs"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        language = data.get('language', 'en')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # If the query is in Arabic, translate it to English for better search results
        search_query = query
        if language == 'ar':
            # Simple Arabic detection
            arabic_chars = sum(1 for char in query if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F')
            total_chars = len([char for char in query if char.isalpha()])
            
            if total_chars > 0 and arabic_chars / total_chars > 0.3:
                # Translate Arabic to English for search
                translated_query = translate_arabic_to_english(query)
                if translated_query:
                    search_query = translated_query
        
        # Search Google Books API
        google_books = search_google_books(search_query)
        
        # Search Gutendx for public domain books
        gutendx_books = search_gutendx_books(search_query)
        
        # Combine and format results
        combined_results = combine_book_results(google_books, gutendx_books)
        
        return jsonify({
            'books': combined_results,
            'total': len(combined_results),
            'search_query': search_query,
            'original_query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def translate_arabic_to_english(text):
    """Translate Arabic text to English using MyMemory API"""
    try:
        params = {
            'q': text,
            'langpair': 'ar|en',
            'mt': 1,
            'de': 'bookfinder@example.com'
        }
        
        response = requests.get('https://api.mymemory.translated.net/get', params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data.get('responseStatus') == 200:
            return data.get('responseData', {}).get('translatedText', text)
        
    except Exception as e:
        print(f"Translation error: {e}")
    
    return text  # Return original if translation fails

def search_google_books(query):
    """Search Google Books API"""
    try:
        params = {
            'q': query,
            'maxResults': 10,
            'printType': 'books'
        }
        
        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get('items', []):
            volume_info = item.get('volumeInfo', {})
            access_info = item.get('accessInfo', {})
            
            book = {
                'id': item.get('id'),
                'title': volume_info.get('title', 'Unknown Title'),
                'authors': volume_info.get('authors', ['Unknown Author']),
                'categories': volume_info.get('categories', []),
                'description': volume_info.get('description', ''),
                'published_date': volume_info.get('publishedDate', ''),
                'page_count': volume_info.get('pageCount'),
                'language': volume_info.get('language', 'en'),
                'cover_url': get_cover_url(volume_info.get('imageLinks', {})),
                'pdf_url': get_pdf_url(access_info),
                'is_public_domain': access_info.get('publicDomain', False),
                'source': 'google_books'
            }
            books.append(book)
            
        return books
        
    except Exception as e:
        print(f"Error searching Google Books: {e}")
        return []

def search_gutendx_books(query):
    """Search Gutendx API for public domain books"""
    try:
        params = {
            'search': query,
            'page_size': 10
        }
        
        response = requests.get(GUTENDX_API, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get('results', []):
            # Get PDF format URL
            formats = item.get('formats', {})
            pdf_url = None
            
            # Look for PDF format
            for format_type, url in formats.items():
                if 'pdf' in format_type.lower():
                    pdf_url = url
                    break
            
            # If no PDF, try to get from Project Gutenberg
            if not pdf_url and item.get('id'):
                pdf_url = f"https://www.gutenberg.org/files/{item['id']}/{item['id']}-pdf.pdf"
            
            book = {
                'id': f"gutendx_{item.get('id')}",
                'title': item.get('title', 'Unknown Title'),
                'authors': [author.get('name', 'Unknown Author') for author in item.get('authors', [])],
                'categories': item.get('subjects', [])[:5],  # Limit to first 5 subjects
                'description': item.get('summaries', [''])[0] if item.get('summaries') else '',
                'published_date': '',
                'page_count': None,
                'language': item.get('languages', ['en'])[0],
                'cover_url': formats.get('image/jpeg', ''),
                'pdf_url': pdf_url,
                'is_public_domain': True,
                'source': 'gutendx'
            }
            books.append(book)
            
        return books
        
    except Exception as e:
        print(f"Error searching Gutendx: {e}")
        return []

def get_cover_url(image_links):
    """Extract the best available cover image URL"""
    if not image_links:
        return None
    
    # Prefer larger images
    for size in ['extraLarge', 'large', 'medium', 'small', 'thumbnail', 'smallThumbnail']:
        if size in image_links:
            return image_links[size]
    
    return None

def get_pdf_url(access_info):
    """Extract PDF URL if available"""
    pdf_info = access_info.get("pdf", {})
    # For public domain books, Google Books might provide a direct link or indicate full viewability
    if access_info.get("publicDomain"):
        # Check if there's a direct download link for PDF
        if pdf_info.get("isAvailable") and pdf_info.get("downloadLink"):
            return pdf_info.get("downloadLink")
        # If not a direct download, check for webReaderLink which might lead to viewable PDF
        elif access_info.get("webReaderLink"):
            return access_info.get("webReaderLink")
    return None

def combine_book_results(google_books, gutendx_books):
    """Combine and deduplicate results from different sources"""
    all_books = []
    seen_titles = set()
    
    # Add Gutendx books first (they have PDF links)
    for book in gutendx_books:
        title_key = book['title'].lower().strip()
        if title_key not in seen_titles:
            all_books.append(book)
            seen_titles.add(title_key)
    
    # Add Google Books that aren't duplicates
    for book in google_books:
        title_key = book['title'].lower().strip()
        if title_key not in seen_titles:
            all_books.append(book)
            seen_titles.add(title_key)
    
    return all_books[:10]  # Limit to 10 results

@book_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Book API is running'})

