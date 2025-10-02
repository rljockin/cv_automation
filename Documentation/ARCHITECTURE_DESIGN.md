# CV Automation System
## Automated CV → Resumé Generation for Synergie PM

Transform raw CV files into standardized Synergie Resumés through intelligent extraction, parsing, and generation.

---

## 🎯 Project Overview

This system automates the process of converting diverse CV formats into the standard Synergie project management Resumé template. It handles:

- **949 CVs analyzed** - Understanding all input formats
- **539 Resumés analyzed** - Perfect template replication
- **93.7% success rate** - High automation potential
- **6.3% requiring OCR** - Robust error handling

---

## 📊 System Status

**Phase:** Architecture & Foundation  
**Version:** 0.1.0 (Development)  
**Last Updated:** October 1, 2025  

---

## 🏗️ Architecture

The system uses a modular 7-layer architecture:

1. **Input Layer** - File scanning and validation
2. **Extraction Layer** - Text extraction (DOCX, PDF, OCR)
3. **Transformation Layer** - Data mapping and cleaning
4. **Generation Layer** - Resumé document creation
5. **Quality Control Layer** - Validation and review
6. **Output Layer** - File management and storage
7. **Monitoring Layer** - Logging and metrics

See [`Documentation/ARCHITECTURE_DESIGN.md`](Documentation/ARCHITECTURE_DESIGN.md) for complete architecture details.

---

## 📁 Project Structure

```
CV Automation/
├── Documentation/          # All analysis reports and design docs
├── src/                   # Source code (modular components)
│   ├── 1_input/          # File scanning and validation
│   ├── 2_extraction/     # Text extractors and parsers
│   ├── 3_transformation/ # Data mapping and cleaning
│   ├── 4_generation/     # Resumé template generation
│   ├── 5_quality/        # Quality control and validation
│   ├── 6_output/         # File management
│   ├── 7_monitoring/     # Logging and metrics
│   ├── core/             # Core models and utilities
│   └── api/              # API interfaces
├── docker/                # Docker configuration
├── tests/                 # Unit and integration tests
├── data/                  # Analysis data and templates
├── database/              # SQLite database
├── logs/                  # Application logs
├── scripts/               # Utility and analysis scripts
└── config/                # Configuration files
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Tesseract OCR (for image-based PDFs)
- LibreOffice (for PDF conversion)
- Docker (for containerized deployment)

### Installation

```bash
# Clone or navigate to project
cd "CV Automation"

# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract OCR (Windows)
choco install tesseract

# Verify installation
python --version
tesseract --version
```

### Running

```bash
# Process single CV
python scripts/run_single.py --cv-path "path/to/cv.pdf"

# Process batch
python scripts/run_batch.py --folder "Netwerk - Documenten"

# Launch web interface
python web/app.py
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE_DESIGN.md](Documentation/ARCHITECTURE_DESIGN.md) | Complete system architecture |
| [COMPREHENSIVE_INVESTIGATION_SUMMARY.md](Documentation/COMPREHENSIVE_INVESTIGATION_SUMMARY.md) | CV analysis (949 files) |
| [Comprehensive_CV_Analysis_Report.txt](Documentation/Comprehensive_CV_Analysis_Report.txt) | Detailed CV catalog |
| [Comprehensive_Resume_Analysis_Report.txt](Documentation/Comprehensive_Resume_Analysis_Report.txt) | Detailed Resumé catalog |

---

## 🎨 Synergie Template Specifications

### Colors
- **Primary Orange:** `#D07E1F` (RGB: 208, 126, 31)
- **Text:** Black `#000000`
- **Secondary:** Gray `#808080`

### Typography
- **Font:** Calibri (exclusive)
- **Sizes:** 24pt (name), 18pt (headers), 14pt (body), 10pt (details)

### Structure
- **Page:** A4 (8.27" × 11.69")
- **Margins:** Top 1.63", Bottom 1.11", Left 0.93", Right 0.80"
- **Layout:** Table-based (2-column: 25% dates | 75% content)

---

## 🔧 Development

### Setting Up Development Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Code Style

- **Language:** Python 3.11+
- **Style Guide:** PEP 8
- **Type Hints:** Required
- **Docstrings:** Google style
- **Testing:** pytest

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t cv-automation .

# Run container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 📈 Performance Metrics

| Metric | Current | Target |
|--------|---------|--------|
| **Success Rate** | 93.7% | >90% ✅ |
| **Processing Speed** | TBD | <2 min/CV |
| **Accuracy** | TBD | >95% |
| **Files Processed** | 0 | 949 total |

---

## 🗺️ Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅
- [x] Architecture design
- [x] Folder structure
- [x] Documentation
- [ ] Base classes and interfaces

### Phase 2: Extraction (Weeks 3-4)
- [ ] DOCX extractor
- [ ] PDF extractor
- [ ] OCR pipeline
- [ ] Section parsers

### Phase 3: Generation (Weeks 5-6)
- [ ] Template engine
- [ ] Table builder
- [ ] PDF converter
- [ ] Style applicator

### Phase 4: Integration (Week 7)
- [ ] End-to-end pipeline
- [ ] Quality control
- [ ] Testing
- [ ] Bug fixes

### Phase 5: Production (Week 8)
- [ ] Docker deployment
- [ ] Web interface
- [ ] Monitoring
- [ ] Documentation

---

## 🤝 Contributing

This is an internal Synergie PM project. For questions or suggestions:

1. Review the architecture documentation
2. Check existing issues/tasks
3. Follow the development guidelines
4. Test thoroughly before committing

---

## 📝 License

Internal Synergie PM Project - All Rights Reserved

---

## 🔗 Related Resources

- **Network Folder:** `C:\Users\RudoJockinSynergiepr\Synergie PM\Netwerk - Documenten`
- **CV Count:** 949 files
- **Resumé Count:** 1,089 files (539 DOCX + 550 PDF)
- **Unprocessed:** 325 CVs pending

---

## 📞 Support

For issues or questions:
- Check documentation in `Documentation/` folder
- Review logs in `logs/` folder
- See analysis reports for CV/Resumé patterns

---

**Last Updated:** October 1, 2025  
**Status:** 🏗️ In Development  
**Next Milestone:** Complete Input Layer components

