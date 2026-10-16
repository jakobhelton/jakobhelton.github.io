#!/usr/bin/env python3
"""
extract_figures.py — Downloads arXiv PDFs and TeX sources for first-author papers and
extracts the paper's figures, in the order they appear in the TeX, as PNGs.

Figures come from the arXiv e-print (TeX source): every \\includegraphics / \\plotone /
\\plottwo reference in the main .tex (following \\input / \\include) is resolved to a
PNG, JPG, or PDF file and saved as assets/papers/<id>/figures/figN.png.
Vector PDFs are rasterized with PyMuPDF.

Papers whose figures were already extracted from TeX (marked by figures/.from_tex) are
skipped; pass --force to redo everything.
"""
import json, os, re, shutil, sys, tarfile, tempfile, time, gzip, requests
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf
from PIL import Image

PUBLICATIONS_FILE = "data/publications.json"
PAPERS_DIR = "assets/papers"
MARKER = ".from_tex"
MIN_SIZE = (150, 150)
MAX_IMAGES = 30
MAX_WIDTH = 2000
PDF_DPI = 200
MAX_SOURCE_BYTES = 300 * 1024 * 1024
EXTENSIONS = ["", ".pdf", ".png", ".jpg", ".jpeg"]
SKIP_NAMES = re.compile(r"orcid|logo|badge", re.I)
HEADERS = {"User-Agent": "Mozilla/5.0 (jakobhelton.github.io figure extractor)"}

GRAPHIC_RE = re.compile(r"\\(?:includegraphics|plotone|plottwo|epsfbox)\*?\s*(?:\[[^\]]*\])?\s*((?:\{[^{}]*\}\s*)+)")
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\{[^{}]*\})+)\}")


def load_papers():
    if not os.path.exists(PUBLICATIONS_FILE): print(f"{PUBLICATIONS_FILE} not found."); return []
    with open(PUBLICATIONS_FILE) as f: data = json.load(f)
    return [p for p in data.get("publications", []) if p.get("is_first_author") and p.get("arxiv_id")]


def download(url, dest, max_bytes=None):
    try:
        with requests.get(url, headers=HEADERS, timeout=60, stream=True) as r:
            r.raise_for_status()
            size = 0
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                for c in r.iter_content(1 << 16):
                    size += len(c)
                    if max_bytes and size > max_bytes: raise ValueError("source too large")
                    f.write(c)
        return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False


def extract_source(archive, dest):
    """Extract an e-print (tar.gz, or a single gzipped .tex) into dest; refuse unsafe paths."""
    root = os.path.realpath(dest)
    try:
        with tarfile.open(archive) as tar:
            for m in tar.getmembers():
                target = os.path.realpath(os.path.join(dest, m.name))
                if not (m.isfile() or m.isdir()) or not (target == root or target.startswith(root + os.sep)):
                    continue
                tar.extract(m, dest, filter="data") if hasattr(tarfile, "data_filter") else tar.extract(m, dest)
        return True
    except tarfile.ReadError:
        pass
    try:
        with gzip.open(archive, "rb") as g, open(os.path.join(dest, "main.tex"), "wb") as f:
            shutil.copyfileobj(g, f)
        return True
    except Exception as e:
        print(f"  Error extracting source: {e}")
        return False


def read_tex(path):
    with open(path, encoding="utf-8", errors="ignore") as f: text = f.read()
    return re.sub(r"(?<!\\)%.*", "", text)  # drop comments


def find_main_tex(src):
    best = None
    for dirpath, _, files in os.walk(src):
        for fn in files:
            if not fn.endswith(".tex"): continue
            path = os.path.join(dirpath, fn)
            text = read_tex(path)
            if r"\documentclass" in text and r"\begin{document}" in text:
                if best is None or len(text) > best[0]: best = (len(text), path)
    return best[1] if best else None


def expand_tex(path, src, seen=None):
    """Return the main tex text with \\input/\\include recursively inlined."""
    seen = seen or set()
    if path in seen or not os.path.exists(path): return ""
    seen.add(path)
    text = read_tex(path)

    def repl(m):
        name = m.group(1).strip()
        for cand in (name, name + ".tex"):
            for base in (os.path.dirname(path), src):
                p = os.path.join(base, cand)
                if os.path.isfile(p): return expand_tex(p, src, seen)
        return ""
    return INPUT_RE.sub(repl, text)


def resolve_graphic(name, src, search_dirs):
    name = name.strip()
    for d in search_dirs:
        for ext in EXTENSIONS:
            p = os.path.realpath(os.path.join(d, name + ext))
            if p.startswith(os.path.realpath(src) + os.sep) and os.path.isfile(p) and \
               p.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
                return p
    return None


def figure_files(src):
    """Ordered, de-duplicated list of graphic files referenced by the paper's TeX."""
    main = find_main_tex(src)
    if not main: return []
    text = expand_tex(main, src)
    search_dirs = [os.path.dirname(main), src]
    for m in GRAPHICSPATH_RE.finditer(text):
        for d in re.findall(r"\{([^{}]*)\}", m.group(1)):
            search_dirs.append(os.path.join(os.path.dirname(main), d))
    files, seen = [], set()
    for m in GRAPHIC_RE.finditer(text):
        for name in re.findall(r"\{([^{}]*)\}", m.group(1)):
            if SKIP_NAMES.search(name): continue
            p = resolve_graphic(name, src, search_dirs)
            if p and p not in seen:
                seen.add(p); files.append(p)
    return files


def to_png(path, out_path):
    """Convert a PNG/JPG/PDF graphic to a PNG. Returns True if a usable image was written."""
    if path.lower().endswith(".pdf"):
        doc = pymupdf.open(path)
        pix = doc[0].get_pixmap(dpi=PDF_DPI, alpha=False)
        doc.close()
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    else:
        img = Image.open(path)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.split()[-1]); img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
    if img.width < MIN_SIZE[0] or img.height < MIN_SIZE[1]: return False
    if img.width > MAX_WIDTH:
        img = img.resize((MAX_WIDTH, round(img.height * MAX_WIDTH / img.width)), Image.LANCZOS)
    img.save(out_path, "PNG", optimize=True)
    return True


def extract_figures(ax, figs_dir):
    """Download the e-print for ax and rebuild figs_dir from its figures. Returns count."""
    with tempfile.TemporaryDirectory() as tmp:
        archive = os.path.join(tmp, "source")
        src = os.path.join(tmp, "src"); os.makedirs(src)
        if not download(f"https://arxiv.org/e-print/{ax}", archive, MAX_SOURCE_BYTES): return 0
        if not extract_source(archive, src): return 0
        out = os.path.join(tmp, "out"); os.makedirs(out)
        count = 0
        for path in figure_files(src):
            if count >= MAX_IMAGES: break
            try:
                if to_png(path, os.path.join(out, f"fig{count + 1}.png")): count += 1
            except Exception as e:
                print(f"  Skipped {os.path.basename(path)}: {e}")
        if count == 0: return 0
        open(os.path.join(out, MARKER), "w").close()
        if os.path.isdir(figs_dir): shutil.rmtree(figs_dir)  # only after extraction succeeded
        os.makedirs(os.path.dirname(figs_dir), exist_ok=True)
        shutil.copytree(out, figs_dir)
        return count


def main():
    force = "--force" in sys.argv
    papers = load_papers()
    print(f"Found {len(papers)} first-author papers")
    for i, p in enumerate(papers):
        ax = p["arxiv_id"]; sid = ax.replace(".", "_")
        pdf = os.path.join(PAPERS_DIR, sid, "paper.pdf")
        figs = os.path.join(PAPERS_DIR, sid, "figures")
        print(f"[{i+1}/{len(papers)}] {ax}")
        if not os.path.exists(pdf): download(f"https://arxiv.org/pdf/{ax}", pdf)
        if not force and os.path.exists(os.path.join(figs, MARKER)): continue
        n = extract_figures(ax, figs)
        print(f"  {n} figures" if n else "  No figures extracted; existing figures left untouched")
        time.sleep(3)


if __name__ == "__main__":
    main()
