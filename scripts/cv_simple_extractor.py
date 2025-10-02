#!/usr/bin/env python3
"""
CV Simple Text Extractor - Eenvoudige PDF tekst extractie
Gemaakt voor het uitlezen van CV bestanden
"""

import sys
import os
from datetime import datetime

def try_pdf_extraction():
    """Probeer verschillende PDF extractie methoden"""
    
    pdf_path = r"C:\Users\RudoJockinSynergiepr\OneDrive - Synergie PM\Documenten\_GJRoth_CV_omgevingsmanager_senior_def.pdf"
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PDF tekst extractie gestart...")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bestand: {pdf_path}")
    
    # Controleer of bestand bestaat
    if not os.path.exists(pdf_path):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout: Bestand niet gevonden: {pdf_path}")
        return ""
    
    # Methode 1: Probeer PyPDF2
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Probeer PyPDF2...")
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
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst gevonden met PyPDF2: {len(text)} karakters")
                return text
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst gevonden met PyPDF2")
                
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PyPDF2 niet beschikbaar")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PyPDF2 fout: {e}")
    
    # Methode 2: Probeer pdfplumber
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Probeer pdfplumber...")
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            
            for page_num, page in enumerate(pdf.pages):
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verwerk pagina {page_num + 1}...")
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if text.strip():
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst gevonden met pdfplumber: {len(text)} karakters")
                return text
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst gevonden met pdfplumber")
                
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] pdfplumber niet beschikbaar")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] pdfplumber fout: {e}")
    
    # Methode 3: Probeer pymupdf
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Probeer pymupdf...")
        import fitz
        
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verwerk pagina {page_num + 1}...")
            page = doc.load_page(page_num)
            page_text = page.get_text()
            text += page_text + "\n"
        
        doc.close()
        
        if text.strip():
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst gevonden met pymupdf: {len(text)} karakters")
            return text
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst gevonden met pymupdf")
            
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] pymupdf niet beschikbaar")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] pymupdf fout: {e}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen van de methoden werkte. Het PDF bevat mogelijk alleen afbeeldingen.")
    return ""

def main():
    """Hoofdfunctie"""
    # Installeer eerst PyPDF2 als het niet bestaat
    try:
        import PyPDF2
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installeer PyPDF2...")
        os.system("pip install PyPDF2")
    
    # Probeer tekst extractie
    extracted_text = try_pdf_extraction()
    
    if extracted_text and extracted_text.strip():
        # Sla op naar bestand
        output_path = "CV_tekst_geëxtraheerd.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        print(f"\n{'='*50}")
        print("GEEXTRACHEERDE TEKST:")
        print(f"{'='*50}")
        print(extracted_text)
        print(f"{'='*50}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst opgeslagen naar: {output_path}")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst geëxtraheerd uit het PDF bestand.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Dit kan betekenen dat het PDF alleen afbeeldingen bevat.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Voor OCR is extra software nodig (Tesseract).")

if __name__ == "__main__":
    main()

