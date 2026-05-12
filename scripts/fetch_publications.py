#!/usr/bin/env python3
"""
fetch_publications.py — Fetches publications from SciX/ADS API
"""
import json, os, re, sys, requests
from datetime import datetime, timezone

LIBRARY_ID = "57nm1ouuTMusp62fvjiXYg"
ADS_API_BASE = "https://api.adsabs.harvard.edu/v1"
YOUR_LAST_NAME = "Helton"
OUTPUT_FILE = "data/publications.json"
FIELDS = ["bibcode","title","author","first_author","year","pubdate","pub","doi","identifier","abstract","citation_count","keyword","property","page","volume","issue"]

def get_token():
    t = os.environ.get("ADS_API_TOKEN", "")
    if not t: print("WARNING: ADS_API_TOKEN not set.")
    return t

def fetch_library_bibcodes(token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{ADS_API_BASE}/biblib/libraries/{LIBRARY_ID}"
    try:
        all_bib, start, page_size = [], 0, 200
        while True:
            r = requests.get(url, headers=headers, params={"rows": page_size, "start": start}, timeout=30)
            if r.status_code != 200:
                break
            data = r.json()
            docs = data.get("documents", [])
            all_bib.extend(docs)
            total = data.get("metadata", {}).get("num_documents", 0)
            start += page_size
            if start >= total or not docs:
                break
        if all_bib:
            return all_bib
    except Exception as e:
        print(f"Library API failed: {e}")
    return fetch_by_author(token)

def fetch_by_author(token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{ADS_API_BASE}/search/query", params={"q": 'author:"Helton, Jakob M."', "fl": "bibcode", "rows": 500, "sort": "date desc"}, headers=headers, timeout=30)
    r.raise_for_status()
    return [d["bibcode"] for d in r.json().get("response", {}).get("docs", [])]

def fetch_details(bibcodes, token):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    all_papers = []
    for i in range(0, len(bibcodes), 50):
        chunk = bibcodes[i:i+50]
        q = " OR ".join([f'bibcode:"{b}"' for b in chunk])
        try:
            r = requests.get(f"{ADS_API_BASE}/search/query", params={"q": q, "fl": ",".join(FIELDS), "rows": 50, "sort": "date desc"}, headers=headers, timeout=30)
            r.raise_for_status()
            all_papers.extend(r.json().get("response", {}).get("docs", []))
        except Exception as e:
            print(f"Error: {e}")
    return all_papers

def extract_arxiv(ids):
    if not ids: return ""
    for i in ids:
        if "arXiv:" in i: return i.replace("arXiv:", "")
        m = re.match(r"(\d{4}\.\d{4,5})", i)
        if m: return m.group(1)
    return ""

def is_first(p):
    fa = p.get("first_author", "")
    if YOUR_LAST_NAME.lower() in fa.lower(): return True
    a = p.get("author", [])
    return bool(a and YOUR_LAST_NAME.lower() in a[0].lower())

def fmt(p):
    ax = extract_arxiv(p.get("identifier", []))
    doi = p.get("doi", [])
    doi = doi[0] if isinstance(doi, list) and doi else (doi if isinstance(doi, str) else "")
    t = p.get("title", ["Untitled"])
    t = t[0] if isinstance(t, list) else t
    fa = is_first(p)
    fig = f"../assets/papers/{ax.replace('.','_')}/figures/fig1.png" if fa and ax else ""
    return {"bibcode": p.get("bibcode",""), "title": t, "authors": p.get("author",[]), "first_author": p.get("first_author",""), "year": p.get("year",""), "pubdate": p.get("pubdate",""), "journal": p.get("pub",""), "doi": doi, "arxiv_id": ax, "citation_count": p.get("citation_count",0), "abstract": p.get("abstract",""), "keywords": p.get("keyword",[]), "volume": p.get("volume",""), "page": p.get("page",[]), "property": p.get("property",[]), "is_first_author": fa, "figure_url": fig, "detail_url": ""}

def main():
    token = get_token()
    print("Fetching bibcodes...")
    bib = fetch_library_bibcodes(token)
    print(f"Found {len(bib)} bibcodes")
    if not bib: sys.exit(0)
    print("Fetching details...")
    papers = fetch_details(bib, token)
    formatted = sorted([fmt(p) for p in papers], key=lambda x: x.get("pubdate",""), reverse=True)
    fa_count = sum(1 for p in formatted if p["is_first_author"])
    out = {"last_updated": datetime.now(timezone.utc).isoformat(), "total_count": len(formatted), "first_author_count": fa_count, "publications": formatted}
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f: json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(formatted)} pubs ({fa_count} first-author)")

if __name__ == "__main__": main()
