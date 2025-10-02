#!/usr/bin/env python3
"""
CV Text Extractor v2 - Extraheert tekst uit PDF bestanden
Gemaakt voor het uitlezen van CV bestanden die als foto's zijn opgeslagen
"""

import pdfplumber
import sys
import os
from datetime import datetime

def extract_text_from_pdf(pdf_path, output_path=None):
    """
    Extraheert tekst uit een PDF bestand
    
    Args:
        pdf_path (str): Pad naar het PDF bestand
        output_path (str): Pad voor het output tekstbestand (optioneel)
    
    Returns:
        str: Geëxtraheerde tekst
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PDF tekst extractie gestart...")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bestand: {pdf_path}")
    
    try:
        all_text = []
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PDF heeft {len(pdf.pages)} pagina's")
            
            # Loop door alle pagina's
            for page_num, page in enumerate(pdf.pages):
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verwerk pagina {page_num + 1}...")
                
                # Probeer tekst extractie
                text = page.extract_text()
                
                if text:
                    all_text.append(text)
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst gevonden op pagina {page_num + 1}: {len(text)} karakters")
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst gevonden op pagina {page_num + 1}")
                    
                    # Probeer tabellen te extraheren
                    tables = page.extract_tables()
                    if tables:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(tables)} tabel(len) gevonden op pagina {page_num + 1}")
                        for table in tables:
                            for row in table:
                                if row:
                                    row_text = " | ".join([cell for cell in row if cell])
                                    if row_text.strip():
                                        all_text.append(row_text)
        
        # Combineer alle tekst
        full_text = "\n".join(all_text)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tekst extractie voltooid!")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Totaal aantal karakters: {len(full_text)}")
        
        # Sla op naar bestand als output_path is opgegeven
        if output_path and full_text.strip():
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
    
    if extracted_text and extracted_text.strip():
        print(f"\n{'='*50}")
        print("GEEXTRACHEERDE TEKST:")
        print(f"{'='*50}")
        print(extracted_text)
        print(f"{'='*50}")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Geen tekst geëxtraheerd uit het PDF bestand.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Dit kan betekenen dat het PDF alleen afbeeldingen bevat.")

if __name__ == "__main__":
    main()

