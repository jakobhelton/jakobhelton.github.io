#!/usr/bin/env python3
"""
extract_figures.py — Downloads arXiv PDFs for first-author papers and extracts figures.
"""
import json, os, sys, time, requests, fitz
from PIL import Image
from io import BytesIO

PUBLICATIONS_FILE = "data/publications.json"
PAPERS_DIR = "assets/papers"
MIN_SIZE = (150, 150)
MAX_IMAGES = 20

def load_papers():
    if not os.path.exists(PUBLICATIONS_FILE): print(f"{PUBLICATIONS_FILE} not found."); return []
    with open(PUBLICATIONS_FILE) as f: data = json.load(f)
    return [p for p in data.get("publications",[]) if p.get("is_first_author") and p.get("arxiv_id")]

def download_pdf(ax, dest):
    if os.path.exists(dest): return True
    try:
        r = requests.get(f"https://arxiv.org/pdf/{ax}", timeout=60, stream=True); r.raise_for_status()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            for c in r.iter_content(8192): f.write(c)
        return True
    except Exception as e: print(f"  Error: {e}"); return False

def extract_images(pdf_path, out_dir):
    if not os.path.exists(pdf_path): return 0
    os.makedirs(out_dir, exist_ok=True)
    if [f for f in os.listdir(out_dir) if f.endswith('.png')]: return -1
    doc = fitz.open(pdf_path)
    count = 0
    for pn in range(len(doc)):
        if count >= MAX_IMAGES: break
        for _, img_info in enumerate(doc[pn].get_images(full=True)):
            if count >= MAX_IMAGES: break
            try:
                bi = doc.extract_image(img_info[0])
                if not bi: continue
                img = Image.open(BytesIO(bi["image"]))
                if img.width < MIN_SIZE[0] or img.height < MIN_SIZE[1]: continue
                count += 1
                if img.mode in ("CMYK","P","LA","PA"): img = img.convert("RGB")
                img.save(os.path.join(out_dir, f"fig{count}.png"), "PNG", optimize=True)
            except: pass
    doc.close()
    return count

def main():
    papers = load_papers()
    print(f"Found {len(papers)} first-author papers")
    for i, p in enumerate(papers):
        ax = p["arxiv_id"]; sid = ax.replace(".","_")
        pdf = os.path.join(PAPERS_DIR, sid, "paper.pdf")
        figs = os.path.join(PAPERS_DIR, sid, "figures")
        print(f"[{i+1}/{len(papers)}] {ax}")
        if download_pdf(ax, pdf): extract_images(pdf, figs)
        time.sleep(3)

if __name__ == "__main__": main()
