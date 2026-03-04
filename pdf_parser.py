import fitz
import re


def clean_text(text):
    """
    Cleans raw PDF text — fixes 3 problems:
    1. Excessive newlines
    2. Hyphenated words split across lines
    3. Special/unicode characters
    """
    # collapse 3+ newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # join hyphenated line breaks: "transfor-\nmation" → "transformation"
    text = re.sub(r'-\n', '', text)
    
    # remove non-ASCII characters like ∗ † Ł
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # collapse multiple spaces into one
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    text = text.strip()
    return text


def extract_text_from_pdf(pdf_path):
    """
    Opens a PDF and extracts clean text page by page.
    Returns a list of dicts, one per page.
    """
    pages = []
    doc = fitz.open(pdf_path)

    print(f"📄 Opened: {pdf_path}")
    print(f"📝 Total pages: {len(doc)}")

    for page_number in range(len(doc)):
        page = doc[page_number]
        raw_text = page.get_text()

        if raw_text.strip() == "":
            print(f"  ⚠️  Page {page_number + 1} is empty, skipping...")
            continue

        cleaned_text = clean_text(raw_text)

        page_data = {
            "page_number": page_number + 1,
            "text": cleaned_text,
            "char_count": len(cleaned_text)
        }

        pages.append(page_data)
        print(f"  ✅ Page {page_number + 1}: {len(cleaned_text)} characters")

    doc.close()
    return pages


if __name__ == "__main__":

    results = extract_text_from_pdf("sample.pdf")

    print("\n" + "="*50)
    print(f"✅ DONE — extracted {len(results)} pages")
    print("="*50)

    # open raw again just for comparison
    doc = fitz.open("sample.pdf")
    raw = doc[0].get_text()
    doc.close()

    print("\n🔴 BEFORE CLEANING:")
    print("-"*30)
    print(repr(raw[:200]))

    print("\n🟢 AFTER CLEANING:")
    print("-"*30)
    print(repr(results[0]["text"][:200]))