from pdf_parser import extract_text_from_pdf

pages = extract_text_from_pdf("sample.pdf")

print(f"Total pages: {len(pages)}")
print(f"Page 2 preview:\n{pages[1]['text'][:300]}")