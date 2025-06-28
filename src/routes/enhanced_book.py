import requests
import os
import tempfile
import subprocess
from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin

enhanced_book_bp = Blueprint('enhanced_book', __name__)

# API endpoints
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
GUTENDX_API = "https://gutendx.com/books"
OPENLIBRARY_API = "https://openlibrary.org/search.json"

def search_google_books(query, max_results=10):
    """Search Google Books API for book information."""
    try:
        params = {
            'q': query,
            'maxResults': max_results,
            'printType': 'books'
        }
        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching Google Books: {e}")
        return None

def search_gutendx(query, max_results=10):
    """Search Gutendx API for public domain books."""
    try:
        params = {
            'search': query,
            'page_size': max_results
        }
        response = requests.get(GUTENDX_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching Gutendx: {e}")
        return None

def search_openlibrary(query, max_results=10):
    """Search Open Library API for book information."""
    try:
        params = {
            'q': query,
            'limit': max_results,
            'fields': 'key,title,author_name,first_publish_year,isbn,cover_i,subject,ia'
        }
        response = requests.get(OPENLIBRARY_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching Open Library: {e}")
        return None

def get_pdf_links_from_google_books(volume_info, access_info):
    """Extract PDF links from Google Books volume."""
    pdf_links = []
    
    # Check for direct PDF access
    if access_info.get('pdf', {}).get('isAvailable'):
        pdf_url = access_info.get('pdf', {}).get('downloadLink')
        if pdf_url:
            pdf_links.append({
                'source': 'Google Books',
                'url': pdf_url,
                'type': 'direct'
            })
    
    # Check for web reader with PDF option
    if access_info.get('webReaderLink'):
        web_reader = access_info.get('webReaderLink')
        if 'books.google' in web_reader:
            pdf_links.append({
                'source': 'Google Books Reader',
                'url': web_reader,
                'type': 'web_reader'
            })
    
    return pdf_links

def get_pdf_links_from_gutendx(book_data):
    """Extract PDF links from Gutendx book data."""
    pdf_links = []
    formats = book_data.get('formats', {})
    
    # Look for PDF formats
    for format_type, url in formats.items():
        if 'pdf' in format_type.lower():
            pdf_links.append({
                'source': 'Project Gutenberg',
                'url': url,
                'type': 'direct'
            })
    
    # Also check for EPUB and MOBI that we can convert
    epub_url = formats.get('application/epub+zip')
    if epub_url:
        pdf_links.append({
            'source': 'Project Gutenberg (EPUB)',
            'url': epub_url,
            'type': 'convertible',
            'format': 'epub'
        })
    
    mobi_url = formats.get('application/x-mobipocket-ebook')
    if mobi_url:
        pdf_links.append({
            'source': 'Project Gutenberg (MOBI)',
            'url': mobi_url,
            'type': 'convertible',
            'format': 'mobi'
        })
    
    return pdf_links

def get_pdf_links_from_openlibrary(doc):
    """Extract PDF links from Open Library document."""
    pdf_links = []
    
    # Check for Internet Archive identifier
    ia_id = doc.get('ia')
    if ia_id:
        # Construct Internet Archive PDF URL
        if isinstance(ia_id, list) and ia_id:
            ia_id = ia_id[0]
        
        if ia_id:
            ia_pdf_url = f"https://archive.org/download/{ia_id}/{ia_id}.pdf"
            pdf_links.append({
                'source': 'Internet Archive',
                'url': ia_pdf_url,
                'type': 'direct'
            })
    
    return pdf_links

def convert_ebook_to_pdf(ebook_url, format_type):
    """Convert EPUB or MOBI to PDF using epub2pdf library."""
    try:
        # Download the ebook file
        response = requests.get(ebook_url, timeout=30)
        response.raise_for_status()
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=f'.{format_type}', delete=False) as temp_ebook:
            temp_ebook.write(response.content)
            temp_ebook_path = temp_ebook.name
        
        # Create output PDF path
        temp_pdf_path = temp_ebook_path.replace(f'.{format_type}', '.pdf')
        
        # Convert using epub2pdf (if available)
        try:
            if format_type == 'epub':
                # Try using epub2pdf
                result = subprocess.run([
                    'python', '-m', 'epub2pdf', temp_ebook_path, temp_pdf_path
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(temp_pdf_path):
                    return temp_pdf_path
        except Exception as e:
            print(f"Conversion failed: {e}")
        
        # Cleanup temporary ebook file
        os.unlink(temp_ebook_path)
        return None
        
    except Exception as e:
        print(f"Error converting ebook to PDF: {e}")
        return None

@enhanced_book_bp.route('/enhanced-search', methods=['POST'])
@cross_origin()
def enhanced_search():
    """Enhanced book search with multiple sources and PDF conversion."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Translate if needed (reuse existing translation logic)
        if data.get('language') == 'ar':
            # Use existing translation service
            translation_response = requests.post(
                'http://localhost:5000/api/translate',
                json={'text': query, 'source': 'ar', 'target': 'en'},
                timeout=10
            )
            if translation_response.status_code == 200:
                translated = translation_response.json().get('translated_text', query)
                query = translated
        
        results = []
        
        # Search Google Books
        google_results = search_google_books(query)
        if google_results and 'items' in google_results:
            for item in google_results['items'][:5]:  # Limit to 5 results per source
                volume_info = item.get('volumeInfo', {})
                access_info = item.get('accessInfo', {})
                
                # Get PDF links
                pdf_links = get_pdf_links_from_google_books(volume_info, access_info)
                
                book_data = {
                    'id': item.get('id'),
                    'title': volume_info.get('title', 'Unknown Title'),
                    'authors': volume_info.get('authors', ['Unknown Author']),
                    'categories': volume_info.get('categories', []),
                    'description': volume_info.get('description', ''),
                    'cover_url': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                    'published_date': volume_info.get('publishedDate', ''),
                    'page_count': volume_info.get('pageCount'),
                    'language': volume_info.get('language', 'en'),
                    'pdf_links': pdf_links,
                    'source': 'Google Books'
                }
                results.append(book_data)
        
        # Search Gutendx
        gutendx_results = search_gutendx(query)
        if gutendx_results and 'results' in gutendx_results:
            for book in gutendx_results['results'][:5]:  # Limit to 5 results per source
                # Get PDF links
                pdf_links = get_pdf_links_from_gutendx(book)
                
                book_data = {
                    'id': f"gutendx_{book.get('id')}",
                    'title': book.get('title', 'Unknown Title'),
                    'authors': [author.get('name', 'Unknown Author') for author in book.get('authors', [])],
                    'categories': book.get('subjects', []),
                    'description': book.get('summaries', [''])[0] if book.get('summaries') else '',
                    'cover_url': book.get('formats', {}).get('image/jpeg', ''),
                    'published_date': '',
                    'page_count': None,
                    'language': book.get('languages', ['en'])[0] if book.get('languages') else 'en',
                    'pdf_links': pdf_links,
                    'source': 'Project Gutenberg'
                }
                results.append(book_data)
        
        # Search Open Library
        openlibrary_results = search_openlibrary(query)
        if openlibrary_results and 'docs' in openlibrary_results:
            for doc in openlibrary_results['docs'][:5]:  # Limit to 5 results per source
                # Get PDF links
                pdf_links = get_pdf_links_from_openlibrary(doc)
                
                book_data = {
                    'id': f"openlibrary_{doc.get('key', '').replace('/works/', '')}",
                    'title': doc.get('title', 'Unknown Title'),
                    'authors': doc.get('author_name', ['Unknown Author']),
                    'categories': doc.get('subject', [])[:5] if doc.get('subject') else [],  # Limit subjects
                    'description': '',
                    'cover_url': f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-M.jpg" if doc.get('cover_i') else '',
                    'published_date': str(doc.get('first_publish_year', '')),
                    'page_count': None,
                    'language': 'en',
                    'pdf_links': pdf_links,
                    'source': 'Open Library'
                }
                results.append(book_data)
        
        return jsonify({
            'query': query,
            'total_results': len(results),
            'results': results
        })
        
    except Exception as e:
        print(f"Error in enhanced search: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@enhanced_book_bp.route('/convert-to-pdf', methods=['POST'])
@cross_origin()
def convert_to_pdf():
    """Convert an ebook URL to PDF and serve it."""
    try:
        data = request.get_json()
        ebook_url = data.get('url')
        format_type = data.get('format', 'epub')
        
        if not ebook_url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Convert the ebook to PDF
        pdf_path = convert_ebook_to_pdf(ebook_url, format_type)
        
        if pdf_path and os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f'converted_book.pdf',
                mimetype='application/pdf'
            )
        else:
            return jsonify({'error': 'Conversion failed'}), 500
            
    except Exception as e:
        print(f"Error in PDF conversion: {e}")
        return jsonify({'error': 'Internal server error'}), 500

