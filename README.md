# 📝 Resume Parser with IBM Granite and OCR

This project parses resumes in PDF/DOCX format, extracts structured information (experience, skills, education), generates formatted Word documents, and optionally indexes data in Elasticsearch for search.

---> Local LLM Parsing:
Initially, we used Meta’s LLaMA 3 language model running locally to parse and structure resume data. This approach allowed fast prototyping and direct experimentation with prompt engineering and custom logic for extraction.

---> IBM Granite API Integration:
As the project matured, we integrated IBM Watson Machine Learning’s Granite LLM APIs, which offer scalable and robust inference capabilities via the IBM Cloud. The model prompt was adapted to fit IBM’s API, and fallback logic, OCR extraction, and post-processing cleanup were added for improved accuracy.
---

## 🚀 Features

- Extracts text from resumes (PDF and DOCX)  
- OCR fallback if no text is detected  
- Sends text to IBM Granite foundation model to get structured JSON  
- Post-processing cleanup and validation  
- Generates standardized Word resumes using templates  
- Saves extracted JSON  
- Optionally indexes data in Elasticsearch  
- Creates an Excel summary file with candidate metadata 

## 🛠 Requirements

- Python 3.8+
- Tesseract OCR installed (for OCR fallback)
- Poppler installed (for pdf2image)
