#!/usr/bin/env python3
"""
CV Analyzer - Analyseert PDF bestanden en probeert tekst te extraheren
Gemaakt voor het uitlezen van CV bestanden die als foto's zijn opgeslagen
"""

import sys
import os
from datetime import datetime

def analyze_pdf_structure(pdf_path):
    """
    Analyseert de structuur van een PDF bestand
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Analyseer PDF structuur...")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bestand: {pdf_path}")
    
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PDF informatie:")
            print(f"  - Aantal pagina's: {len(pdf_reader.pages)}")
            print(f"  - PDF versie: {pdf_reader.pdf_version}")
            
            if pdf_reader.metadata:
                print(f"  - Titel: {pdf_reader.metadata.get('title', 'N/A')}")
                print(f"  - Auteur: {pdf_reader.metadata.get('author', 'N/A')}")
                print(f"  - Onderwerp: {pdf_reader.metadata.get('subject', 'N/A')}")
            
            # Analyseer elke pagina
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pagina {page_num + 1} analyse:")
                
                # Probeer verschillende extractie methoden
                methods = [
                    ("Standaard extract_text()", lambda p: p.extract_text()),
                    ("Met visitor", lambda p: p.extract_text(visitor_text=lambda text, cm, tm, fontDict, fontSize: text)),
                ]
                
                for method_name, method_func in methods:
                    try:
                        text = method_func(page)
                        if text and text.strip():
                            print(f"  - {method_name}: {len(text)} karakters gevonden")
                            if len(text) > 50:  # Alleen tonen als er substantiële tekst is
                                print(f"    Eerste 100 karakters: {text[:100]}...")
                        else:
                            print(f"  - {method_name}: Geen tekst gevonden")
                    except Exception as e:
                        print(f"  - {method_name}: Fout - {e}")
                
                # Controleer op afbeeldingen
                try:
                    if '/XObject' in page['/Resources']:
                        xObject = page['/Resources']['/XObject'].get_object()
                        image_count = 0
                        for obj in xObject:
                            if xObject[obj]['/Subtype'] == '/Image':
                                image_count += 1
                        print(f"  - Afbeeldingen gevonden: {image_count}")
                    else:
                        print(f"  - Geen afbeeldingen gevonden")
                except:
                    print(f"  - Kon afbeeldingen niet analyseren")
            
            return True
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout bij analyseren: {e}")
        return False

def try_alternative_extraction(pdf_path):
    """
    Probeer alternatieve extractie methoden
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Probeer alternatieve extractie methoden...")
    
    # Methode 1: Probeer met verschillende PyPDF2 instellingen
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            all_text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                
                # Probeer verschillende extractie methoden
                methods = [
                    page.extract_text,
                    lambda: page.extract_text(visitor_text=lambda text, cm, tm, fontDict, fontSize: text),
                    lambda: page.extract_text(visitor_text=lambda text, cm, tm, fontDict, fontSize: text if text.strip() else ""),
                ]
                
                for method in methods:
                    try:
                        text = method()
                        if text and text.strip():
                            all_text += text + "\n"
                            break
                    except:
                        continue
            
            if all_text.strip():
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst gevonden met alternatieve methoden: {len(all_text)} karakters")
                
                # Sla op
                output_path = "CV_tekst_geëxtraheerd_alternatief.txt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(all_text)
                
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst opgeslagen naar: {output_path}")
                
                print(f"\n{'='*50}")
                print("GEEXTRACHEERDE TEKST:")
                print(f"{'='*50}")
                print(all_text)
                print(f"{'='*50}")
                
                return True
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst gevonden met alternatieve methoden")
                return False
                
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout bij alternatieve extractie: {e}")
        return False

def create_manual_instructions():
    """
    Maakt instructies voor handmatige verwerking
    """
    print(f"\n{'='*60}")
    print("AANBEVELINGEN VOOR HANDMATIGE VERWERKING:")
    print(f"{'='*60}")
    print("Het PDF bestand bevat waarschijnlijk alleen afbeeldingen (gescande document).")
    print("Voor het extraheren van tekst heb je OCR (Optical Character Recognition) nodig.")
    print("\nOpties:")
    print("1. Online OCR services:")
    print("   - https://www.onlineocr.net/")
    print("   - https://www.free-online-ocr.com/")
    print("   - https://www.ilovepdf.com/ocr-pdf")
    print("   - https://www.sodapdf.com/ocr-pdf/")
    print("\n2. Desktop software:")
    print("   - Adobe Acrobat Pro")
    print("   - Microsoft OneNote (kan OCR uitvoeren)")
    print("   - Google Drive (upload PDF, open met Google Docs)")
    print("\n3. Tesseract OCR installeren:")
    print("   - Download van: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   - Installeer en voeg toe aan PATH")
    print("   - Voer dan het OCR script opnieuw uit")
    print(f"{'='*60}")

def main():
    """Hoofdfunctie"""
    pdf_path = r"C:\Users\RudoJockinSynergiepr\OneDrive - Synergie PM\Documenten\_GJRoth_CV_omgevingsmanager_senior_def.pdf"
    
    # Controleer of bestand bestaat
    if not os.path.exists(pdf_path):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout: Bestand niet gevonden: {pdf_path}")
        return
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CV PDF Analyzer gestart...")
    
    # Analyseer PDF structuur
    if analyze_pdf_structure(pdf_path):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PDF analyse voltooid")
    
    # Probeer alternatieve extractie
    if try_alternative_extraction(pdf_path):
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst succesvol geëxtraheerd!")
    else:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst kon worden geëxtraheerd")
        create_manual_instructions()

if __name__ == "__main__":
    main()

