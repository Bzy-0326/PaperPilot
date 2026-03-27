from datetime import date

import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "Mozilla/5.0"}


def _safe_get(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return ""


def _extract_text_or_empty(node):
    if not node:
        return ""
    return node.get_text(" ", strip=True)


def _extract_links_from_page(soup: BeautifulSoup) -> dict:
    pdf_url = ""
    arxiv_url = ""
    github_url = ""

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue

        full_href = f"https://huggingface.co{href}" if href.startswith("/") else href
        href_lower = full_href.lower()

        if not github_url and "github.com" in href_lower:
            github_url = full_href
        if not arxiv_url and "arxiv.org" in href_lower:
            arxiv_url = full_href
        if not pdf_url and (href_lower.endswith(".pdf") or "/pdf/" in href_lower):
            pdf_url = full_href

    return {
        "pdf_url": pdf_url,
        "arxiv_url": arxiv_url,
        "github_url": github_url,
    }


def _clean_candidate_text(text: str) -> str:
    text = " ".join((text or "").split())
    bad_prefixes = [
        "Hugging Face Models Datasets Spaces Buckets",
        "Hugging Face Models Datasets Spaces",
        "Models Datasets Spaces Buckets",
        "Enterprise Pricing Log In Sign Up Papers",
    ]
    for prefix in bad_prefixes:
        if text.startswith(prefix):
            text = text.split("Papers", 1)[-1].strip() if "Papers" in text else ""

    return " ".join(text.split()).strip()


def _looks_like_bad_navigation_text(text: str) -> bool:
    lowered = text.lower()
    bad_markers = [
        "hugging face",
        "models datasets spaces",
        "enterprise pricing",
        "log in sign up",
    ]
    return any(marker in lowered for marker in bad_markers)


def _looks_like_abstract(text: str) -> bool:
    if len(text) < 120:
        return False
    if _looks_like_bad_navigation_text(text):
        return False
    return True


def _extract_abstract(soup: BeautifulSoup) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        content = _clean_candidate_text(meta.get("content", ""))
        if _looks_like_abstract(content):
            return content

    selectors = [
        "[data-target='paper-abstract']",
        "[data-testid='paper-abstract']",
        "main p",
        "article p",
        "section p",
    ]

    candidates = []
    for selector in selectors:
        for node in soup.select(selector):
            text = _clean_candidate_text(_extract_text_or_empty(node))
            if _looks_like_abstract(text):
                candidates.append(text)

    if candidates:
        candidates.sort(key=len, reverse=True)
        return candidates[0]

    return ""


def fetch_hf_paper_detail(paper_url: str) -> dict:
    html = _safe_get(paper_url)
    if not html:
        return {
            "abstract": "",
            "pdf_url": "",
            "arxiv_url": "",
            "github_url": "",
        }

    soup = BeautifulSoup(html, "html.parser")
    links = _extract_links_from_page(soup)
    abstract = _extract_abstract(soup)

    return {
        "abstract": abstract,
        "pdf_url": links["pdf_url"],
        "arxiv_url": links["arxiv_url"],
        "github_url": links["github_url"],
    }


def fetch_hf_daily_papers(target_date: str | None = None) -> list:
    if not target_date:
        target_date = str(date.today())

    url = f"https://huggingface.co/papers/date/{target_date}"
    html = _safe_get(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    papers = []

    for h3 in soup.find_all("h3"):
        a = h3.find("a")
        if not a:
            continue

        title = a.get_text(strip=True)
        href = a.get("href", "").strip()
        if not href:
            continue

        paper_url = f"https://huggingface.co{href}" if href.startswith("/") else href
        detail = fetch_hf_paper_detail(paper_url)

        papers.append(
            {
                "source": "huggingface_papers",
                "source_paper_id": href.strip("/"),
                "title": title,
                "abstract": detail.get("abstract", ""),
                "authors": [],
                "paper_url": paper_url,
                "pdf_url": detail.get("pdf_url", ""),
                "arxiv_url": detail.get("arxiv_url", ""),
                "github_url": detail.get("github_url", ""),
                "source_date": target_date,
            }
        )

    return papers
