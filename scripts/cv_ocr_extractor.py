#!/usr/bin/env python3
"""
CV OCR Text Extractor - Extraheert tekst uit PDF met OCR
Gemaakt voor het uitlezen van CV bestanden die als foto's zijn opgeslagen
"""

import sys
import os
from datetime import datetime

def install_required_packages():
    """Installeer benodigde packages"""
    packages = [
        "PyPDF2",
        "pdf2image", 
        "pytesseract",
        "Pillow"
    ]
    
    for package in packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {package} is al geïnstalleerd")
        except ImportError:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installeer {package}...")
            os.system(f"pip install {package}")

def extract_text_with_ocr(pdf_path, output_path=None):
    """
    Extraheert tekst uit een PDF bestand met OCR
    
    Args:
        pdf_path (str): Pad naar het PDF bestand
        output_path (str): Pad voor het output tekstbestand (optioneel)
    
    Returns:
        str: Geëxtraheerde tekst
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PDF OCR extractie gestart...")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bestand: {pdf_path}")
    
    try:
        # Import benodigde modules
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image
        
        # Converteer PDF naar afbeeldingen
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Converteer PDF naar afbeeldingen...")
        images = convert_from_path(pdf_path, dpi=300)  # Hoge DPI voor betere OCR
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(images)} pagina's geconverteerd")
        
        all_text = []
        
        # Voer OCR uit op elke afbeelding
        for i, image in enumerate(images):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OCR op pagina {i + 1}...")
            
            # Voer OCR uit
            text = pytesseract.image_to_string(image, lang='nld+eng')  # Nederlands en Engels
            
            if text.strip():
                all_text.append(f"--- PAGINA {i + 1} ---\n{text}\n")
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst gevonden op pagina {i + 1}: {len(text)} karakters")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst gevonden op pagina {i + 1}")
        
        # Combineer alle tekst
        full_text = "\n".join(all_text)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OCR extractie voltooid!")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Totaal aantal karakters: {len(full_text)}")
        
        # Sla op naar bestand als output_path is opgegeven
        if output_path and full_text.strip():
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst opgeslagen naar: {output_path}")
        
        return full_text
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout bij OCR: {e}")
        return ""

def alternative_ocr_method(pdf_path, output_path=None):
    """
    Alternatieve OCR methode zonder Tesseract
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Probeer alternatieve OCR methode...")
    
    try:
        # Probeer met een online OCR service of andere methode
        # Voor nu, probeer de PDF opnieuw met verschillende instellingen
        
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verwerk pagina {page_num + 1} met alternatieve methode...")
                page = pdf_reader.pages[page_num]
                
                # Probeer verschillende extractie methoden
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except:
                    pass
                
                # Probeer ook met andere parameters
                try:
                    page_text = page.extract_text(visitor_text=lambda text, cm, tm, fontDict, fontSize: text)
                    if page_text:
                        text += page_text + "\n"
                except:
                    pass
            
            if text.strip():
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst gevonden met alternatieve methode: {len(text)} karakters")
                
                if output_path:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst opgeslagen naar: {output_path}")
                
                return text
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst gevonden met alternatieve methode")
                return ""
                
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout bij alternatieve methode: {e}")
        return ""

def main():
    """Hoofdfunctie"""
    pdf_path = r"C:\Users\RudoJockinSynergiepr\OneDrive - Synergie PM\Documenten\_GJRoth_CV_omgevingsmanager_senior_def.pdf"
    
    # Controleer of bestand bestaat
    if not os.path.exists(pdf_path):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout: Bestand niet gevonden: {pdf_path}")
        return
    
    # Installeer benodigde packages
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Controleer en installeer benodigde packages...")
    install_required_packages()
    
    # Maak output bestandsnaam
    output_path = "CV_tekst_geëxtraheerd_OCR.txt"
    
    # Probeer eerst OCR
    extracted_text = extract_text_with_ocr(pdf_path, output_path)
    
    # Als OCR niet werkt, probeer alternatieve methode
    if not extracted_text or not extracted_text.strip():
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OCR werkte niet, probeer alternatieve methode...")
        extracted_text = alternative_ocr_method(pdf_path, output_path)
    
    if extracted_text and extracted_text.strip():
        print(f"\n{'='*50}")
        print("GEEXTRACHEERDE TEKST:")
        print(f"{'='*50}")
        print(extracted_text)
        print(f"{'='*50}")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst geëxtraheerd uit het PDF bestand.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Het PDF bevat mogelijk alleen afbeeldingen die OCR vereisen.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Voor betere OCR resultaten is Tesseract OCR software nodig.")

if __name__ == "__main__":
    main()

