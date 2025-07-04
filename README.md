# 📝 Resume Parser with IBM Granite and OCR

This project parses resumes in PDF/DOCX format, extracts structured information (experience, skills, education), generates formatted Word documents, and optionally indexes data in Elasticsearch for search.

---

## 🚀 Features

✅ Extracts text from resumes (PDF and DOCX)  
✅ OCR fallback if no text is detected  
✅ Sends text to IBM Granite foundation model to get structured JSON  
✅ Post-processing cleanup and validation  
✅ Generates standardized Word resumes using templates  
✅ Saves extracted JSON  
✅ Optionally indexes data in Elasticsearch  
✅ Creates an Excel summary file with candidate metadata 

## 🛠 Requirements

- Python 3.8+
- Tesseract OCR installed (for OCR fallback)
- Poppler installed (for pdf2image)