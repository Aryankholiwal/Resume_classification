import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from io import StringIO

def extract_pdf_text(pdf_path, include_tables=True, ocr=None):
    """
    Extracts text from a PDF file.
    - If ocr=False: only extract text, no OCR fallback.
    - If ocr=True: force OCR on all pages.
    - If ocr=None: try text first, then OCR if empty.
    """
    def _extract_text_from_pdf():
        text_lines = []

        with fitz.open(pdf_path) as doc:
            for page in doc:
                # Standard page text
                page_text = page.get_text().strip()
                if page_text:
                    text_lines.append(page_text)

                if include_tables:
                    # Structured blocks
                    blocks = page.get_text("dict").get("blocks", [])
                    for block in blocks:
                        if "lines" in block:
                            for line in block["lines"]:
                                parts = [
                                    span.get("text", "").strip()
                                    for span in line.get("spans", [])
                                    if span.get("text", "").strip()
                                ]
                                if parts:
                                    line_text = " | ".join(parts)
                                    text_lines.append(line_text)

        # Remove duplicates while preserving order
        seen = set()
        deduped_lines = []
        for line in text_lines:
            if line not in seen:
                deduped_lines.append(line)
                seen.add(line)

        return "\n".join(deduped_lines).strip()

    def _perform_ocr():
        print("🟠 OCR processing PDF pages...")
        images = convert_from_path(pdf_path)
        ocr_text = StringIO()
        for img in images:
            ocr_text.write(pytesseract.image_to_string(img))
        return ocr_text.getvalue().strip()

    if ocr is True:
        # Force OCR
        return _perform_ocr()
    elif ocr is False:
        # Force only text extraction
        return _extract_text_from_pdf()
    else:
        # Default behavior: try text, then fallback
        extracted_text = _extract_text_from_pdf()
        if extracted_text:
            return extracted_text
        else:
            return _perform_ocr()
