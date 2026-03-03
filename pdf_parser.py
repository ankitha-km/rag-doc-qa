# step2_pdf_parser.py  (updated)
import fitz
import re   # regular expressions — for text cleaning

def clean_text(text):
    """Remove noise from raw PDF text."""

    # Multiple newlines → single newline
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Multiple spaces → single space
    text = re.sub(r'[ \t]{2,}', ' ', text)

    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\n]', ' ', text)

    return text.strip()


def parse_pdf(filepath):
    """
    Opens a PDF and returns a list of dicts.
    Each dict = one page worth of cleaned text + metadata.
    """
    doc = fitz.open(filepath)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        raw_text = page.get_text()
        cleaned = clean_text(raw_text)

        # Only keep pages that actually have text
        if len(cleaned.strip()) > 50:
            pages.append({
                "page_number": page_num + 1,
                "text": cleaned,
                "char_count": len(cleaned)
            })

    doc.close()
    return pages


# ── Run it and inspect the output ────────────────────────
if __name__ == "__main__":
    pages = parse_pdf("sample.pdf")

    print(f"✅ Extracted {len(pages)} pages with text\n")

    for p in pages:
        print(f"📄 Page {p['page_number']} — {p['char_count']} chars")
        print(p['text'][:400])
        print("─" * 60)