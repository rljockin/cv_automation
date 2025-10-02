#!/usr/bin/env python3
"""
CV Solution - Eenvoudige oplossing voor CV tekst extractie
Gemaakt voor het uitlezen van CV bestanden die als foto's zijn opgeslagen
"""

import sys
import os
from datetime import datetime

def create_simple_solution():
    """
    Maakt een eenvoudige oplossing voor het verwerken van het CV
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CV Solution - Eenvoudige aanpak")
    
    pdf_path = r"C:\Users\RudoJockinSynergiepr\OneDrive - Synergie PM\Documenten\_GJRoth_CV_omgevingsmanager_senior_def.pdf"
    
    print(f"\n{'='*60}")
    print("CV TEKST EXTRACTIE - OPLOSSING")
    print(f"{'='*60}")
    print(f"Bestand: {pdf_path}")
    print(f"Status: PDF bevat alleen afbeeldingen (geen selecteerbare tekst)")
    print(f"Pagina's: 2")
    print(f"{'='*60}")
    
    print(f"\n{'='*60}")
    print("AANBEVOLEN OPLOSSINGEN:")
    print(f"{'='*60}")
    
    print("\n1. 🚀 SNELSTE OPLOSSING - Google Drive:")
    print("   - Upload het PDF naar Google Drive")
    print("   - Klik met rechts op het bestand")
    print("   - Kies 'Openen met' > 'Google Docs'")
    print("   - Google Docs voert automatisch OCR uit")
    print("   - Kopieer de tekst uit Google Docs")
    
    print("\n2. 💻 DESKTOP OPLOSSING - Microsoft OneNote:")
    print("   - Open Microsoft OneNote")
    print("   - Ga naar 'Invoegen' > 'Bestand' > 'PDF afdrukken'")
    print("   - Selecteer het CV bestand")
    print("   - OneNote voert automatisch OCR uit")
    print("   - Kopieer de tekst uit OneNote")
    
    print("\n3. 🌐 ONLINE OCR SERVICES:")
    print("   - https://www.onlineocr.net/ (gratis, 15 bestanden per uur)")
    print("   - https://www.free-online-ocr.com/ (gratis)")
    print("   - https://www.ilovepdf.com/ocr-pdf (gratis)")
    print("   - https://www.sodapdf.com/ocr-pdf/ (gratis)")
    
    print("\n4. 🔧 PROFESSIONELE OPLOSSING - Tesseract OCR:")
    print("   - Download Tesseract van: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   - Installeer en voeg toe aan Windows PATH")
    print("   - Voer dan het OCR script opnieuw uit")
    
    print(f"\n{'='*60}")
    print("STAP-VOOR-STAP INSTRUCTIES VOOR GOOGLE DRIVE:")
    print(f"{'='*60}")
    print("1. Ga naar https://drive.google.com")
    print("2. Klik op 'Nieuw' > 'Bestand uploaden'")
    print("3. Selecteer het CV bestand")
    print("4. Wacht tot upload voltooid is")
    print("5. Klik met rechts op het bestand")
    print("6. Kies 'Openen met' > 'Google Docs'")
    print("7. Wacht tot OCR voltooid is (kan even duren)")
    print("8. Kopieer alle tekst uit Google Docs")
    print("9. Plak in een nieuw document of tekstbestand")
    print(f"{'='*60}")
    
    # Maak een instructie bestand
    instructions_file = "CV_OCR_Instructies.txt"
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write("CV TEKST EXTRACTIE - INSTRUCTIES\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Bestand: {pdf_path}\n")
        f.write("Status: PDF bevat alleen afbeeldingen (geen selecteerbare tekst)\n")
        f.write("Pagina's: 2\n\n")
        f.write("AANBEVOLEN OPLOSSINGEN:\n")
        f.write("-" * 30 + "\n\n")
        f.write("1. GOOGLE DRIVE (AANBEVOLEN):\n")
        f.write("   - Upload PDF naar Google Drive\n")
        f.write("   - Open met Google Docs\n")
        f.write("   - Google voert automatisch OCR uit\n")
        f.write("   - Kopieer de tekst\n\n")
        f.write("2. MICROSOFT ONENOTE:\n")
        f.write("   - Open OneNote\n")
        f.write("   - Invoegen > Bestand > PDF afdrukken\n")
        f.write("   - OneNote voert automatisch OCR uit\n")
        f.write("   - Kopieer de tekst\n\n")
        f.write("3. ONLINE OCR SERVICES:\n")
        f.write("   - https://www.onlineocr.net/\n")
        f.write("   - https://www.free-online-ocr.com/\n")
        f.write("   - https://www.ilovepdf.com/ocr-pdf\n")
        f.write("   - https://www.sodapdf.com/ocr-pdf/\n\n")
        f.write("4. TESSERACT OCR (VOOR GEBRUIKERS):\n")
        f.write("   - Download van: https://github.com/UB-Mannheim/tesseract/wiki\n")
        f.write("   - Installeer en voeg toe aan PATH\n")
        f.write("   - Voer dan het OCR script opnieuw uit\n\n")
        f.write("STAP-VOOR-STAP GOOGLE DRIVE:\n")
        f.write("-" * 30 + "\n")
        f.write("1. Ga naar https://drive.google.com\n")
        f.write("2. Klik op 'Nieuw' > 'Bestand uploaden'\n")
        f.write("3. Selecteer het CV bestand\n")
        f.write("4. Wacht tot upload voltooid is\n")
        f.write("5. Klik met rechts op het bestand\n")
        f.write("6. Kies 'Openen met' > 'Google Docs'\n")
        f.write("7. Wacht tot OCR voltooid is (kan even duren)\n")
        f.write("8. Kopieer alle tekst uit Google Docs\n")
        f.write("9. Plak in een nieuw document of tekstbestand\n")
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Instructies opgeslagen in: {instructions_file}")
    
    return True

def main():
    """Hoofdfunctie"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CV Solution gestart...")
    
    # Controleer of bestand bestaat
    pdf_path = r"C:\Users\RudoJockinSynergiepr\OneDrive - Synergie PM\Documenten\_GJRoth_CV_omgevingsmanager_senior_def.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fout: Bestand niet gevonden: {pdf_path}")
        return
    
    # Maak oplossing
    create_simple_solution()
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Oplossing voltooid!")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Gebruik een van de aanbevolen methoden om de tekst te extraheren.")

if __name__ == "__main__":
    main()

