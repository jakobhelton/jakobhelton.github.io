#!/usr/bin/env python3
"""fetch_nasa_image.py — Fetches the NASA Image of the Day from nasa.gov."""

import io, json, os, re, requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image

IOTD_PAGE = "https://www.nasa.gov/image-of-the-day/"
JSON_OUT = "data/nasa_image.json"
IMG_DIR = "assets/images"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def find_latest_article():
    r = requests.get(IOTD_PAGE, headers=UA, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "nasa.gov/image-article/" in href or (href.startswith("/") and "/image-article/" in href):
            if href.startswith("/"):
                href = "https://www.nasa.gov" + href
            return href
    return None

def _para_to_html(p):
    """Return paragraph inner content as HTML, preserving <a> hyperlinks with absolute URLs."""
    parts = []
    for child in p.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag) and child.name == "a":
            href = child.get("href", "")
            if href and href.startswith("/"):
                href = "https://www.nasa.gov" + href
            text = child.get_text()
            parts.append(f'<a href="{href}" target="_blank" rel="noopener">{text}</a>' if href else text)
        else:
            parts.append(child.get_text(" "))
    return "".join(parts).strip()


def parse_article(url):
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title = ""
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    if not title:
        og = soup.find("meta", property="og:title")
        if og:
            title = og.get("content", "").split(" | ")[0].strip()

    # Featured image: og:image is usually the highest quality
    image_url = ""
    og_img = soup.find("meta", property="og:image")
    if og_img:
        image_url = og_img.get("content", "")
    if not image_url:
        for img in soup.select("figure img, .wp-post-image, article img, main img"):
            src = img.get("src", "") or img.get("data-src", "")
            if src and not src.endswith((".gif", ".svg")):
                image_url = src
                break

    # Body text and credit
    body_sel = soup.select_one(
        "div.entry-content, div.article-body, div.wp-block-post-content, main article, .hds-article"
    )
    paragraphs, credit = [], ""
    if body_sel:
        for p in body_sel.find_all("p"):
            text = p.get_text(" ", strip=True)
            if not text:
                continue
            # Skip reading-time metadata (e.g. "2 min read")
            if re.match(r"^\d+\s+min\s+read$", text, re.IGNORECASE):
                continue
            # Skip short byline/author paragraphs (no sentence-ending punctuation)
            if len(text) < 50 and not re.search(r"[.!?]", text):
                continue
            if re.match(r"^(image credit[s]?|credits?|photo credit[s]?)[\s:]", text, re.IGNORECASE):
                raw = re.sub(r"^(image credit[s]?|credits?|photo credit[s]?)[\s:]+", "", text, flags=re.IGNORECASE).strip()
                credit = raw
            else:
                paragraphs.append(_para_to_html(p))

    caption = "\n\n".join(paragraphs)
    if len(caption) > 2000:
        caption = caption[:1997] + "…"

    if not credit:
        credit = "NASA"

    return {
        "title": title,
        "caption": caption,
        "credit": credit,
        "image_url": image_url,
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

MAX_PX = 3840       # cap longest edge at 4K
JPEG_QUALITY = 85   # JPEG quality for saved output

def download_image(url):
    r = requests.get(url, headers=UA, timeout=45, stream=True)
    r.raise_for_status()
    raw = io.BytesIO(r.content)

    img = Image.open(raw)
    # Flatten transparency (PNG/WebP with alpha → white background)
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Downscale if either dimension exceeds MAX_PX
    w, h = img.size
    if max(w, h) > MAX_PX:
        scale = MAX_PX / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Remove stale hero_0 files with other extensions; we always write .jpg now
    for old_ext in ("jpg", "png", "webp"):
        old = os.path.join(IMG_DIR, f"hero_0.{old_ext}")
        if os.path.exists(old):
            os.remove(old)

    path = os.path.join(IMG_DIR, "hero_0.jpg")
    img.save(path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    size_mb = os.path.getsize(path) / 1_000_000
    print(f"  Compressed to {img.size[0]}×{img.size[1]} px, {size_mb:.2f} MB")
    return "assets/images/hero_0.jpg"

def main():
    print("Fetching NASA Image of the Day…")
    url = find_latest_article()
    if not url:
        print(f"ERROR: could not locate an image-article link on {IOTD_PAGE}")
        return
    print(f"  Article: {url}")

    data = parse_article(url)
    print(f"  Title:   {data['title']}")

    if data["image_url"]:
        try:
            local = download_image(data["image_url"])
            data["local_image"] = local
            print(f"  Saved:   {local}")
        except Exception as e:
            print(f"  Image download failed: {e}")
            data["local_image"] = None
    else:
        print("  No image URL found")
        data["local_image"] = None

    os.makedirs(os.path.dirname(JSON_OUT), exist_ok=True)
    with open(JSON_OUT, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Written: {JSON_OUT}")

if __name__ == "__main__":
    main()
