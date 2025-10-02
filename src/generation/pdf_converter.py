#!/usr/bin/env python3
"""
PDF Converter - Convert DOCX to PDF with high quality
Handles document conversion while preserving formatting
"""

import os
import subprocess
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.core import CVFile, ProcessingStatus


class PDFConverter:
    """
    Convert DOCX to PDF with high quality
    
    Features:
    - High-quality PDF conversion
    - Preserves formatting and styling
    - Handles fonts and colors correctly
    - Error handling and validation
    - Multiple conversion methods
    
    Conversion Methods:
    1. LibreOffice (preferred - best quality)
    2. Microsoft Word (if available)
    3. Python libraries (fallback)
    """
    
    def __init__(self):
        """Initialize PDF converter"""
        
        # Check available conversion methods
        self.libreoffice_available = self._check_libreoffice()
        self.word_available = self._check_word()
        self.python_libs_available = self._check_python_libs()
        
        # Set preferred method
        if self.libreoffice_available:
            self.preferred_method = 'libreoffice'
        elif self.word_available:
            self.preferred_method = 'word'
        elif self.python_libs_available:
            self.preferred_method = 'python'
        else:
            self.preferred_method = None
    
    def convert_docx_to_pdf(self, docx_path: str, output_dir: str) -> Optional[str]:
        """
        Convert DOCX file to PDF
        
        Args:
            docx_path: Path to DOCX file
            output_dir: Directory to save PDF
            
        Returns:
            Path to converted PDF file or None if failed
        """
        
        if not os.path.exists(docx_path):
            print(f"Error: DOCX file not found: {docx_path}")
            return None
        
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Try conversion methods in order of preference
        conversion_methods = [
            ('libreoffice', self._convert_with_libreoffice),
            ('word', self._convert_with_word),
            ('python', self._convert_with_python)
        ]
        
        for method_name, method_func in conversion_methods:
            if method_name == 'libreoffice' and not self.libreoffice_available:
                continue
            if method_name == 'word' and not self.word_available:
                continue
            if method_name == 'python' and not self.python_libs_available:
                continue
            
            try:
                print(f"Converting with {method_name}...")
                success = method_func(docx_path, pdf_path)
                
                if success and os.path.exists(pdf_path):
                    print(f"✅ PDF conversion successful: {pdf_path}")
                    return pdf_path
                else:
                    print(f"❌ {method_name} conversion failed")
            
            except Exception as e:
                print(f"❌ {method_name} conversion error: {str(e)}")
                continue
        
        print("❌ All conversion methods failed")
        return None
    
    def _convert_with_libreoffice(self, docx_path: str, pdf_path: str) -> bool:
        """Convert using LibreOffice (best quality)"""
        
        try:
            # LibreOffice command
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(pdf_path),
                docx_path
            ]
            
            # Run conversion
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return True
            else:
                print(f"LibreOffice error: {result.stderr}")
                return False
        
        except subprocess.TimeoutExpired:
            print("LibreOffice conversion timeout")
            return False
        except Exception as e:
            print(f"LibreOffice conversion error: {str(e)}")
            return False
    
    def _convert_with_word(self, docx_path: str, pdf_path: str) -> bool:
        """Convert using Microsoft Word (if available)"""
        
        try:
            # Try to use win32com if available
            import win32com.client
            
            # Create Word application
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            # Open document
            doc = word.Documents.Open(docx_path)
            
            # Export as PDF
            doc.ExportAsFixedFormat(
                OutputFileName=pdf_path,
                ExportFormat=17,  # PDF format
                OpenAfterExport=False,
                OptimizeFor=0,  # Print quality
                BitmapMissingFonts=True,
                DocStructureTags=True,
                CreateBookmarks=0,
                UseDocumentStructure=True
            )
            
            # Close document and Word
            doc.Close()
            word.Quit()
            
            return True
        
        except ImportError:
            print("win32com not available for Word conversion")
            return False
        except Exception as e:
            print(f"Word conversion error: {str(e)}")
            return False
    
    def _convert_with_python(self, docx_path: str, pdf_path: str) -> bool:
        """Convert using Python libraries (fallback)"""
        
        try:
            # Try docx2pdf
            from docx2pdf import convert
            
            convert(docx_path, pdf_path)
            return True
        
        except ImportError:
            print("docx2pdf not available")
        
        try:
            # Try python-docx + reportlab
            from docx import Document
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            # Read DOCX
            doc = Document(docx_path)
            
            # Create PDF
            pdf_doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=12,
                textColor='#D07E1F'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6
            )
            
            # Build PDF content
            story = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    # Determine style based on formatting
                    if paragraph.runs and paragraph.runs[0].bold:
                        if paragraph.runs[0].font.color.rgb and str(paragraph.runs[0].font.color.rgb) == 'D07E1F':
                            story.append(Paragraph(paragraph.text, title_style))
                        else:
                            story.append(Paragraph(paragraph.text, styles['Heading2']))
                    else:
                        story.append(Paragraph(paragraph.text, body_style))
                    
                    story.append(Spacer(1, 6))
            
            # Build PDF
            pdf_doc.build(story)
            return True
        
        except ImportError:
            print("reportlab not available")
        except Exception as e:
            print(f"Python conversion error: {str(e)}")
        
        return False
    
    def _check_libreoffice(self) -> bool:
        """Check if LibreOffice is available"""
        
        try:
            result = subprocess.run(['libreoffice', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _check_word(self) -> bool:
        """Check if Microsoft Word is available"""
        
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Quit()
            return True
        except:
            return False
    
    def _check_python_libs(self) -> bool:
        """Check if Python conversion libraries are available"""
        
        try:
            from docx2pdf import convert
            return True
        except ImportError:
            pass
        
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate
            return True
        except ImportError:
            pass
        
        return False
    
    def get_conversion_info(self) -> Dict[str, Any]:
        """Get information about available conversion methods"""
        
        return {
            'libreoffice_available': self.libreoffice_available,
            'word_available': self.word_available,
            'python_libs_available': self.python_libs_available,
            'preferred_method': self.preferred_method,
            'all_methods_available': all([
                self.libreoffice_available,
                self.word_available,
                self.python_libs_available
            ])
        }
    
    def validate_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Validate converted PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with validation results
        """
        
        validation_results = {
            'file_exists': False,
            'file_size': 0,
            'is_valid_pdf': False,
            'page_count': 0,
            'issues': []
        }
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            validation_results['issues'].append("PDF file does not exist")
            return validation_results
        
        validation_results['file_exists'] = True
        validation_results['file_size'] = os.path.getsize(pdf_path)
        
        # Check if file is valid PDF
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                validation_results['is_valid_pdf'] = True
                validation_results['page_count'] = len(pdf_reader.pages)
        
        except ImportError:
            validation_results['issues'].append("PyPDF2 not available for PDF validation")
        except Exception as e:
            validation_results['issues'].append(f"PDF validation error: {str(e)}")
        
        return validation_results
    
    def batch_convert(self, docx_files: List[str], output_dir: str) -> Dict[str, Any]:
        """
        Convert multiple DOCX files to PDF
        
        Args:
            docx_files: List of DOCX file paths
            output_dir: Output directory for PDFs
            
        Returns:
            Dictionary with conversion results
        """
        
        results = {
            'total_files': len(docx_files),
            'successful': 0,
            'failed': 0,
            'converted_files': [],
            'failed_files': [],
            'errors': []
        }
        
        for docx_file in docx_files:
            try:
                pdf_path = self.convert_docx_to_pdf(docx_file, output_dir)
                
                if pdf_path:
                    results['successful'] += 1
                    results['converted_files'].append(pdf_path)
                else:
                    results['failed'] += 1
                    results['failed_files'].append(docx_file)
            
            except Exception as e:
                results['failed'] += 1
                results['failed_files'].append(docx_file)
                results['errors'].append(f"{docx_file}: {str(e)}")
        
        return results
