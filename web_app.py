#!/usr/bin/env python3
"""
CV Automation Web Interface
Simple web interface for CV upload and Resumé generation
"""

import os
import sys
import uuid
from pathlib import Path
from flask import Flask, request, render_template, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import json
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.extraction.extractors import ExtractorFactory
from src.core import CVFile, FileFormat
from src.core.database import get_database
from openai_parser import OpenAICVParser
from template_resume_generator_v2 import TemplateResumeGeneratorV2

app = Flask(__name__)
# Get secret key from environment or use default (change in production!)
app.secret_key = os.getenv('SECRET_KEY', 'cv_automation_secret_key_2024_CHANGE_IN_PRODUCTION')

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
TEMPLATE_PATH = '2.docx'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize components
extractor_factory = ExtractorFactory()
openai_parser = OpenAICVParser()
resume_generator = TemplateResumeGeneratorV2(TEMPLATE_PATH)

# Initialize database
db = get_database()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle CV upload and processing"""
    try:
        # Check if file was uploaded
        if 'cv_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['cv_file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload PDF, DOCX, or DOC files.'})
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{file_id}.{file_extension}"
        
        # Save uploaded file
        upload_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(upload_path)
        
        # Process the CV
        result = process_cv(upload_path, filename)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'CV processed successfully!',
                'download_url': f"/download/{result['resume_filename']}",
                'resume_filename': result['resume_filename']
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Processing failed: {result['error']}"
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Upload failed: {str(e)}"
        })

def process_cv(cv_path, original_filename):
    """Process uploaded CV through the complete pipeline"""
    try:
        print(f"Processing CV: {original_filename}")
        
        # Step 1: Extract text from CV
        print("Step 1: Extracting text...")
        cv_file = CVFile(
            id=str(uuid.uuid4()),
            person_name="Unknown",
            file_name=original_filename,
            file_path=cv_path,
            file_format=FileFormat.DOCX if cv_path.endswith('.docx') else FileFormat.PDF,
            file_size=os.path.getsize(cv_path)
        )
        
        extraction_result = extractor_factory.extract(cv_file)
        
        if not extraction_result.success:
            return {'success': False, 'error': f'Text extraction failed: {extraction_result.error}'}
        
        print(f"Text extracted: {len(extraction_result.text)} characters")
        
        # Step 2: Parse with OpenAI
        print("Step 2: Parsing with OpenAI...")
        cv_data = openai_parser.parse_cv_text(extraction_result.text)
        
        if not cv_data:
            return {'success': False, 'error': 'AI parsing failed'}
        
        print(f"CV data parsed successfully. Confidence: {cv_data.get('confidence_score', 0.0)}")
        
        # Step 3: Generate Resumé
        print("Step 3: Generating Resumé...")
        personal_info = cv_data.get('personal_info', {})
        person_name = personal_info.get('full_name', 'Unknown')
        resume_filename = resume_generator.format_resume_filename(personal_info)
        output_path = os.path.join(OUTPUT_FOLDER, resume_filename)
        
        generation_result = resume_generator.generate_resume(cv_data, output_path)
        
        if not generation_result['success']:
            return {'success': False, 'error': f'Resumé generation failed: {generation_result["error"]}'}
        
        print(f"Resumé generated: {resume_filename}")
        
        return {
            'success': True,
            'resume_filename': resume_filename,
            'output_path': output_path,
            'person_name': person_name
        }
    
    except Exception as e:
        print(f"Processing error: {str(e)}")
        return {'success': False, 'error': str(e)}

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated Resumé"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    """API status endpoint"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'extractor': 'ready',
            'openai_parser': 'ready',
            'resume_generator': 'ready',
            'database': 'ready'
        }
    })

# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = db.get_processing_stats(days=30)
        confidence_dist = db.get_confidence_distribution()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'confidence_distribution': confidence_dist,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/dashboard/recent')
def dashboard_recent():
    """Get recent activity"""
    try:
        limit = int(request.args.get('limit', 50))
        recent = db.get_recent_activity(limit=limit)
        
        return jsonify({
            'success': True,
            'activity': recent
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/dashboard/failed')
def dashboard_failed():
    """Get list of failed CVs"""
    try:
        failed = db.get_failed_cvs()
        
        return jsonify({
            'success': True,
            'failed_cvs': failed
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/dashboard/batch/<batch_id>')
def dashboard_batch(batch_id):
    """Get batch job details"""
    try:
        batch = db.get_batch_job(batch_id)
        
        if not batch:
            return jsonify({
                'success': False,
                'error': 'Batch not found'
            }), 404
        
        # batch is now a dict from database
        return jsonify({
            'success': True,
            'batch': {
                'id': batch['id'],
                'total_files': batch['total_files'],
                'processed_files': batch['processed_files'],
                'successful_files': batch['successful_files'],
                'failed_files': batch['failed_files'],
                'status': batch['status'],
                'current_file': batch['current_file'],
                'average_confidence': batch['average_confidence'],
                'started_at': batch['started_at'].isoformat() if batch['started_at'] else None,
                'completed_at': batch['completed_at'].isoformat() if batch['completed_at'] else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting CV Automation Web Interface...")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print(f"Template path: {TEMPLATE_PATH}")
    
    # Create templates directory and HTML file
    os.makedirs('templates', exist_ok=True)
    
    # Create simple HTML template
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CV Automation - Synergie</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #D07E1F;
            text-align: center;
            margin-bottom: 30px;
        }
        .upload-area {
            border: 2px dashed #D07E1F;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            background-color: #fafafa;
        }
        .upload-area:hover {
            background-color: #f0f0f0;
        }
        input[type="file"] {
            margin: 20px 0;
        }
        button {
            background-color: #D07E1F;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #b86a1a;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
        }
        .success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .error {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #D07E1F;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CV Automation - Synergie</h1>
        <p style="text-align: center; color: #666;">
            Upload your CV and get a professionally formatted Synergie Resumé
        </p>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area">
                <h3>Upload CV</h3>
                <p>Supported formats: PDF, DOCX, DOC</p>
                <input type="file" id="cvFile" name="cv_file" accept=".pdf,.docx,.doc" required>
                <br>
                <button type="submit" id="submitBtn">Generate Resumé</button>
            </div>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Processing your CV...</p>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('cvFile');
            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            if (!fileInput.files[0]) {
                showResult('Please select a file', 'error');
                return;
            }
            
            // Show loading
            loading.style.display = 'block';
            submitBtn.disabled = true;
            result.innerHTML = '';
            
            const formData = new FormData();
            formData.append('cv_file', fileInput.files[0]);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showResult(`
                        <strong>Success!</strong><br>
                        Your Resumé has been generated successfully.<br>
                        <a href="${data.download_url}" download style="color: #D07E1F; text-decoration: none; font-weight: bold;">
                            📥 Download Resumé
                        </a>
                    `, 'success');
                } else {
                    showResult(`<strong>Error:</strong> ${data.error}`, 'error');
                }
            } catch (error) {
                showResult(`<strong>Error:</strong> ${error.message}`, 'error');
            } finally {
                loading.style.display = 'none';
                submitBtn.disabled = false;
            }
        });
        
        function showResult(message, type) {
            const result = document.getElementById('result');
            result.innerHTML = `<div class="result ${type}">${message}</div>`;
        }
    </script>
</body>
</html>
    '''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Production-ready server configuration
    # Use PORT environment variable for PaaS platforms (Railway, Render, etc.)
    # Falls back to 5000 for local development
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    port = int(os.getenv('PORT', os.getenv('FLASK_PORT', 5000)))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
