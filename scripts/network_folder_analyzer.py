#!/usr/bin/env python3
"""
Network Folder Analyzer - Scans and analyzes CV vs Resumé files
Distinguishes between raw CVs and processed Resumés in the Network folder
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import re
from collections import defaultdict

def scan_network_folder(base_path):
    """
    Scans the Network folder and categorizes files
    
    Args:
        base_path (str): Path to the Network folder
        
    Returns:
        dict: Categorized file information
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning Network folder...")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Base path: {base_path}")
    
    stats = {
        'total_folders': 0,
        'total_files': 0,
        'resumes_synergie': [],
        'raw_cvs': [],
        'other_files': [],
        'people_with_both': [],
        'people_with_only_cv': [],
        'people_with_only_resume': [],
    }
    
    # Pattern for processed Resumés
    resume_pattern = re.compile(r'Resum[eé]_Synergie', re.IGNORECASE)
    cv_pattern = re.compile(r'^CV[_ ]', re.IGNORECASE)
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(base_path):
        # Skip the template folder
        if 'STANDAARD RESUME' in root:
            continue
            
        stats['total_folders'] += len(dirs)
        
        # Get person's name from folder
        rel_path = os.path.relpath(root, base_path)
        
        # Check for files in this folder
        person_cvs = []
        person_resumes = []
        
        for file in files:
            if not file.lower().endswith(('.pdf', '.docx', '.doc')):
                continue
                
            stats['total_files'] += 1
            full_path = os.path.join(root, file)
            
            # Categorize file
            if resume_pattern.search(file):
                stats['resumes_synergie'].append({
                    'path': full_path,
                    'filename': file,
                    'person': rel_path,
                    'extension': os.path.splitext(file)[1]
                })
                person_resumes.append(file)
            elif cv_pattern.search(file):
                stats['raw_cvs'].append({
                    'path': full_path,
                    'filename': file,
                    'person': rel_path,
                    'extension': os.path.splitext(file)[1]
                })
                person_cvs.append(file)
            else:
                stats['other_files'].append({
                    'path': full_path,
                    'filename': file,
                    'person': rel_path,
                    'extension': os.path.splitext(file)[1]
                })
        
        # Check if person has both CV and Resume
        if person_cvs and person_resumes and rel_path != '.':
            stats['people_with_both'].append({
                'person': rel_path,
                'cvs': person_cvs,
                'resumes': person_resumes
            })
        elif person_cvs and not person_resumes and rel_path != '.':
            stats['people_with_only_cv'].append({
                'person': rel_path,
                'cvs': person_cvs
            })
        elif person_resumes and not person_cvs and rel_path != '.':
            stats['people_with_only_resume'].append({
                'person': rel_path,
                'resumes': person_resumes
            })
    
    return stats

def print_statistics(stats):
    """Print scan statistics"""
    print(f"\n{'='*70}")
    print("NETWORK FOLDER SCAN RESULTS")
    print(f"{'='*70}")
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  - Total folders scanned: {stats['total_folders']}")
    print(f"  - Total document files: {stats['total_files']}")
    print(f"  - Processed Resumés (Resumé_Synergie pattern): {len(stats['resumes_synergie'])}")
    print(f"  - Raw CVs (CV_ pattern): {len(stats['raw_cvs'])}")
    print(f"  - Other files: {len(stats['other_files'])}")
    
    print(f"\n👥 PEOPLE CATEGORIZATION:")
    print(f"  - People with BOTH CV and Resumé: {len(stats['people_with_both'])}")
    print(f"  - People with ONLY CV (not processed): {len(stats['people_with_only_cv'])}")
    print(f"  - People with ONLY Resumé (processed): {len(stats['people_with_only_resume'])}")
    
    # File extensions breakdown
    resume_extensions = defaultdict(int)
    cv_extensions = defaultdict(int)
    
    for resume in stats['resumes_synergie']:
        resume_extensions[resume['extension']] += 1
    
    for cv in stats['raw_cvs']:
        cv_extensions[cv['extension']] += 1
    
    print(f"\n📄 FILE FORMAT BREAKDOWN:")
    print(f"\n  Resumé_Synergie files by format:")
    for ext, count in sorted(resume_extensions.items()):
        print(f"    {ext}: {count}")
    
    print(f"\n  Raw CV files by format:")
    for ext, count in sorted(cv_extensions.items()):
        print(f"    {ext}: {count}")
    
    # Show examples of people with both
    print(f"\n📋 SAMPLE: People with BOTH CV and Resumé (first 10):")
    for i, person in enumerate(stats['people_with_both'][:10], 1):
        print(f"\n  {i}. {person['person']}")
        print(f"     CVs: {', '.join(person['cvs'][:2])}")
        print(f"     Resumés: {', '.join(person['resumes'][:2])}")
    
    print(f"\n⚠️  UNPROCESSED: People with ONLY CV (first 20):")
    for i, person in enumerate(stats['people_with_only_cv'][:20], 1):
        print(f"  {i}. {person['person']}")

def analyze_file_naming_patterns(stats):
    """Analyze naming patterns in Resumé files"""
    print(f"\n{'='*70}")
    print("NAMING PATTERN ANALYSIS")
    print(f"{'='*70}")
    
    resume_patterns = defaultdict(int)
    
    for resume in stats['resumes_synergie']:
        filename = resume['filename']
        # Extract pattern (Resumé vs Resume, with/without accent)
        if 'Resumé_Synergie' in filename:
            resume_patterns['Resumé_Synergie (with é)'] += 1
        elif 'Resume_Synergie' in filename:
            resume_patterns['Resume_Synergie (no accent)'] += 1
        else:
            resume_patterns['Other'] += 1
    
    print(f"\n📝 RESUMÉ NAMING PATTERNS:")
    for pattern, count in sorted(resume_patterns.items(), key=lambda x: -x[1]):
        print(f"  {pattern}: {count}")
    
    # Analyze typical naming structure
    print(f"\n📝 TYPICAL RESUMÉ NAMING STRUCTURE:")
    sample_resumes = [r['filename'] for r in stats['resumes_synergie'][:5]]
    for i, name in enumerate(sample_resumes, 1):
        print(f"  {i}. {name}")

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using PyPDF2
    
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
            
            for page_num in range(min(3, len(pdf_reader.pages))):  # First 3 pages only
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text + "\n"
            
            return text.strip()
    except Exception as e:
        return f"Error extracting text: {e}"

def compare_cv_vs_resume(stats):
    """Compare actual content of CV vs Resumé files"""
    print(f"\n{'='*70}")
    print("CONTENT COMPARISON: CV vs RESUMÉ")
    print(f"{'='*70}")
    
    # Find people with both CV and Resume for direct comparison
    if not stats['people_with_both']:
        print("No people found with both CV and Resumé for comparison.")
        return
    
    # Try to install PyPDF2 if not available
    try:
        import PyPDF2
    except ImportError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installing PyPDF2...")
        os.system("pip install PyPDF2 -q")
        import PyPDF2
    
    # Pick first person with both PDF files
    for person_data in stats['people_with_both'][:5]:  # Try first 5
        person = person_data['person']
        
        # Find PDF files
        cv_pdf = None
        resume_pdf = None
        
        for cv in person_data['cvs']:
            if cv.endswith('.pdf'):
                cv_pdf = cv
                break
        
        for resume in person_data['resumes']:
            if resume.endswith('.pdf'):
                resume_pdf = resume
                break
        
        if not cv_pdf or not resume_pdf:
            continue
        
        print(f"\n🔍 COMPARING: {person}")
        print(f"{'─'*70}")
        
        base_path = r"C:\Users\RudoJockinSynergiepr\Synergie PM\Netwerk - Documenten"
        cv_full_path = os.path.join(base_path, person, cv_pdf)
        resume_full_path = os.path.join(base_path, person, resume_pdf)
        
        print(f"\n📄 RAW CV: {cv_pdf}")
        print(f"Path: {cv_full_path}")
        print(f"File size: {os.path.getsize(cv_full_path) / 1024:.1f} KB")
        
        cv_text = extract_text_from_pdf(cv_full_path)
        if cv_text and len(cv_text) > 50:
            print(f"Text length: {len(cv_text)} characters")
            print(f"First 500 characters:")
            print(f"{cv_text[:500]}...")
        else:
            print("⚠️  No text extracted (likely image-based PDF)")
        
        print(f"\n📋 PROCESSED RESUMÉ: {resume_pdf}")
        print(f"Path: {resume_full_path}")
        print(f"File size: {os.path.getsize(resume_full_path) / 1024:.1f} KB")
        
        resume_text = extract_text_from_pdf(resume_full_path)
        if resume_text and len(resume_text) > 50:
            print(f"Text length: {len(resume_text)} characters")
            print(f"First 500 characters:")
            print(f"{resume_text[:500]}...")
        else:
            print("⚠️  No text extracted (likely image-based PDF)")
        
        print(f"\n{'─'*70}")
        
        # Only compare one person for now
        break

def save_report(stats, output_file="network_folder_analysis_report.txt"):
    """Save analysis report to file"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saving report to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("NETWORK FOLDER ANALYSIS REPORT\n")
        f.write("=" * 70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total folders scanned: {stats['total_folders']}\n")
        f.write(f"Total document files: {stats['total_files']}\n")
        f.write(f"Processed Resumés: {len(stats['resumes_synergie'])}\n")
        f.write(f"Raw CVs: {len(stats['raw_cvs'])}\n")
        f.write(f"Other files: {len(stats['other_files'])}\n\n")
        
        f.write("PEOPLE CATEGORIZATION\n")
        f.write("-" * 70 + "\n")
        f.write(f"People with BOTH: {len(stats['people_with_both'])}\n")
        f.write(f"People with ONLY CV: {len(stats['people_with_only_cv'])}\n")
        f.write(f"People with ONLY Resumé: {len(stats['people_with_only_resume'])}\n\n")
        
        f.write("PEOPLE WITH ONLY CV (UNPROCESSED)\n")
        f.write("-" * 70 + "\n")
        for person in stats['people_with_only_cv']:
            f.write(f"{person['person']}\n")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Report saved successfully!")

def main():
    """Main function"""
    base_path = r"C:\Users\RudoJockinSynergiepr\Synergie PM\Netwerk - Documenten"
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Network Folder Analyzer started...")
    
    # Check if path exists
    if not os.path.exists(base_path):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: Path not found: {base_path}")
        return
    
    # Scan the network folder
    stats = scan_network_folder(base_path)
    
    # Print statistics
    print_statistics(stats)
    
    # Analyze naming patterns
    analyze_file_naming_patterns(stats)
    
    # Compare CV vs Resume content
    compare_cv_vs_resume(stats)
    
    # Save report
    save_report(stats)
    
    print(f"\n{'='*70}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Analysis complete!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

