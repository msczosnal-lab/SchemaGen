"""Extract EPLAN API HTML docs to structured JSON for knowledge base."""
import json
import os
import re
from html.parser import HTMLParser

SRC = r"C:\Users\Filip\Desktop\startUp\AutoGen\EPLAN API docs"
OUT = r"C:\Users\Filip\Desktop\Cursor\SchemaGen\docs\eplan-kb\raw-extract.json"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
        self.in_pre = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag == "pre":
            self.in_pre = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "th"):
            self.parts.append("\n### ")
        elif tag == "tr":
            self.parts.append("\n")
        elif tag == "td":
            self.parts.append("| ")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in ("p", "br"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag == "pre":
            self.in_pre = False

    def handle_data(self, data):
        if self.skip:
            return
        t = data.strip()
        if t:
            self.parts.append(t + ("\n" if self.in_pre else " "))


def clean_html_entities(s: str) -> str:
    return (
        s.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
    )


def extract_file(path: str, fn: str) -> dict:
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()

    title_m = re.search(r"<title>([^<]+)</title>", html, re.I)
    title = title_m.group(1).strip() if title_m else fn

    bc_m = re.search(r"i-breadcrumbs-container[^>]*>(.*?)</div>", html, re.S)
    breadcrumb = ""
    if bc_m:
        breadcrumb = re.sub(r"<[^>]+>", " ", bc_m.group(1))
        breadcrumb = re.sub(r"\s+", " ", breadcrumb).strip()

    body_m = re.search(
        r'id="i-body-content"[^>]*>(.*?)(?:id="i-footer-content"|<script)',
        html,
        re.S,
    )
    body_html = body_m.group(1) if body_m else html

    ext = TextExtractor()
    ext.feed(body_html)
    text = "".join(ext.parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n +", "\n", text).strip()

    codes = re.findall(r"<pre[^>]*>(.*?)</pre>", body_html, re.S)
    code_blocks = []
    for c in codes:
        c = clean_html_entities(re.sub(r"<[^>]+>", "", c)).strip()
        if len(c) > 15:
            code_blocks.append(c)

    return {
        "file": fn,
        "title": title,
        "breadcrumb": breadcrumb,
        "text": text,
        "code": code_blocks,
    }


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    docs = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".html"):
            continue
        docs.append(extract_file(os.path.join(SRC, fn), fn))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(docs)} files -> {OUT}")


if __name__ == "__main__":
    main()
