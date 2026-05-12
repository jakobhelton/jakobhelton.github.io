#!/usr/bin/env python3
"""
fetch_jwst_image.py — Fetches latest JWST featured image from NASA.
"""
import json, os, random, requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

OUTPUT_FILE = "data/jwst_image.json"
NASA_IMAGE_API = "https://images-api.nasa.gov/search"

def abbrev_name(name):
    """'Firstname Lastname (Inst)' -> 'F. Lastname (Inst)'"""
    inst = ""
    if "(" in name:
        i = name.index("(")
        inst = " " + name[i:].strip()
        name = name[:i].strip()
    parts = name.split()
    if len(parts) >= 2:
        return parts[0][0] + ". " + " ".join(parts[1:]) + inst
    return name + inst

def abbrev_credit_names(text):
    """Abbreviate first names in a comma/semicolon-separated credit string."""
    orgs = {"nasa", "esa", "csa", "stsci", "ipac", "caltech", "jpl"}
    def proc_segment(seg):
        seg = seg.strip()
        # Keep "Image Processing:" label prefix intact
        prefix = ""
        for label in ("Image Processing:", "Image:"):
            if seg.startswith(label):
                prefix = label + " "
                seg = seg[len(label):].strip()
                break
        # Split by comma, abbreviate each non-org name
        items = [s.strip() for s in seg.split(",")]
        out = []
        for item in items:
            base = item.split("(")[0].strip().lower().replace(".", "")
            if base in orgs or not item:
                out.append(item)
            else:
                out.append(abbrev_name(item))
        return prefix + ", ".join(out)
    return "; ".join(proc_segment(s) for s in text.split(";"))

def build_credit(d):
    parts = ["NASA, ESA, CSA, STScI"]
    photographer = d.get("photographer", "").strip()
    secondary = d.get("secondary_creator", "").strip()
    if secondary:
        parts.append("Image Processing: " + abbrev_name(secondary))
    elif photographer and photographer.lower() not in ("nasa", "nasa/esa", "nasa, esa, csa, stsci"):
        parts.append(abbrev_name(photographer))
    return "; ".join(parts)

def try_api():
    try:
        r = requests.get(NASA_IMAGE_API, params={"q":"James Webb Space Telescope","media_type":"image","page_size":5,"year_start":str(datetime.now().year-1)}, timeout=15)
        r.raise_for_status()
        for item in r.json().get("collection",{}).get("items",[]):
            d = item.get("data",[{}])[0]; links = item.get("links",[])
            if not links: continue
            url = links[0].get("href","")
            if not url: continue
            desc = d.get("description","")
            if len(desc) > 300: desc = desc[:297]+"..."
            nid = d.get("nasa_id","")
            return {"title": d.get("title","JWST Image"), "description": desc, "image_url": url, "credit": build_credit(d), "link": f"https://images.nasa.gov/details/{nid}" if nid else "https://science.nasa.gov/mission/webb/", "source": "NASA Images API", "fetched_at": datetime.now(timezone.utc).isoformat()}
    except Exception as e: print(f"API failed: {e}")
    return None

def fallback():
    imgs = [
        {"title":"Webb's First Deep Field","description":"The deepest infrared image of the distant universe to date.","image_url":"https://stsci-opo.org/STScI-01G7JJADTH90FR98AKKJFKSS0R.png","link":"https://science.nasa.gov/missions/webb/nasas-webb-delivers-deepest-infrared-image-of-universe-yet/"},
        {"title":"Cosmic Cliffs in the Carina Nebula","description":"The edge of a nearby star-forming region NGC 3324.","image_url":"https://stsci-opo.org/STScI-01G8GZR0S3Y2SHKHTHHRQ5F3XW.png","link":"https://science.nasa.gov/missions/webb/cosmic-cliffs-glittering-landscape-of-star-birth/"},
        {"title":"Pillars of Creation (NIRCam)","description":"Webb's view of the iconic Pillars of Creation.","image_url":"https://stsci-opo.org/STScI-01GF1RQZ8JFGKQXMVMFZWGHEGD.png","link":"https://science.nasa.gov/missions/webb/webb-takes-star-filled-portrait-of-pillars-of-creation/"},
        {"title":"Tarantula Nebula","description":"A mosaic stretching 340 light-years across.","image_url":"https://stsci-opo.org/STScI-01GA76Q01D09HFEV174SVMQDMV.png","link":"https://science.nasa.gov/missions/webb/webb-inspects-the-heart-of-the-phantom-galaxy/"},
    ]
    c = random.choice(imgs)
    c.update({"credit":"NASA, ESA, CSA, STScI","source":"curated fallback","fetched_at":datetime.now(timezone.utc).isoformat()})
    return c

def main():
    print("Fetching JWST image...")
    result = try_api() or fallback()
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f: json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Saved: {result.get('title','N/A')}")

if __name__ == "__main__": main()
