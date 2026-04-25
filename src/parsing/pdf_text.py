import fitz


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_texts = []
    for page in doc:
        text = page.get_text("text")
        if text:
            page_texts.append(text)
    return "\n".join(page_texts).strip()
