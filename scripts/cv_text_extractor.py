#!/usr/bin/env python3
"""
CV Text Extractor - Extraheert tekst uit PDF bestanden met OCR
Gemaakt voor het uitlezen van CV bestanden die als foto's zijn opgeslagen
"""

import fitz  # PyMuPDF
import sys
import os
from datetime import datetime

def extract_text_from_pdf(pdf_path, output_path=None):
    """
    Extraheert tekst uit een PDF bestand met behulp van OCR
    
    Args:
        pdf_path (str): Pad naar het PDF bestand
        output_path (str): Pad voor het output tekstbestand (optioneel)
    
    Returns:
        str: Geëxtraheerde tekst
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PDF tekst extractie gestart...")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bestand: {pdf_path}")
    
    try:
        # Open het PDF bestand
        doc = fitz.open(pdf_path)
        all_text = []
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PDF heeft {len(doc)} pagina's")
        
        # Loop door alle pagina's
        for page_num in range(len(doc)):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verwerk pagina {page_num + 1}...")
            
            page = doc.load_page(page_num)
            
            # Probeer eerst gewone tekst extractie
            text = page.get_text()
            
            # Als er weinig tekst is, probeer OCR
            if len(text.strip()) < 50:  # Als er minder dan 50 karakters zijn
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Weinig tekst gevonden, probeer OCR...")
                
                # Converteer pagina naar afbeelding
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom voor betere OCR kwaliteit
                pix = page.get_pixmap(matrix=mat)
                
                # Probeer OCR met PyMuPDF's ingebouwde OCR
                try:
                    # Dit vereist dat Tesseract geïnstalleerd is
                    ocr_text = page.get_text("dict")
                    if ocr_text and len(ocr_text.get('blocks', [])) > 0:
                        # Verwerk de OCR resultaten
                        for block in ocr_text.get('blocks', []):
                            if 'lines' in block:
                                for line in block['lines']:
                                    line_text = ""
                                    for span in line.get('spans', []):
                                        line_text += span.get('text', '')
                                    if line_text.strip():
                                        all_text.append(line_text.strip())
                except Exception as e:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OCR fout: {e}")
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Gebruik standaard tekst extractie...")
                    all_text.append(text)
            else:
                all_text.append(text)
        
        doc.close()
        
        # Combineer alle tekst
        full_text = "\n".join(all_text)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst extractie voltooid!")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Totaal aantal karakters: {len(full_text)}")
        
        # Sla op naar bestand als output_path is opgegeven
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst opgeslagen naar: {output_path}")
        
        return full_text
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout bij verwerken PDF: {e}")
        return ""

def main():
    """Hoofdfunctie"""
    pdf_path = r"C:\Users\RudoJockinSynergiepr\OneDrive - Synergie PM\Documenten\_GJRoth_CV_omgevingsmanager_senior_def.pdf"
    
    # Controleer of bestand bestaat
    if not os.path.exists(pdf_path):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout: Bestand niet gevonden: {pdf_path}")
        return
    
    # Maak output bestandsnaam
    output_path = "CV_tekst_geëxtraheerd.txt"
    
    # Extraheer tekst
    extracted_text = extract_text_from_pdf(pdf_path, output_path)
    
    if extracted_text:
        print(f"\n{'='*50}")
        print("GEEXTRACHEERDE TEKST:")
        print(f"{'='*50}")
        print(extracted_text)
        print(f"{'='*50}")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst geëxtraheerd uit het PDF bestand.")

if __name__ == "__main__":
    main()

