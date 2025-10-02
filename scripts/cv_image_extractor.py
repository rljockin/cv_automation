#!/usr/bin/env python3
"""
CV Image Text Extractor - Converteert PDF naar afbeeldingen voor handmatige OCR
Gemaakt voor het uitlezen van CV bestanden die als foto's zijn opgeslagen
"""

import sys
import os
from datetime import datetime

def convert_pdf_to_images(pdf_path, output_dir="cv_images"):
    """
    Converteert PDF naar afbeeldingen
    
    Args:
        pdf_path (str): Pad naar het PDF bestand
        output_dir (str): Directory voor de afbeeldingen
    
    Returns:
        list: Lijst van afbeelding bestanden
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Converteer PDF naar afbeeldingen...")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bestand: {pdf_path}")
    
    try:
        from pdf2image import convert_from_path
        
        # Maak output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Directory gemaakt: {output_dir}")
        
        # Converteer PDF naar afbeeldingen
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Converteer PDF...")
        images = convert_from_path(pdf_path, dpi=300)  # Hoge DPI voor betere kwaliteit
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(images)} pagina's geconverteerd")
        
        image_files = []
        
        # Sla elke pagina op als afbeelding
        for i, image in enumerate(images):
            filename = f"cv_pagina_{i+1:02d}.png"
            filepath = os.path.join(output_dir, filename)
            image.save(filepath, 'PNG')
            image_files.append(filepath)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pagina {i+1} opgeslagen als: {filename}")
        
        return image_files
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout bij converteren: {e}")
        return []

def create_manual_ocr_instructions(image_files):
    """
    Maakt instructies voor handmatige OCR
    """
    print(f"\n{'='*60}")
    print("INSTRUCTIES VOOR HANDMATIGE OCR:")
    print(f"{'='*60}")
    print("1. De PDF is geconverteerd naar afbeeldingen in de 'cv_images' directory")
    print("2. Open elke afbeelding en kopieer de tekst handmatig")
    print("3. Of gebruik een online OCR service zoals:")
    print("   - https://www.onlineocr.net/")
    print("   - https://www.free-online-ocr.com/")
    print("   - https://www.ilovepdf.com/ocr-pdf")
    print("\nAfbeelding bestanden:")
    for i, filepath in enumerate(image_files, 1):
        print(f"   {i}. {filepath}")
    print(f"{'='*60}")

def try_simple_text_extraction(pdf_path):
    """
    Probeer eenvoudige tekst extractie zonder OCR
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Probeer eenvoudige tekst extractie...")
    
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verwerk pagina {page_num + 1}...")
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
            
            if text.strip():
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst gevonden: {len(text)} karakters")
                
                # Sla op
                output_path = "CV_tekst_geëxtraheerd.txt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst opgeslagen naar: {output_path}")
                
                print(f"\n{'='*50}")
                print("GEEXTRACHEERDE TEKST:")
                print(f"{'='*50}")
                print(text)
                print(f"{'='*50}")
                
                return True
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst gevonden")
                return False
                
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout bij tekst extractie: {e}")
        return False

def main():
    """Hoofdfunctie"""
    pdf_path = r"C:\Users\RudoJockinSynergiepr\OneDrive - Synergie PM\Documenten\_GJRoth_CV_omgevingsmanager_senior_def.pdf"
    
    # Controleer of bestand bestaat
    if not os.path.exists(pdf_path):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout: Bestand niet gevonden: {pdf_path}")
        return
    
    # Probeer eerst eenvoudige tekst extractie
    if try_simple_text_extraction(pdf_path):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst succesvol geëxtraheerd!")
        return
    
    # Als dat niet werkt, converteer naar afbeeldingen
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Eenvoudige extractie werkte niet, converteer naar afbeeldingen...")
    
    # Installeer pdf2image als het niet bestaat
    try:
        from pdf2image import convert_from_path
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installeer pdf2image...")
        os.system("pip install pdf2image")
    
    # Converteer PDF naar afbeeldingen
    image_files = convert_pdf_to_images(pdf_path)
    
    if image_files:
        create_manual_ocr_instructions(image_files)
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout bij converteren van PDF naar afbeeldingen")

if __name__ == "__main__":
    main()

