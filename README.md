# Book Information Retrieval System

An AI-powered book search system that supports both English and Arabic languages, providing book covers, categories, authors, and free PDF download links.

## Features

- 🔍 **Smart Search**: Search for books in English or Arabic
- 🌐 **Multilingual**: Full support for English and Arabic (RTL layout)
- 📚 **Comprehensive Data**: Book covers, authors, categories, and descriptions
- 📄 **Free PDFs**: Direct download links for public domain books
- 🤖 **AI Translation**: Automatic Arabic to English translation for better search results
- 📱 **Responsive**: Works on desktop and mobile devices

## APIs Used

- **Google Books API**: Comprehensive book metadata
- **Gutendx API**: Public domain books with PDF links
- **MyMemory Translation API**: Arabic to English translation
- **Open Library Covers API**: Book cover images (fallback)

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm (or npm)

### 1. Backend Setup (Flask)

```bash
# Navigate to the project directory
cd book-api

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask server
python src/main.py
```

The backend will be available at `http://localhost:5000`

### 2. Frontend Development (Optional)

If you want to modify the frontend:

```bash
# Navigate to frontend directory
cd ../book-info-system

# Install dependencies
pnpm install

# Run development server
pnpm run dev --host

# Build for production
pnpm run build

# Copy build to Flask static directory
cp -r dist/* ../book-api/src/static/
```

### 3. Access the Application

Once the Flask server is running, open your browser and go to:
```
http://localhost:5000
```

## Project Structure

```
book-api/
├── src/
│   ├── routes/
│   │   ├── book.py          # Book search API endpoints
│   │   ├── translation.py   # Translation API endpoints
│   │   └── user.py          # User management (template)
│   ├── models/
│   │   └── user.py          # Database models
│   ├── static/              # Frontend build files
│   │   ├── index.html
│   │   └── assets/
│   ├── database/
│   │   └── app.db           # SQLite database
│   └── main.py              # Flask application entry point
├── venv/                    # Python virtual environment
├── requirements.txt         # Python dependencies
└── README.md               # This file

book-info-system/           # React frontend source (for development)
├── src/
│   ├── components/
│   ├── App.jsx             # Main React component
│   └── main.jsx            # React entry point
├── dist/                   # Built frontend files
├── package.json
└── pnpm-lock.yaml
```

## API Endpoints

### Book Search
- **POST** `/api/books/search`
  - Body: `{"query": "book name", "language": "en|ar"}`
  - Returns: Book information with covers and PDF links

### Translation
- **POST** `/api/translate/translate`
  - Body: `{"text": "text to translate", "source_lang": "ar", "target_lang": "en"}`
  - Returns: Translated text

### Health Check
- **GET** `/api/books/health`
  - Returns: API status

## Usage Examples

### English Search
1. Enter book name in English (e.g., "Pride and Prejudice")
2. Click "Search Books"
3. View results with book information and PDF links

### Arabic Search
1. Click the language toggle to switch to Arabic
2. Enter book name in Arabic (e.g., "أليس في بلاد العجائب")
3. Click "البحث عن الكتب"
4. The system automatically translates to English for better search results

## API Rate Limits

- **MyMemory Translation**: 50,000 characters/day with email parameter
- **Google Books**: No explicit limit for basic usage
- **Gutendx**: No explicit limit

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port in `src/main.py`
2. **Translation not working**: Check internet connection and MyMemory API status
3. **No search results**: Try different search terms or check API connectivity

### Debug Mode

The Flask app runs in debug mode by default. Check the console for detailed error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please check the troubleshooting section or create an issue in the project repository.

