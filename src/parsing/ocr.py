import io

import fitz
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def ocr_pdf(pdf_bytes: bytes, max_pages: int = 10, dpi: int = 200) -> str:
    """Extract text from a PDF using OCR fallback."""
    if not TESSERACT_AVAILABLE:
        return "OCR not available - tesseract not installed"
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts = []
    for page_index in range(min(len(doc), max_pages)):
        page = doc[page_index]
        pix = page.get_pixmap(dpi=dpi)
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        page_texts.append(pytesseract.image_to_string(image))
    return "\n".join(page_texts).strip()
