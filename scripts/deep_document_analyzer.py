#!/usr/bin/env python3
"""
Deep Document Analyzer - Extracts and compares CV vs Resumé structure
Analyzes DOCX and PDF files to understand formatting differences
"""

import os
import sys
from datetime import datetime

def extract_text_from_docx(docx_path):
    """
    Extract text from DOCX file
    
    Args:
        docx_path (str): Path to DOCX file
        
    Returns:
        str: Extracted text
    """
    try:
        from docx import Document
        
        doc = Document(docx_path)
        text_parts = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        return "\n".join(text_parts)
    except Exception as e:
        return f"Error: {e}"

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF file
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        str: Extracted text
    """
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
            
            return text.strip()
    except Exception as e:
        return f"Error: {e}"

def analyze_document_structure(file_path, doc_type):
    """Analyze structure of a document"""
    print(f"\n{'='*70}")
    print(f"ANALYZING {doc_type.upper()}: {os.path.basename(file_path)}")
    print(f"{'='*70}")
    
    # Get file info
    file_size = os.path.getsize(file_path) / 1024
    file_ext = os.path.splitext(file_path)[1].lower()
    
    print(f"File: {file_path}")
    print(f"Size: {file_size:.1f} KB")
    print(f"Format: {file_ext}")
    
    # Extract text
    if file_ext == '.docx':
        text = extract_text_from_docx(file_path)
    elif file_ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    else:
        print("Unsupported format")
        return None
    
    if not text or text.startswith("Error"):
        print(f"⚠️  Could not extract text: {text}")
        return None
    
    print(f"\nText length: {len(text)} characters")
    print(f"Number of lines: {text.count(chr(10)) + 1}")
    
    # Analyze structure
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    print(f"\n{'─'*70}")
    print(f"DOCUMENT STRUCTURE (first 50 lines):")
    print(f"{'─'*70}")
    
    for i, line in enumerate(lines[:50], 1):
        # Truncate long lines
        display_line = line[:120] + "..." if len(line) > 120 else line
        print(f"{i:3}. {display_line}")
    
    # Identify sections
    print(f"\n{'─'*70}")
    print(f"IDENTIFIED SECTIONS:")
    print(f"{'─'*70}")
    
    # Common section headers
    section_keywords = [
        'personalia', 'persoonlijk', 'personal', 'profile', 'profiel',
        'opleiding', 'education', 'opleidingen',
        'ervaring', 'werkervaring', 'experience', 'work experience',
        'projecten', 'projects', 'projectervaring',
        'vaardigheden', 'skills', 'competenties',
        'certificaten', 'certificates', 'certificering',
        'talen', 'languages',
        'referenties', 'references',
        'cursussen', 'training'
    ]
    
    sections_found = []
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for keyword in section_keywords:
            if keyword in line_lower and len(line) < 50:  # Section headers are usually short
                sections_found.append(f"Line {i+1}: {line}")
                break
    
    if sections_found:
        for section in sections_found[:15]:  # Show first 15 sections
            print(f"  • {section}")
    else:
        print("  No clear sections identified")
    
    return text

def compare_documents_side_by_side(cv_path, resume_path):
    """Compare CV and Resume side by side"""
    print(f"\n{'='*70}")
    print(f"SIDE-BY-SIDE COMPARISON")
    print(f"{'='*70}")
    
    print(f"\nCV:     {os.path.basename(cv_path)}")
    print(f"Resume: {os.path.basename(resume_path)}")
    
    # Extract both
    cv_ext = os.path.splitext(cv_path)[1].lower()
    resume_ext = os.path.splitext(resume_path)[1].lower()
    
    if cv_ext == '.docx':
        cv_text = extract_text_from_docx(cv_path)
    else:
        cv_text = extract_text_from_pdf(cv_path)
    
    if resume_ext == '.docx':
        resume_text = extract_text_from_docx(resume_path)
    else:
        resume_text = extract_text_from_pdf(resume_path)
    
    print(f"\n{'─'*70}")
    print(f"COMPARISON METRICS:")
    print(f"{'─'*70}")
    print(f"{'Metric':<30} {'CV':<20} {'Resume':<20}")
    print(f"{'─'*70}")
    print(f"{'Characters':<30} {len(cv_text):<20} {len(resume_text):<20}")
    print(f"{'Lines':<30} {cv_text.count(chr(10)) + 1:<20} {resume_text.count(chr(10)) + 1:<20}")
    print(f"{'Words (approx.)':<30} {len(cv_text.split()):<20} {len(resume_text.split()):<20}")
    
    # Check for common formatting indicators
    cv_has_bullets = '•' in cv_text or '-' in cv_text
    resume_has_bullets = '•' in resume_text or '-' in resume_text
    
    print(f"{'Has bullet points':<30} {str(cv_has_bullets):<20} {str(resume_has_bullets):<20}")
    
    # Check for dates
    import re
    date_pattern = r'\d{4}'
    cv_dates = len(re.findall(date_pattern, cv_text))
    resume_dates = len(re.findall(date_pattern, resume_text))
    
    print(f"{'Date references (years)':<30} {cv_dates:<20} {resume_dates:<20}")

def analyze_standard_template():
    """Analyze the standard Resumé template"""
    base_path = r"C:\Users\RudoJockinSynergiepr\Synergie PM\Netwerk - Documenten\A. STANDAARD RESUME"
    template_file = os.path.join(base_path, "Standaard Resume_Synergie projectmanagement.docx")
    
    print(f"\n{'='*70}")
    print(f"STANDARD RESUMÉ TEMPLATE ANALYSIS")
    print(f"{'='*70}")
    
    if not os.path.exists(template_file):
        print(f"Template not found: {template_file}")
        return
    
    analyze_document_structure(template_file, "TEMPLATE")

def main():
    """Main analysis function"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Deep Document Analyzer started...")
    
    # Install python-docx if needed
    try:
        from docx import Document
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installing python-docx...")
        os.system("pip install python-docx -q")
    
    # Install PyPDF2 if needed
    try:
        import PyPDF2
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installing PyPDF2...")
        os.system("pip install PyPDF2 -q")
    
    # Analyze standard template
    analyze_standard_template()
    
    # Analyze sample CV
    base_path = r"C:\Users\RudoJockinSynergiepr\Synergie PM\Netwerk - Documenten"
    
    # Example 1: Abdelhasib, Eslam (has both)
    person_folder = os.path.join(base_path, "Abdelhasib, Eslam")
    cv_path = os.path.join(person_folder, "CV_NL_Eslam Abdelhasib.pdf")
    resume_path = os.path.join(person_folder, "Resume_Synergie projectmanagement_Eslam Abdelhasib (gemeente Utrecht).docx")
    
    if os.path.exists(cv_path):
        analyze_document_structure(cv_path, "RAW CV")
    
    if os.path.exists(resume_path):
        analyze_document_structure(resume_path, "PROCESSED RESUMÉ")
    
    if os.path.exists(cv_path) and os.path.exists(resume_path):
        compare_documents_side_by_side(cv_path, resume_path)
    
    # Example 2: Smit, Ronald (has both)
    person_folder2 = os.path.join(base_path, "Smit, Ronald")
    cv_path2 = os.path.join(person_folder2, "CV Ronald Smit 2025.pdf")
    resume_path2 = os.path.join(person_folder2, "Resumé_Synergie projectmanagement_Ronald Smit.docx")
    
    if os.path.exists(cv_path2):
        analyze_document_structure(cv_path2, "RAW CV")
    
    if os.path.exists(resume_path2):
        analyze_document_structure(resume_path2, "PROCESSED RESUMÉ")
    
    if os.path.exists(cv_path2) and os.path.exists(resume_path2):
        compare_documents_side_by_side(cv_path2, resume_path2)
    
    print(f"\n{'='*70}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Deep analysis complete!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

