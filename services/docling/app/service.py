"""
Docling Service - PDF to Markdown conversion
Converts PDFs to clean markdown for RAG ingestion
"""
from flask import Flask, request, jsonify, send_file
import sys
import os
import tempfile
from pathlib import Path
import io

# Add common to path
sys.path.insert(0, '/workspace/services/common')
from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)

# No upload size limit for docling - it can handle large PDFs
app.config['MAX_CONTENT_LENGTH'] = None

# Initialize metrics
metrics = ServiceMetrics("docling-service")

# Initialize health checks
health = HealthCheck("docling-service")

# Check if docling is available
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
    print("✅ Docling library loaded successfully")
except ImportError:
    DOCLING_AVAILABLE = False
    print("⚠️  Docling not available, will use fallback parser")

# Fallback to PyPDF2 if docling not available
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
    print("✅ PyPDF2 fallback available")
except ImportError:
    PYPDF2_AVAILABLE = False
    print("❌ No PDF parser available!")

def parse_with_docling(pdf_path: Path) -> dict:
    """Parse PDF using Docling"""
    try:
        print(f"🔍 Starting docling parse of: {pdf_path}")
        print(f"📏 File size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")

        converter = DocumentConverter()
        print("✅ DocumentConverter created")

        result = converter.convert(str(pdf_path))
        print("✅ Conversion complete")

        # Extract markdown
        markdown = result.document.export_to_markdown()
        print(f"✅ Markdown extracted: {len(markdown)} characters")

        # Extract metadata - ensure all values are JSON serializable
        # Note: num_pages might be a method or property, handle both cases
        try:
            if callable(getattr(result.document, 'num_pages', None)):
                num_pages = result.document.num_pages()
            else:
                num_pages = getattr(result.document, 'num_pages', 0)
        except:
            num_pages = 0

        metadata = {
            'title': str(getattr(result.document, 'title', pdf_path.stem)),
            'num_pages': int(num_pages) if num_pages else 0,
            'parser': 'docling'
        }

        return {
            'success': True,
            'markdown': markdown,
            'metadata': metadata
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Docling parsing failed: {str(e)}")
        print(f"📋 Traceback:\n{error_details}")
        return {
            'success': False,
            'error': str(e)
            # Don't include traceback in JSON response - just log it
        }

def parse_with_pypdf2(pdf_path: Path) -> dict:
    """Fallback: Parse PDF using PyPDF2"""
    try:
        import PyPDF2

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # Extract text from all pages
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"

            # Basic cleanup
            text = text.strip()

            metadata = {
                'title': pdf_path.stem,
                'num_pages': len(reader.pages),
                'parser': 'pypdf2_fallback'
            }

            return {
                'success': True,
                'markdown': text,
                'metadata': metadata
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Health checks
health.add_check("docling_available", lambda: DOCLING_AVAILABLE or PYPDF2_AVAILABLE)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(health.get_health())

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint"""
    return jsonify(metrics.get_stats())

@app.route('/parse', methods=['POST'])
@timed(metrics, 'parse_pdf')
def parse_pdf():
    """
    Parse PDF to markdown

    Body (multipart/form-data):
    - file: PDF file

    Returns:
    {
        "success": true,
        "markdown": "...",
        "metadata": {...}
    }
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400

        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files supported'}), 400

        metrics.increment('parse_requests')

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            file.save(tmp.name)
            tmp_path = Path(tmp.name)

        try:
            # Parse PDF
            if DOCLING_AVAILABLE:
                result = parse_with_docling(tmp_path)
                metrics.increment('docling_parses')
            elif PYPDF2_AVAILABLE:
                result = parse_with_pypdf2(tmp_path)
                metrics.increment('pypdf2_parses')
            else:
                return jsonify({'error': 'No PDF parser available'}), 500

            if result['success']:
                metrics.increment('parse_success')
                metrics.set_gauge('last_pdf_pages', result['metadata'].get('num_pages', 0))
                return jsonify(result)
            else:
                metrics.increment('parse_errors')
                return jsonify(result), 500

        finally:
            # Cleanup temp file
            try:
                tmp_path.unlink()
            except:
                pass

    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/parse/url', methods=['POST'])
@timed(metrics, 'parse_pdf_url')
def parse_pdf_url():
    """
    Parse PDF from URL

    Body:
    {
        "url": "https://example.com/document.pdf"
    }
    """
    try:
        data = request.json
        url = data.get('url', '')

        if not url:
            return jsonify({'error': 'url required'}), 400

        metrics.increment('parse_url_requests')

        # Download PDF
        import requests
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(response.content)
            tmp_path = Path(tmp.name)

        try:
            # Parse PDF
            if DOCLING_AVAILABLE:
                result = parse_with_docling(tmp_path)
            elif PYPDF2_AVAILABLE:
                result = parse_with_pypdf2(tmp_path)
            else:
                return jsonify({'error': 'No PDF parser available'}), 500

            if result['success']:
                metrics.increment('parse_success')
                return jsonify(result)
            else:
                metrics.increment('parse_errors')
                return jsonify(result), 500

        finally:
            # Cleanup temp file
            try:
                tmp_path.unlink()
            except:
                pass

    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/info', methods=['GET'])
def info():
    """Get parser info"""
    return jsonify({
        'service': 'docling-service',
        'parsers': {
            'docling': DOCLING_AVAILABLE,
            'pypdf2': PYPDF2_AVAILABLE
        },
        'active_parser': 'docling' if DOCLING_AVAILABLE else 'pypdf2' if PYPDF2_AVAILABLE else 'none'
    })

if __name__ == '__main__':
    print("🚀 Docling Service starting...")
    print(f"📄 Docling available: {DOCLING_AVAILABLE}")
    print(f"📄 PyPDF2 available: {PYPDF2_AVAILABLE}")

    if not DOCLING_AVAILABLE and not PYPDF2_AVAILABLE:
        print("❌ No PDF parser available! Install docling or PyPDF2")

    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

