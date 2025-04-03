import requests
import os
import json
import time
import fitz  # PyMuPDF
import re
from pathlib import Path

SEARCH_TERMS = [
    "substance use disorder DSM-5",
    "addiction typologies rehab",
    "co-occurring disorders substance use",
    "alcohol withdrawal management",
    "opioid use disorder MAT",
    "evidence-based addiction treatment inpatient",
    "CBT addiction",
    "motivational interviewing substance use",
    "contingency management treatment outcomes",
    "12-step program alcohol use disorder",
    "trauma-informed care substance use",
    "ACE score addiction",
    "addiction borderline personality disorder",
    "dual diagnosis treatment",
    "relapse prevention strategies",
    "rehab patient personas",
    "long-term residential treatment outcomes",
    "young adults substance use treatment engagement",
    "court-mandated treatment effectiveness",
    "neurobiology of addiction"
]

OUTPUT_DIR = Path("rag_docs")
PDF_DIR = OUTPUT_DIR / "pdfs"
TEXT_DIR = OUTPUT_DIR / "clean_text"
CHUNK_FILE = OUTPUT_DIR / "chunks.jsonl"

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,authors,year,url,openAccessPdf"
HEADERS = {"User-Agent": "AddictionResearchBot/1.0"}

PDF_DIR.mkdir(parents=True, exist_ok=True)
TEXT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_papers(term, limit=10):
    url = f"{BASE_URL}?query={term}&limit={limit}&fields={FIELDS}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"⚠️ Failed search: {term} (status {response.status_code})")
        return []

def download_pdf(paper, index):
    pdf_info = paper.get("openAccessPdf")
    if pdf_info and pdf_info.get("url"):
        url = pdf_info["url"]
        local_path = PDF_DIR / f"{paper['paperId']}_{index}.pdf"
        try:
            response = requests.get(url)
            with open(local_path, "wb") as f:
                f.write(response.content)
            return local_path
        except Exception as e:
            print(f"⚠️ PDF download failed: {url}")
    return None

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        return "\n".join([page.get_text("text") for page in doc])
    except Exception as e:
        print(f"⚠️ Failed to read {pdf_path}")
        return ""

def clean_text(text):
    text = re.sub(r'(Page \d+|Author Manuscript|J [\w\s\(\)\.\-]+;\d+:\d+–\d+\.?|\bdoi:[\S]+)', '', text)
    text = re.sub(r'(Author|Manuscript|Correspondence|PMC)[\s\S]+?(?=(\n\n|$))', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'(?<=\w)-\n(?=\w)', '', text)
    return text.strip()

def chunk_text(text, max_chars=1000):
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 80 and not p.strip().startswith('FIG.') and not p.strip().startswith('TABLE')]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) < max_chars:
            current += para + "\n"
        else:
            chunks.append(current.strip())
            current = para + "\n"
    if current:
        chunks.append(current.strip())
    return chunks

def main():
    all_chunks = []
    for term in SEARCH_TERMS:
        print(f"🔎 Searching: {term}")
        papers = fetch_papers(term)
        for idx, paper in enumerate(papers):
            pdf_path = download_pdf(paper, idx)
            if pdf_path:
                raw_text = extract_text_from_pdf(pdf_path)
                cleaned = clean_text(raw_text)
                text_file = TEXT_DIR / (pdf_path.stem + ".txt")
                text_file.write_text(cleaned, encoding="utf-8")
                chunks = chunk_text(cleaned)
                for chunk in chunks:
                    all_chunks.append({
                        "text": chunk,
                        "metadata": {
                            "search_term": term,
                            "source": paper.get("title"),
                            "url": paper.get("url"),
                            "year": paper.get("year")
                        }
                    })
        time.sleep(1)

    print(f"💾 Saving {len(all_chunks)} chunks to {CHUNK_FILE}")
    with open(CHUNK_FILE, "w", encoding="utf-8") as f:
        for item in all_chunks:
            f.write(json.dumps(item) + "\n")

if __name__ == "__main__":
    main()
