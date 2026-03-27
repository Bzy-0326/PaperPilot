import re
import fitz

URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+")

def parse_pdf_basic(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)

    pages = []
    all_text = []
    links = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        all_text.append(text)

        page_links = URL_RE.findall(text)
        for link in page_links:
            links.append({
                "page": page_num,
                "url": link
            })

        pages.append({
            "page_number": page_num,
            "text": text
        })

    full_text = "\n".join(all_text)

    return {
        "page_count": len(doc),
        "full_text": full_text,
        "pages": pages,
        "links": links
    }