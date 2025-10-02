#!/usr/bin/env python3
"""
Debug script to test name extraction from filename
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_name_extraction():
    """Test name extraction from filename"""
    filename = 'CV Ray Amat 2025.docx'
    
    print(f"Testing filename: {filename}")
    
    # Remove file extension
    name_part = filename.replace('.docx', '').replace('.pdf', '').replace('.doc', '')
    print(f"After removing extension: {name_part}")
    
    # Remove common CV prefixes
    prefixes = ['CV', 'cv', 'Resume', 'resume', 'Resumé', 'resumé']
    for prefix in prefixes:
        if name_part.startswith(prefix):
            name_part = name_part[len(prefix):].strip()
            print(f"After removing prefix '{prefix}': {name_part}")
            break
    
    # Remove year patterns
    import re
    name_part = re.sub(r'\s*\d{4}\s*$', '', name_part).strip()
    print(f"After removing year: {name_part}")
    
    # Clean up name
    name_part = name_part.replace('_', ' ').replace('-', ' ').strip()
    print(f"After cleaning: {name_part}")
    
    # Check if it looks like a name
    def is_likely_name(text):
        if not text or len(text) < 3 or len(text) > 50:
            return False
        
        if not re.search(r'[A-Za-z]', text):
            return False
        
        if re.search(r'\d', text):
            return False
        
        cv_words = ['cv', 'resume', 'curriculum', 'vitae', 'werkervaring', 'opleiding',
                   'vaardigheden', 'experience', 'education', 'skills']
        if any(word in text.lower() for word in cv_words):
            return False
        
        if text.isupper() and len(text) > 10:
            return False
        
        words = text.split()
        if len(words) < 1 or len(words) > 4:
            return False
        
        return True
    
    is_name = is_likely_name(name_part)
    print(f"Is likely name: {is_name}")
    
    if is_name:
        print(f"✅ Successfully extracted name: '{name_part}'")
    else:
        print(f"❌ Failed to extract valid name from: '{name_part}'")

if __name__ == "__main__":
    test_name_extraction()
