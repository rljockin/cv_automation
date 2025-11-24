#!/usr/bin/env python3
"""
OpenAI API Integration for CV Parsing
Converts unstructured CV text to structured data
"""

import os
import sys
import json
import openai
from typing import Dict, Optional
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.core.logger import setup_logger, log_error_with_context
except ImportError:
    # Fallback if logger module not found
    import logging
    def setup_logger(name):
        return logging.getLogger(name)
    def log_error_with_context(logger, msg, error, context=None):
        logger.error(f"{msg}: {error}")

class OpenAICVParser:
    """Parse CV text using OpenAI API"""
    
    def __init__(self):
        # Setup logging
        self.logger = setup_logger(__name__)
        
        # Load environment variables from .env file
        load_dotenv()
        
        # Get OpenAI API key from environment
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            self.logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please create a .env file with your API key or set the environment variable."
            )
        
        self.logger.info("OpenAICVParser initialized successfully")
        
        # System prompt for CV parsing - Based on comprehensive analysis of 949 CVs and 539 Resumés
        self.system_prompt = """
You are an expert CV parsing specialist for Synergie Project Management, with deep knowledge of Dutch and English CV structures based on analysis of 949 CVs and 539 standardized Resumés.

## CONTEXT & REQUIREMENTS

You are parsing CVs to create standardized Synergie Resumés. The target Resumé format is:
- **Purpose**: Client presentation (not personal marketing)
- **Focus**: Project experience and professional roles
- **Privacy**: Minimal personal information (name, city, birth year only)
- **Language**: Dutch preferred, English acceptable
- **Structure**: Table-based layout with specific sections

## CV STRUCTURE PATTERNS (Based on 949 CV Analysis)

### Section Headers (Dutch/English) - By Frequency:
Based on analysis of 949 CVs, sections appear with these frequencies:

1. **Projects** (1866 occurrences, 196.6%): Projecten, Projects, Project ervaring, Uitgevoerde projecten, Enkele projecten, Relevante werkervaring
2. **Work Experience** (1319 occurrences, 139%): Werkervaring, Ervaring, Work experience, Professional experience, Loopbaan
3. **Courses** (1362 occurrences, 143.5%): Cursussen, Courses, Training, Trainingen
4. **Education** (2003 occurrences, 211.1%): Opleiding, Opleidingen, Education, Scholing
5. **Profile** (507 occurrences, 53.4%): Profiel, Profile, Samenvatting, Summary, Over mij
6. **Personal Info** (525 occurrences, 55.3%): Personalia, Persoonlijke gegevens, Personal info, Gegevens
7. **Skills** (407 occurrences, 42.9%): Vaardigheden, Skills, Competenties, Competencies
8. **Languages** (202 occurrences, 21.3%): Talen, Languages, Talenkennis
9. **Software** (156 occurrences, 16.4%): Software, Tools, Applicaties, Programma's
10. **Certifications** (112 occurrences, 11.8%): Certificaten, Certificates, Certificering, Certifications

### CRITICAL: DUAL-SECTION CV PATTERN (Very Common):
Many CVs have work experience split across TWO sections. You MUST extract from BOTH:

**SECTION 1: Career/Employment Timeline**
- Headers: "Loopbaan", "Career", "Werkervaring" (early in CV)
- Content: List of employers with dates and positions
- Example: "2011-heden: [Position], [Company]"
- Location: Usually first 1-2 pages

**SECTION 2: Detailed Work/Project History**
- Headers: "Relevante werkervaring", "Projecten", "Enkele projecten", "Project ervaring"
- Content: Detailed project-by-project breakdown with clients, roles, responsibilities
- Example: "2023-2024: [Project], [Client], [Role], [Responsibilities]"
- Location: Usually pages 2-9 (can be MANY pages)

### EXTRACTION RULE - SIMPLE:
1. Find and extract ALL employers from section 1 (if present)
2. Find and extract ALL projects from section 2 (if present)  
3. Match projects to employers by date overlap
4. If uncertain which employer, use the date range to determine the best match
5. Extract EVERYTHING - don't skip anything

### Date Format Patterns (93% use year-based):
- YYYY (2025)
- YYYY - YYYY (2020 - 2023)
- YYYY - heden (2023 - present)
- Month YYYY (Jan 2025, January 2025)
- DD-MM-YYYY (01-10-2025)
- MM/YYYY (10/2025)

## TARGET RESUMÉ STRUCTURE (Based on 539 Resumé Analysis)

### Required Sections:
1. **Header**: Name (24pt), Location (14pt), Birth Year (14pt)
2. **Profile** (Optional): Professional summary written in he-form (hij is, hij heeft, etc.) - extract exactly if present in CV, otherwise generate (2-5 sentences)
3. **Werkervaring**: Work experience with projects
4. **Opleiding**: Education background
5. **Cursussen**: Training and courses

### Work Experience Structure:
Each position should include:
- Employment period (YYYY - YYYY or YYYY - heden)
- Company name
- Job title/position
- Projects within that position:
  - Project period (MMM 'YY - MMM 'YY)
  - Project name and client
  - Role in project
  - Key responsibilities (bullet points)

## EXTRACTION GUIDELINES

### Personal Information:
- **Extract**: Full name, city (not full address), birth year (not full date)
- **Do NOT extract**: Phone numbers, email addresses, full addresses, photos
- **Privacy focus**: Only what's needed for client presentation

### Work Experience - CRITICAL: FLAT STRUCTURE (One Entry Per Project)

**RULE 1: Each project/assignment = Separate work_experience entry**
Do NOT group projects under one employer. Each project gets its own entry in the work_experience array.

**RULE 2: Read the ENTIRE CV**
- Scan all pages from start to finish
- CVs are typically 3-9 pages
- Projects often span pages 2-9

**RULE 3: Find ALL project/work entries**
Look for:
- "Relevante werkervaring" / "Projecten" / "Enkele projecten" (main source of project details)
- "Loopbaan" / "Werkervaring" (employment timeline - may have additional context)
- Any mention of work with dates, client names, roles

**RULE 4: Create SEPARATE entry for each project**
For each project found, create ONE work_experience entry:
```json
{
  "company": "[Company/Client Name]",  // Could be "GLOBOX for Client X" or just "Client X"
  "position": "[Role for this specific project]",  // "Projectleider", "Ontwerpleider", etc.
  "start_date": "[YYYY]",  // Project start year
  "end_date": "[YYYY or null]",  // Project end year
  "is_current": false,
  "projects": [{
    "name": "[Project Name]",
    "responsibilities": ["task1", "task2", ...]
  }]
}
```

**RULE 5: Extract complete information for EACH project**
- Company/Client name (who you worked for on this project)
- Position/Role (what you did on this project)
- Start & end dates (YYYY format)
- Project name
- ALL responsibilities (every bullet point)
- Technologies/Keywords

**RULE 6: No grouping, no nesting**
- DON'T create one "2011-heden: Self-employed" entry with 20 projects inside
- DO create 20 separate entries, each with its own dates and client
- Each work_experience entry represents ONE project or ONE work period

**Example Output Structure:**
```json
{
  "work_experience": [
    {
      "company": "Royal Haskoning Nederland",
      "position": "Faseringcoördinator",
      "start_date": "2021",
      "end_date": "2023",
      "projects": [{"name": "Oosterweel Contract 3B", "responsibilities": [...]}]
    },
    {
      "company": "ROCO THV Belgie",
      "position": "Faseringcoördinator",  
      "start_date": "2021",
      "end_date": "2023",
      "projects": [{"name": "Oosterweel Contract 3B", "responsibilities": [...]}]
    },
    {
      "company": "Tauw Nederland",
      "position": "Ontwerper Wegen",
      "start_date": "2021",
      "end_date": "2021",
      "projects": [{"name": "Reconstructie A9", "responsibilities": [...]}]
    }
    // ... 50+ more entries, one per project
  ]
}
```

### REAL-WORLD EXAMPLE (Henny Kooijman Pattern):

**Input CV Structure:**
```
Page 1:
Loopbaan:
2011-heden: Zelfstandig Ondernemer, GLOBOX Engineering
2010: Projectmanager Complexe Infra, Inspec Nederland bv
2008-2010: Projectmanager Civiel, Tauw Nederland bv
[...8 more employers...]

Pages 2-9:
Relevante werkervaring:
2025-heden: Medewerken aan richtlijnen NOA, Handboek Wegontwerp
2023-2024: [Project details]
2021-2023: Oosterweel Contract 3B, Royal Haskoning, Faseringcoördinator
  Keywords: 3D, BIM, Ontwerpnota, Relatics, Inpassing, Fasering
2021-2022: Oosterweel Contract 3B, ROCO THV Belgie, Faseringcoördinator
  Keywords: Overleg, Technische Eisen, Werkpakketten
2020-2021: [More projects...]
[...30+ more projects back to 2011...]
```

**Correct Extraction:**
```json
{
  "work_experience": [
    {
      "company": "GLOBOX Engineering",
      "position": "Zelfstandig Ondernemer",
      "start_date": "2011",
      "end_date": null,
      "is_current": true,
      "projects": [
        {
          "name": "Medewerken aan richtlijnen NOA",
          "client": "Handboek Wegontwerp",
          "period": "2025-heden",
          "role": null,
          "responsibilities": [...]
        },
        {
          "name": "Oosterweel Contract 3B",
          "client": "Royal Haskoning",
          "period": "2021-2023",
          "role": "Faseringcoördinator",
          "responsibilities": [...],
          "technologies": ["3D", "BIM", "Ontwerpnota", "Relatics"]
        },
        ... (ALL 30+ projects from 2011-2025)
      ]
    },
    {
      "company": "Inspec Nederland bv",
      "position": "Projectmanager Complexe Infra",
      "start_date": "2010",
      "end_date": "2010",
      "projects": []
    },
    ... (other employers from Loopbaan)
  ]
}
```

**Key Points:**
- GLOBOX has 30+ projects (from "Relevante werkervaring" section)
- Each project has full details (name, client, period, role, responsibilities, technologies)
- Older employers (pre-2011) have empty projects arrays (no details in CV)

### Education:
- **Extract**: Degree name, institution, period
- **Focus on**: Higher education (HBO, WO, University)
- **Format**: YYYY - YYYY or single year

### Profile Summary:
- **CRITICAL RULE: Exact extraction if profile section exists**
  - If CV contains a profile section (Profiel, Profile, Samenvatting, Summary, Over mij):
    → Extract the text EXACTLY as written
    → ONLY change it to he-form (hij is, hij heeft, hij werkt, etc.)
    → Do NOT rewrite, rephrase, or summarize
    → Keep original structure and key phrases
  - If NO profile section exists:
    → Generate new profile based on work_experience, education, and skills
    → Length: 2-5 sentences
- **Always write in he-form**: Use "hij is", "hij heeft", "hij werkt", etc. (3rd person singular)
- **Length**: 
  - If extracted from CV: Keep original length (may be longer than 5 sentences)
  - If generated: 2-5 sentences
- **Content**: Professional summary, experience level, specializations

### Skills & Competencies:
- **Technical skills**: Software, tools, methodologies
- **Project management**: PM methodologies, certifications
- **Industry knowledge**: Infrastructure, engineering, construction

## OUTPUT FORMAT

Return valid JSON with this exact structure:

{
    "personal_info": {
        "full_name": "string",
        "location": "string (city only)",
        "birth_year": number,
        "phone": "string (optional)",
        "email": "string (optional)"
    },
    "work_experience": [
        {
            "company": "string (company/client name)",
            "position": "string (role/function for this specific work/project)",
            "start_date": "string (YYYY)",
            "end_date": "string (YYYY or null for current)",
            "is_current": boolean,
            "location": "string (optional)",
            "projects": [
                {
                    "name": "string (project name if mentioned)",
                    "client": "string (optional)",
                    "period": "string (optional)",
                    "role": "string (optional)",
                    "responsibilities": ["string"],
                    "technologies": ["string (optional)"],
                    "description": "string (optional)"
                }
            ]
        }
    ],
    
    CRITICAL - WORK EXPERIENCE STRUCTURE:
    Each project or work assignment should be a SEPARATE work_experience entry, not nested!
    
    Example - WRONG (nested):
    {
      "company": "Self-employed, GLOBOX",
      "start_date": "2011",
      "projects": [
        {"name": "Project A", "period": "2023-2024"},
        {"name": "Project B", "period": "2021-2022"}
      ]
    }
    
    Example - CORRECT (flat):
    [
      {
        "company": "GLOBOX Engineering (for Client X)",
        "position": "Projectleider",
        "start_date": "2023",
        "end_date": "2024",
        "projects": [{"name": "Project A", "responsibilities": [...]}]
      },
      {
        "company": "GLOBOX Engineering (for Client Y)", 
        "position": "Ontwerpleider",
        "start_date": "2021",
        "end_date": "2022",
        "projects": [{"name": "Project B", "responsibilities": [...]}]
      }
    ]
    
    Each client project = separate work_experience entry with its own dates!
    "education": [
        {
            "degree": "string",
            "institution": "string",
            "period": "string (YYYY - YYYY)",
            "graduation_year": "string (optional)",
            "field_of_study": "string (optional)"
        }
    ],
    "courses": [
        {
            "name": "string",
            "year": "string (YYYY)",
            "institution": "string (optional)"
        }
    ],
    "skills": ["string"],
    "languages": ["string"],
    "certifications": ["string"],
    "profile_summary": "string (exact extract from CV converted to he-form, or 2-5 sentences if generated)",
    "confidence_score": number (0.0-1.0)
}

## QUALITY REQUIREMENTS

### Data Quality:
- Extract exact information, don't make assumptions
- Handle missing information gracefully (use null or empty arrays)
- Maintain chronological order (most recent first)
- Focus on project management and infrastructure experience
- Use professional, third-person language

### Confidence Scoring:
- 0.9-1.0: Complete information, clear structure, all sections present
- 0.7-0.8: Most information present, minor gaps
- 0.5-0.6: Significant information missing, unclear structure
- 0.0-0.4: Major extraction issues, incomplete data

### Language Handling:
- Primary: Dutch (89.8% of CVs)
- Secondary: English (3.1% of CVs)
- Output in Dutch when possible
- Maintain original terminology for technical terms

## COMMON CV PATTERNS

### Pattern 1: Dual-Section CV (Most Common)
- CV has BOTH "Loopbaan" (employer list) AND "Projecten" (project details)
- Extract employers from first section, projects from second section
- Match projects to employers by date overlap
- Result: Employers with detailed project arrays

### Pattern 2: Single Work Experience Section
- CV has only one "Werkervaring" section with everything combined
- Extract employers and projects from same section
- Each job entry may have nested project information

### Pattern 3: Project-Focused CV
- CV emphasizes projects over employers
- Extract all projects with associated companies/clients
- Group projects by employer based on dates and company mentions

**Universal Rule**: Regardless of CV structure, extract ALL work information found anywhere in the CV. The output structure is always the same: employers with projects arrays.

## ERROR HANDLING

If you encounter:
- **Unclear sections**: Use context clues, prioritize work experience
- **Missing dates**: Estimate based on context, mark as uncertain
- **Multiple formats**: Normalize to standard format
- **Language mixing**: Extract in primary language detected
- **Incomplete information**: Extract what's available, note gaps

Remember: You are creating data for professional Resumés that will be presented to clients. Focus on accuracy, completeness, and professional presentation.
"""
    
    def parse_cv_text(self, cv_text: str) -> Optional[Dict]:
        """Parse CV text using OpenAI API"""
        try:
            self.logger.info(f"Starting OpenAI CV parsing, text length: {len(cv_text)} characters")
            print(f"Parsing CV text with OpenAI API...")
            print(f"Text length: {len(cv_text)} characters")
            
            # OpenAI gpt-4o-mini supports up to 128k tokens (~500k characters)
            # Keep a reasonable limit but much higher to avoid losing work experience
            if len(cv_text) > 100000:  # Very high limit - most CVs are under this
                print(f"Warning: CV text is very long ({len(cv_text)} chars), truncating to 100,000 chars")
                cv_text = cv_text[:100000] + "..."
            else:
                print(f"CV text length: {len(cv_text)} chars (within limits)")
            
            # Create user prompt
            user_prompt = f"""
Parse this CV and extract ALL information according to the system prompt structure.

## ⚠️ CRITICAL: EXTRACT FROM ALL WORK-RELATED SECTIONS ⚠️

Many CVs split work information across MULTIPLE sections. You MUST check and extract from ALL of these:

**Section Types to Check:**
1. "Werkervaring" / "Work Experience" / "Ervaring" / "Experience"
2. "Projecten" / "Projects" / "Enkele projecten" / "Uitgevoerde projecten"
3. "Loopbaan" / "Career" / "Employment History"
4. "Relevante werkervaring" / "Relevant Experience" / "Project ervaring"
5. "Professional experience" / "Work History"

**EXTRACTION RULE - SCAN ENTIRE CV:**
- Read from line 1 to the LAST line of the CV
- Identify EVERY section with work-related headers (listed above)
- Extract ALL work entries from ALL sections
- Combine everything into a single work_experience array
- Each project = separate work_experience entry

**Common CV Structures (handle ALL):**
- **Structure A:** "Ervaring" (3 jobs) + "Projecten" (25 projects) → Extract ALL 28 entries
- **Structure B:** "Werkervaring" only → Extract all from that section
- **Structure C:** "Loopbaan" + "Relevante werkervaring" → Extract from BOTH
- **Structure D:** "Projecten" only → Extract all as work experience

**Example - Robin Aartsma Pattern:**
```
CV Structure:
- Page 1: "Ervaring" with 2-3 employer summaries
- Page 2-5: "Projecten" with 20+ detailed project descriptions

Correct Output: 20+ work_experience entries (all projects found)
Wrong Output: Only 2-3 entries (missed "Projecten" section) ← DON'T DO THIS
```

## WORK EXPERIENCE - SPECIAL INSTRUCTIONS (FLAT STRUCTURE):

DOEL: Extract ALL work experience as SEPARATE entries (one entry per project).

## ⚠️⚠️⚠️ ABSOLUTE REGEL: EEN PROJECT = EEN WORK_EXPERIENCE ENTRY ⚠️⚠️⚠️

**FOUT - DOE DIT NOOIT:**
```json
{{
  "work_experience": [
    {{
      "company": "Company X",
      "start_date": "2018",
      "end_date": "2023",
      "projects": [
        {{"name": "Project A", "period": "2020-2021", "role": "Consultant"}},
        {{"name": "Project B", "period": "2021-2022", "role": "Senior"}},
        {{"name": "Project C", "period": "2022-2023", "role": "Lead"}}
      ]
    }}
  ]
}}
```
☝️ DIT IS FOUT! Meerdere projecten in één work_experience entry!

**CORRECT - DOE DIT WEL:**
```json
{{
  "work_experience": [
    {{
      "company": "Company X",
      "position": "Consultant",
      "start_date": "2020",
      "end_date": "2021",
      "projects": [{{"name": "Project A", "responsibilities": [...]}}]
    }},
    {{
      "company": "Company X",
      "position": "Senior",
      "start_date": "2021",
      "end_date": "2022",
      "projects": [{{"name": "Project B", "responsibilities": [...]}}]
    }},
    {{
      "company": "Company X",
      "position": "Lead",
      "start_date": "2022",
      "end_date": "2023",
      "projects": [{{"name": "Project C", "responsibilities": [...]}}]
    }}
  ]
}}
```
☝️ DIT IS CORRECT! Elk project is een aparte work_experience entry!

**KERN REGELS:**
1. Elke work_experience entry heeft MAXIMAAL 1 project in de projects array
2. Gebruik de PROJECT datums voor start_date/end_date (NIET de overall employment periode)
3. Als iemand bij Company X werkte van 2018-2023 met 5 projecten:
   → Maak 5 aparte work_experience entries
   → Elk met project-specifieke datums (bijv. 2020-2021, 2021-2022, etc.)
   → Elk met project-specifieke rol
4. Dit geldt voor ZZP EN loondienst!

**DETECTIE REGELS:**
- Zie je meerdere projectnamen onder één werkgever? → SPLIT ZE
- Zie je meerdere rollen onder één werkgever? → SPLIT ZE
- Zie je meerdere tijdsperiodes voor projecten? → SPLIT ZE
- Elk uniek project/rol/periode = aparte work_experience entry

INSTRUCTIES (stap-voor-stap):
1) Lees de HELE CV-tekst van begin tot eind.
   - Zoek expliciet naar ALLE secties met werk-gerelateerde kopjes: "Ervaring", "Projecten", "Werkervaring", "Loopbaan", "Relevante werkervaring", "Projects", "Work experience" etc.
   - Alle werkervaring uit ALLE gevonden secties moet worden geëxtraheerd
   - NEGEER GEEN ENKELE SECTIE - als een sectie "Projecten" heet, bevat het ook werkervaring!

2) Identificeer ieder afzonderlijk project / opdracht:
   - Een project = één specifieke opdracht/rol (ook als meerdere projecten onder dezelfde werkgever staan).
   - CRITICAL: **NOOIT meerdere projecten groeperen onder één werkgever**. Elke opdracht krijgt één eigen work_experience entry met eigen datums.
   - Als je 3 projecten ziet bij Company X → maak 3 aparte work_experience entries (niet 1 entry met 3 projecten array items!)

3) Voor elk project maak je precies één JSON-entry met de volgende velden:
   - company (string) : de klant/organisatie voor díe opdracht (gebruik de naam zoals in CV vermeld; als het 'ZZP' of opdrachtgever X is, zet exacte vermelding).
   - position (string) : functie/rol die voor díe opdracht is opgegeven (bijv. "Contractmanager", "Projectleider", "Ontwerper").
   - start_date (string|null) : extracteer JAAR in YYYY formaat. Als alleen maand+jaar gegeven, haal jaar (YYYY). Als exacte dag niet aanwezig, negeer dag. Als niet vindbaar: null.
   - end_date (string|null) : extracteer JAAR in YYYY formaat. Als ongoing (bijv. "heden", "present", "nu"): gebruik null en zet is_current op true. Als slechts één jaar vermeld (bv. "2021"): zet start_date en end_date beide op "2021". Als niet vindbaar: null.
   - is_current (boolean) : true als project nog loopt (heden/present), anders false.
   - projects (array) : bevat exact één object met:
       - name (string|null) : naam/titel van het project/werk (zoals in CV). Als niet expliciet: null.
       - responsibilities (array[string]) : ALTIJD een array van strings, ook als CV doorlopende tekst heeft!
           * Als CV bullet points heeft: gebruik die letterlijk (één bullet = één array item)
           * Als CV doorlopende tekst/paragraaf heeft: split de tekst in logische werkzaamheden
           * Elke werkzaamheid = één zin/regel in de array
           * Behoud de originele tekst, verander niets aan de betekenis
           * Split op basis van: komma's, puntkomma's, "en", nieuwe zinnen, of logische taken
           * Voorbeeld: "Projectmanagement inclusief planning, budgetbeheer en risicomanagement" 
             → ["Projectmanagement inclusief planning", "Budgetbeheer", "Risicomanagement"]

4) EDGE CASES:
   - If a project lists a client separate from employer, use the client's name as `company`.
   - If a role is given globally for an employer and not per project, use that role for each project entry.
   - If date format is a single range covering multiple projects with no per-project dates: attempt to find per-project bullets with dates; if impossible, set start_date/end_date to null.
   - Language handling: CV may be Dutch or English — parse both.

## OTHER SECTIONS (Extract normally):
- **personal_info**: full_name, location (city only), birth_year
- **education**: degree, institution, period
- **courses**: name, year, institution
- **skills**: software, tools, technical skills (array of strings)
- **languages**: talen (array of strings)
- **profile_summary**: Exact extract from CV (converted to he-form) if profile section exists, otherwise generate 2-5 sentences
- **confidence_score**: 0.0-1.0

CV TEXT ({len(cv_text)} characters):
{cv_text}

Return complete JSON with the structure specified in the system prompt.
Extract ALL work experience as SEPARATE flat entries (one per project)!

IMPORTANT FOR PROFILE_SUMMARY:
- If CV has a profile/profiel/samenvatting/summary section: Extract EXACTLY and ONLY convert to he-form
- If CV has NO profile section: Generate new 2-5 sentences based on work experience, education, and skills
- NEVER rewrite or rephrase existing profile text - only convert to he-form!
"""
            
            # Call OpenAI API (new format for openai>=1.0.0)
            import httpx
            client = openai.OpenAI(
                api_key=self.api_key,
                http_client=httpx.Client(timeout=120.0)  # 2 minute timeout
            )
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",  # Using full gpt-4o instead of mini for higher token limits
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=16384  # gpt-4o supports up to 16k output tokens (128k total context)
                )
            except openai.RateLimitError as e:
                error_msg = f"OpenAI API rate limit exceeded. Please try again in a moment. Error: {str(e)}"
                self.logger.error(error_msg)
                print(error_msg)
                return None
            except openai.AuthenticationError as e:
                error_msg = f"OpenAI API authentication failed. Please check your API key. Error: {str(e)}"
                self.logger.error(error_msg)
                print(error_msg)
                return None
            except openai.APIError as e:
                error_msg = f"OpenAI API error: {str(e)}"
                self.logger.error(error_msg)
                print(error_msg)
                return None
            except Exception as e:
                error_msg = f"Unexpected error calling OpenAI API: {str(e)}"
                self.logger.error(error_msg)
                print(error_msg)
                return None
            
            # Extract response
            if not response or not response.choices or len(response.choices) == 0:
                error_msg = "OpenAI API returned empty response"
                self.logger.error(error_msg)
                print(error_msg)
                return None
                
            response_text = response.choices[0].message.content
            if not response_text:
                error_msg = "OpenAI API returned empty content"
                self.logger.error(error_msg)
                print(error_msg)
                return None
                
            print(f"OpenAI response received: {len(response_text)} characters")
            
            # Parse JSON response (handle markdown code blocks and explanations)
            try:
                # Clean JSON response generically
                response_text = self._extract_json_safely(response_text)
                
                cv_data = json.loads(response_text)
                print(f"JSON parsed successfully")
                
                # Validate required fields
                if self._validate_cv_data(cv_data):
                    print(f"CV data validation passed")
                    return cv_data
                else:
                    print(f"CV data validation failed")
                    return None
                    
            except json.JSONDecodeError as e:
                log_error_with_context(
                    self.logger,
                    "JSON parsing error in OpenAI response",
                    e,
                    {'response_preview': response_text[:500]}
                )
                print(f"JSON parsing error: {e}")
                print(f"Response text: {response_text[:500]}...")
                return None
                
        except Exception as e:
            log_error_with_context(
                self.logger,
                "OpenAI API call failed",
                e,
                {'text_length': len(cv_text)}
            )
            print(f"OpenAI API error: {e}")
            return None
    
    def _extract_json_safely(self, text: str) -> str:
        """
        Generically extract JSON from response that may have extra text
        Handles markdown code blocks and explanations
        """
        # Remove markdown code blocks if present
        if '```json' in text:
            # Find JSON block
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end > start:
                text = text[start:end].strip()
        elif '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end > start:
                text = text[start:end].strip()
        
        # Find first { and last }
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace:last_brace + 1]
        
        return text.strip()
    
    def _validate_cv_data(self, cv_data: Dict) -> bool:
        """Validate that CV data has required fields"""
        try:
            # Debug: print what we got
            print(f"Validating CV data with keys: {list(cv_data.keys())}")
            
            # Check work experience (minimum required)
            if 'work_experience' not in cv_data:
                print("Missing required field: work_experience")
                return False
            
            work_experience = cv_data.get('work_experience', [])
            if not isinstance(work_experience, list):
                print("work_experience must be a list")
                return False
            
            print(f"Work experience entries: {len(work_experience)}")
            
            # Add missing optional fields with defaults
            if 'personal_info' not in cv_data:
                print("Warning: personal_info missing - adding defaults")
                cv_data['personal_info'] = {
                    'full_name': 'Unknown',
                    'location': 'Unknown',
                    'birth_year': None
                }
            
            if 'education' not in cv_data:
                cv_data['education'] = []
            
            if 'courses' not in cv_data:
                cv_data['courses'] = []
            
            if 'skills' not in cv_data:
                cv_data['skills'] = []
            
            if 'languages' not in cv_data:
                cv_data['languages'] = []
            
            if 'certifications' not in cv_data:
                cv_data['certifications'] = []
            
            if 'profile_summary' not in cv_data:
                cv_data['profile_summary'] = None
            
            if 'confidence_score' not in cv_data:
                cv_data['confidence_score'] = 0.8
            
            return True
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    def test_api_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            import httpx
            client = openai.OpenAI(
                api_key=self.api_key,
                http_client=httpx.Client()
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Hello, this is a test. Please respond with 'API connection successful'."}
                ],
                max_tokens=10
            )
            
            response_text = response.choices[0].message.content
            print(f"API test response: {response_text}")
            return "successful" in response_text.lower()
            
        except Exception as e:
            print(f"API connection test failed: {e}")
            return False

if __name__ == "__main__":
    # Test the parser
    parser = OpenAICVParser()
    
    print("Testing OpenAI API connection...")
    if parser.test_api_connection():
        print("✅ API connection successful")
    else:
        print("❌ API connection failed")
    
    # Test with sample CV text
    sample_cv_text = """
    Robin Aartsma
    Woonplaats: Amersfoort Geboortedatum: 16-07-1986
    Telefoonnummer: 06-43023640
    
    PROFIEL
    Door de diverse projecten die ik in de laatste jaren heb uitgevoerd heb ik een breed kennisveld opgebouwd in zowel de bouwkunde als de infrastructuur.
    
    ERVARING
    Adviseur planning & risicomanagement - Iapo
    November 2016 - heden.
    
    PROJECTEN
    2016 – heden: Dijkverbeteringsprojecten (HWBP), Waterschap Vallei en Veluwe
    Werkzaamheden: Als planner betrokken bij het projectteam voor het opstellen van de deterministische en probabilistische planningen.
    """
    
    print("\nTesting CV parsing...")
    result = parser.parse_cv_text(sample_cv_text)
    
    if result:
        print("✅ CV parsing successful")
        print(f"Extracted name: {result.get('personal_info', {}).get('full_name')}")
        print(f"Work experience entries: {len(result.get('work_experience', []))}")
        print(f"Confidence score: {result.get('confidence_score', 0.0)}")
    else:
        print("❌ CV parsing failed")
