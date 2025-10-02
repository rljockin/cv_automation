#!/usr/bin/env python3
"""
Personal Info Parser - Extract personal information from CV
Extracts name, location, birth year, contact details, and other personal data
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.core import Language, clean_text, extract_name_components


@dataclass
class PersonalInfo:
    """Personal information extracted from CV"""
    full_name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    location: Optional[str]
    birth_year: Optional[int]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    nationality: Optional[str]
    driver_license: Optional[str]
    address: Optional[str]
    postal_code: Optional[str]
    city: Optional[str]
    confidence: float
    language: Language


class PersonalInfoParser:
    """
    Extract personal information from CV text
    
    Handles:
    - Name extraction (various formats)
    - Location extraction (Dutch cities, countries)
    - Contact information (phone, email, website)
    - Birth year detection
    - Address parsing
    - Nationality detection
    - Driver's license information
    
    Strategy:
    1. Look for personal info section first
    2. Extract from document header/top
    3. Use regex patterns for specific data types
    4. Validate and clean extracted data
    """
    
    def __init__(self):
        """Initialize personal info parser with patterns"""
        
        # Dutch cities and regions
        self.dutch_cities = {
            'amsterdam', 'rotterdam', 'den haag', 'utrecht', 'eindhoven', 'tilburg',
            'groningen', 'almere', 'breda', 'nijmegen', 'enschede', 'haarlem',
            'arnhem', 'zaandam', 'amersfoort', 'apeldoorn', 'hoofddorp', 'maastricht',
            'leiden', 'dordrecht', 'zoetermeer', 'zwolle', 'ede', 'emmen', 'westland',
            'delft', 'venlo', 'deventer', 'leeuwarden', 'alkmaar', 'sittard-geleen',
            'helmond', 'purmerend', 'schiedam', 'amstelveen', 'vlaardingen', 'zaanstad',
            'hoorn', 'hardenberg', 'bergschenhoek', 'capelle aan den ijssel', 'ijsselstein',
            'nijkerk', 'rijswijk', 'spijkenisse', 'veenendaal', 'vlaardingen', 'weert',
            'zoetermeer', 'zwijndrecht'
        }
        
        # Countries
        self.countries = {
            'nederland', 'netherlands', 'belgië', 'belgium', 'duitsland', 'germany',
            'frankrijk', 'france', 'engeland', 'england', 'verenigd koninkrijk',
            'united kingdom', 'spanje', 'spain', 'italië', 'italy', 'portugal',
            'polen', 'poland', 'tsjechië', 'czech republic', 'hongarije', 'hungary',
            'roemenië', 'romania', 'bulgarije', 'bulgaria', 'griekenland', 'greece',
            'turkiye', 'turkey', 'marokko', 'morocco', 'suriname', 'indonesië',
            'indonesia', 'china', 'india', 'brazilië', 'brazil', 'argentinië',
            'argentina', 'canada', 'australië', 'australia', 'nieuw zeeland',
            'new zealand', 'verenigde staten', 'united states', 'usa'
        }
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for personal info extraction"""
        
        # Email pattern
        self.pattern_email = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone patterns
        self.pattern_phone_dutch = re.compile(
            r'\b(?:\+31\s?)?(?:0\s?)?[1-9]\d{1,2}[- ]?\d{6,7}\b'
        )
        self.pattern_phone_international = re.compile(
            r'\b\+?\d{1,3}[- ]?\d{2,4}[- ]?\d{2,4}[- ]?\d{2,4}\b'
        )
        
        # Website patterns
        self.pattern_website = re.compile(
            r'\b(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b'
        )
        
        # Dutch postal code pattern
        self.pattern_postal_code = re.compile(r'\b\d{4}\s*[A-Z]{2}\b')
        
        # Birth year pattern
        self.pattern_birth_year = re.compile(
            r'\b(?:geboren|born|geboortedatum|birth\s*date|geb\.|b\.)\s*:?\s*(?:in\s*)?(19\d{2}|20[0-1]\d)\b',
            re.IGNORECASE
        )
        
        # Driver's license pattern
        self.pattern_driver_license = re.compile(
            r'\b(?:rijbewijs|driver\s*license|driving\s*license)\s*:?\s*([A-Z])\b',
            re.IGNORECASE
        )
        
        # Nationality pattern
        self.pattern_nationality = re.compile(
            r'\b(?:nationaliteit|nationality)\s*:?\s*([A-Za-z\s]+?)(?:\n|$|,|\s{2,})',
            re.IGNORECASE
        )
    
    def parse_personal_info(self, text: str, language: Language = Language.UNKNOWN) -> PersonalInfo:
        """
        Parse personal information from CV text
        
        Args:
            text: Raw CV text
            language: Detected language
            
        Returns:
            PersonalInfo object with extracted data
        """
        if not text:
            return self._create_empty_info()
        
        # Clean text
        text = clean_text(text)
        
        # Extract different types of information
        full_name = self._extract_name(text)
        first_name, last_name = extract_name_components(full_name) if full_name else (None, None)
        
        location = self._extract_location(text)
        birth_year = self._extract_birth_year(text)
        phone = self._extract_phone(text)
        email = self._extract_email(text)
        website = self._extract_website(text)
        nationality = self._extract_nationality(text)
        driver_license = self._extract_driver_license(text)
        address, postal_code, city = self._extract_address(text)
        
        # Calculate confidence
        confidence = self._calculate_confidence({
            'name': full_name,
            'location': location,
            'phone': phone,
            'email': email,
            'birth_year': birth_year
        })
        
        return PersonalInfo(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            location=location,
            birth_year=birth_year,
            phone=phone,
            email=email,
            website=website,
            nationality=nationality,
            driver_license=driver_license,
            address=address,
            postal_code=postal_code,
            city=city,
            confidence=confidence,
            language=language
        )
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract full name from text"""
        
        # Look for name patterns in the first few lines
        lines = text.split('\n')[:10]  # Check first 10 lines
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip lines that look like headers or sections
            if re.match(r'^[A-Z\s]+$', line) and len(line) > 20:
                continue
            
            # Skip lines with common CV words
            if any(word in line.lower() for word in ['cv', 'resume', 'curriculum', 'vitae']):
                continue
            
            # Check if line looks like a name
            if self._is_likely_name(line):
                return line
        
        return None
    
    def _is_likely_name(self, text: str) -> bool:
        """Check if text looks like a person's name"""
        
        # Must be reasonable length
        if len(text) < 3 or len(text) > 50:
            return False
        
        # Should contain letters
        if not re.search(r'[A-Za-z]', text):
            return False
        
        # Should not contain numbers (except in rare cases)
        if re.search(r'\d', text):
            return False
        
        # Should not contain common CV words
        cv_words = ['cv', 'resume', 'curriculum', 'vitae', 'werkervaring', 'opleiding',
                   'vaardigheden', 'experience', 'education', 'skills']
        if any(word in text.lower() for word in cv_words):
            return False
        
        # Should not be all caps (unless it's a short name)
        if text.isupper() and len(text) > 10:
            return False
        
        # Should have reasonable word count
        words = text.split()
        if len(words) < 1 or len(words) > 4:
            return False
        
        # Check for common name patterns
        # First name + Last name
        if len(words) == 2:
            return True
        
        # First name + Middle name + Last name
        if len(words) == 3:
            return True
        
        # Dutch names with "van", "de", "der", etc.
        if len(words) >= 3 and any(word.lower() in ['van', 'de', 'der', 'den', 'het'] for word in words[1:-1]):
            return True
        
        return False
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location information"""
        
        # Look for Dutch cities
        for city in self.dutch_cities:
            pattern = r'\b' + re.escape(city) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return city.title()
        
        # Look for countries
        for country in self.countries:
            pattern = r'\b' + re.escape(country) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return country.title()
        
        return None
    
    def _extract_birth_year(self, text: str) -> Optional[int]:
        """Extract birth year"""
        
        match = self.pattern_birth_year.search(text)
        if match:
            try:
                year = int(match.group(1))
                # Validate year range
                if 1920 <= year <= 2010:
                    return year
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        
        # Try Dutch phone pattern first
        match = self.pattern_phone_dutch.search(text)
        if match:
            return match.group(0).strip()
        
        # Try international pattern
        match = self.pattern_phone_international.search(text)
        if match:
            return match.group(0).strip()
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        
        match = self.pattern_email.search(text)
        if match:
            return match.group(0).strip()
        
        return None
    
    def _extract_website(self, text: str) -> Optional[str]:
        """Extract website URL"""
        
        match = self.pattern_website.search(text)
        if match:
            url = match.group(0).strip()
            # Clean up URL
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        
        return None
    
    def _extract_nationality(self, text: str) -> Optional[str]:
        """Extract nationality"""
        
        match = self.pattern_nationality.search(text)
        if match:
            nationality = match.group(1).strip()
            # Clean up nationality
            nationality = re.sub(r'\s+', ' ', nationality)
            return nationality.title()
        
        return None
    
    def _extract_driver_license(self, text: str) -> Optional[str]:
        """Extract driver's license category"""
        
        match = self.pattern_driver_license.search(text)
        if match:
            return match.group(1).upper()
        
        return None
    
    def _extract_address(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract address information"""
        
        # Look for postal code + city pattern
        postal_match = self.pattern_postal_code.search(text)
        if postal_match:
            postal_code = postal_match.group(0).strip()
            
            # Find city near postal code
            postal_pos = postal_match.start()
            context_start = max(0, postal_pos - 100)
            context_end = min(len(text), postal_pos + 100)
            context = text[context_start:context_end]
            
            # Look for city in context
            city = None
            for dutch_city in self.dutch_cities:
                if dutch_city.lower() in context.lower():
                    city = dutch_city.title()
                    break
            
            # Try to extract full address
            address_lines = []
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if postal_code in line and len(line) < 100:
                    address_lines.append(line)
            
            address = ' '.join(address_lines) if address_lines else None
            
            return address, postal_code, city
        
        return None, None, None
    
    def _calculate_confidence(self, extracted_data: Dict) -> float:
        """Calculate confidence score for extracted personal info"""
        
        confidence = 0.0
        total_fields = 5
        
        # Name
        if extracted_data.get('name'):
            confidence += 0.3
        
        # Location
        if extracted_data.get('location'):
            confidence += 0.2
        
        # Phone
        if extracted_data.get('phone'):
            confidence += 0.2
        
        # Email
        if extracted_data.get('email'):
            confidence += 0.2
        
        # Birth year
        if extracted_data.get('birth_year'):
            confidence += 0.1
        
        return confidence
    
    def _create_empty_info(self) -> PersonalInfo:
        """Create empty PersonalInfo object"""
        
        return PersonalInfo(
            full_name=None,
            first_name=None,
            last_name=None,
            location=None,
            birth_year=None,
            phone=None,
            email=None,
            website=None,
            nationality=None,
            driver_license=None,
            address=None,
            postal_code=None,
            city=None,
            confidence=0.0,
            language=Language.UNKNOWN
        )
