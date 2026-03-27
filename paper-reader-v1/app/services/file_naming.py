import re
from pathlib import Path


def sanitize_filename(text: str, max_len: int = 120) -> str:
    if not text:
        return "untitled_paper"

    text = text.strip()

    # 替换 Windows 不允许的文件名字符
    text = re.sub(r'[<>:"/\\\\|?*]', "_", text)

    # 把连续空白替换成下划线
    text = re.sub(r"\s+", "_", text)

    # 去掉连续下划线
    text = re.sub(r"_+", "_", text)

    # 去掉首尾下划线和点
    text = text.strip("._")

    if not text:
        text = "untitled_paper"

    return text[:max_len]


def guess_title_and_year_from_text(full_text: str) -> tuple[str, str]:
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    title = "untitled_paper"
    year = "unknown"

    # 取前面若干行，优先找标题
    head_lines = lines[:20]

    # 找年份
    for line in head_lines:
        m = re.search(r"\b(19|20)\d{2}\b", line)
        if m:
            year = m.group(0)
            break

    # 过滤常见非标题行
    bad_prefixes = [
        "published at",
        "arxiv",
        "abstract",
        "introduction",
        "keywords",
        "authors",
        "doi",
        "http",
        "www.",
    ]

    for line in head_lines:
        low = line.lower()

        if len(line) < 8:
            continue
        if any(low.startswith(prefix) for prefix in bad_prefixes):
            continue
        if re.search(r"@[A-Za-z0-9_]+", line):
            continue

        # 选第一条足够长、看起来像标题的行
        title = line
        break

    return sanitize_filename(title), year


def build_standard_pdf_name(full_text: str, original_name: str) -> str:
    title, year = guess_title_and_year_from_text(full_text)

    suffix = Path(original_name).suffix or ".pdf"
    if suffix.lower() != ".pdf":
        suffix = ".pdf"

    if year == "unknown":
        return f"{title}{suffix}"

    return f"{year}_{title}{suffix}"


def sanitize_download_title(text: str, max_len: int = 120) -> str:
    if not text:
        return "untitled-paper"

    text = text.strip()
    text = re.sub(r'[<>:"/\\\\|?*]', " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ._-")

    if not text:
        text = "untitled-paper"

    return text[:max_len]


def build_reader_download_pdf_name(
    source_date: str | None,
    title: str,
    original_name: str = ".pdf",
) -> str:
    clean_title = sanitize_download_title(title)
    clean_date = (source_date or "").strip() or "unknown-date"

    suffix = Path(original_name).suffix or ".pdf"
    if suffix.lower() != ".pdf":
        suffix = ".pdf"

    return f"{clean_date}-RD-{clean_title}{suffix}"
