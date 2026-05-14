"""
Generates a dark-mode OG image (1200x630 px) for social sharing.
Background: assets/images/hero_2.png (JADES NIRCam Compass Image)
Output: assets/images/og_image.png
"""
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
ACCENT   = (0, 168, 120)      # --accent   (#00a878)
TEXT_PRI = (235, 237, 242)    # --text-primary
TEXT_SEC = (160, 168, 178)    # --text-secondary

BASE_DIR   = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
IMG_DIR    = os.path.join(BASE_DIR, 'assets', 'images')
FONT_CACHE = os.path.join(BASE_DIR, '.font_cache')
OUT_PATH   = os.path.join(IMG_DIR, 'og_image.png')
HERO_PATH  = os.path.join(IMG_DIR, 'hero_2.png')

CREDIT_LINE = (
    "Credit · NASA, ESA, CSA, B. Robertson (UC Santa Cruz), B. Johnson (CfA), "
    "S. Tacchella (Cambridge), M. Rieke (Univ. of Arizona), D. Eisenstein (CfA); "
    "Image Processing: A. Pagan (STScI)"
)

# ── Font download (direct TTF from google/fonts GitHub repo) ──────────────────
_RAW = "https://raw.githubusercontent.com/google/fonts/main/ofl"
GOOGLE_FONTS = [
    (f"{_RAW}/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf", "PlayfairDisplay.ttf"),
    (f"{_RAW}/librefranklin/LibreFranklin%5Bwght%5D.ttf",     "LibreFranklin.ttf"),
    (f"{_RAW}/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",     "JetBrainsMono.ttf"),
]

def _fetch_font(url, dest):
    if os.path.exists(dest):
        return True
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            with open(dest, 'wb') as f:
                f.write(r.read())
        return True
    except Exception as e:
        print(f"  Font download failed ({os.path.basename(dest)}): {e}")
        return False

os.makedirs(FONT_CACHE, exist_ok=True)
_gf = {}
for _url, _fname in GOOGLE_FONTS:
    _dest = os.path.join(FONT_CACHE, _fname)
    _gf[_fname] = _dest if _fetch_font(_url, _dest) else None

def load_font(size, kind='serif'):
    """kind: 'serif' → Playfair Display, 'sans' → Libre Franklin, 'mono' → JetBrains Mono"""
    gf_key = {'serif': 'PlayfairDisplay.ttf',
               'sans':  'LibreFranklin.ttf',
               'mono':  'JetBrainsMono.ttf'}[kind]
    path = _gf.get(gf_key)
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    fallbacks = {
        'serif': ['/System/Library/Fonts/Supplemental/Palatino.ttc',
                  '/System/Library/Fonts/Supplemental/Georgia.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
                  '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'],
        'sans':  ['/System/Library/Fonts/Helvetica.ttc',
                  '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'],
        'mono':  ['/System/Library/Fonts/Menlo.ttc',
                  '/System/Library/Fonts/Monaco.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                  '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf'],
    }[kind]
    for p in fallbacks:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def text_height(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]

def draw_centered(draw, y, text, font, fill):
    w = draw.textlength(text, font=font)
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)

# ── Background (no overlay) ───────────────────────────────────────────────────
bg = Image.open(HERO_PATH).convert('RGB')
bw, bh = bg.size
scale = max(W / bw, H / bh)
bg = bg.resize((int(bw * scale), int(bh * scale)), Image.LANCZOS)
nw, nh = bg.size
left = (nw - W) // 2
top  = (nh - H) // 3
bg   = bg.crop((left, top, left + W, top + H))

img  = bg.copy()
draw = ImageDraw.Draw(img)

# ── Fonts ─────────────────────────────────────────────────────────────────────
f_role = load_font(18, 'mono')
f_name = load_font(60, 'serif')
f_url  = load_font(16, 'mono')
f_sub  = load_font(20, 'sans')

# Credit: auto-shrink to fit one line across full width (with 32 px side padding)
for _sz in range(13, 6, -1):
    f_credit = load_font(_sz, 'mono')
    if draw.textlength(CREDIT_LINE, font=f_credit) <= W - 32:
        break

# ── Layout (all centered) ─────────────────────────────────────────────────────
y = 110

# Role
role_text = "Astrophysicist  ·  Science Communicator  ·  Visual Artist"
draw_centered(draw, y, role_text, f_role, ACCENT)
y += text_height(draw, role_text, f_role) + 22

# Name
name_text = "Jakob M. Helton"
draw_centered(draw, y, name_text, f_name, TEXT_PRI)
y += text_height(draw, name_text, f_name) + 22

# URL
url_text = "jakobhelton.github.io"
draw_centered(draw, y, url_text, f_url, ACCENT)
y += text_height(draw, url_text, f_url) + 32

# Subtitle (centered, wrapped at 900 px)
subtitle = (
    "Studying the first stars, galaxies, galaxy clusters, and large-scale structure "
    "of the Universe using observations from the James Webb Space Telescope."
)
words = subtitle.split()
lines, current = [], ""
for word in words:
    test = (current + " " + word).strip()
    if draw.textlength(test, font=f_sub) > 900 and current:
        lines.append(current)
        current = word
    else:
        current = test
if current:
    lines.append(current)
for line in lines:
    draw_centered(draw, y, line, f_sub, TEXT_PRI)
    y += text_height(draw, line, f_sub) + 8

# Credit — single centered line at bottom
draw_centered(draw, H - 26, CREDIT_LINE, f_credit, TEXT_SEC)

# ── Save ─────────────────────────────────────────────────────────────────────
os.makedirs(IMG_DIR, exist_ok=True)
img.save(OUT_PATH, 'PNG', optimize=True, compress_level=9)
print(f'OG image saved to {OUT_PATH}')
