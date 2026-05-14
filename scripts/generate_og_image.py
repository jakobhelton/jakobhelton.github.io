"""
Generates a dark-mode OG image (1200x630 px) for social sharing.
Background: assets/images/hero_2.png (JADES NIRCam Compass Image)
Output: assets/images/og_image.png
"""
import os
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

def load_font(size, kind='serif', bold=False):
    """kind: 'serif' → Playfair Display, 'sans' → Libre Franklin, 'mono' → JetBrains Mono"""
    gf_key = {'serif': 'PlayfairDisplay.ttf',
               'sans':  'LibreFranklin.ttf',
               'mono':  'JetBrainsMono.ttf'}[kind]
    path = _gf.get(gf_key)
    if path and os.path.exists(path):
        try:
            font = ImageFont.truetype(path, size)
            if bold:
                try:
                    font.set_variation_by_axes([700])
                except Exception:
                    pass
            return font
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

# ── Base fonts ────────────────────────────────────────────────────────────────
f_role = load_font(18, 'mono', bold=True)
f_sub  = load_font(20, 'sans', bold=True)
f_url  = load_font(18, 'mono', bold=True)

# Credit: auto-shrink to fit one line across full width (with 32 px side padding)
for _sz in range(13, 6, -1):
    f_credit = load_font(_sz, 'mono')
    if draw.textlength(CREDIT_LINE, font=f_credit) <= W - 32:
        break

# ── Text content ──────────────────────────────────────────────────────────────
role_text = "Astrophysicist  ·  Science Communicator  ·  Visual Artist"
name_text = "Jakob M. Helton"
url_text  = "jakobhelton.github.io"
subtitle  = (
    "Studying the first stars, galaxies, galaxy clusters, and large-scale structure "
    "of the Universe using observations from the James Webb Space Telescope."
)

# Auto-size name so it is slightly wider than the role line
role_w   = draw.textlength(role_text, font=f_role)
target_w = role_w * 1.08
f_name   = load_font(60, 'serif', bold=True)
for _sz in range(60, 110):
    _f = load_font(_sz, 'serif', bold=True)
    if draw.textlength(name_text, font=_f) >= target_w:
        f_name = _f
        break

# Subtitle split so "Universe" is first word of line 2
sub_lines = [
    "Studying the first stars, galaxies, galaxy clusters, and large-scale structure of the",
    "Universe using observations from the James Webb Space Telescope.",
]

# ── Layout: equal gap between lines; extra gap after the name ─────────────────
# Each entry: (text, font, color, gap_after)
gap       = 24
name_gap  = 52   # extra breathing room between name and description
all_lines = [
    (role_text,     f_role, ACCENT,   gap),
    (name_text,     f_name, TEXT_PRI, name_gap),
    (sub_lines[0],  f_sub,  TEXT_PRI, gap),
    (sub_lines[1],  f_sub,  TEXT_PRI, gap),
    (url_text,      f_url,  ACCENT,   0),
]

total_h  = sum(text_height(draw, t, f) for t, f, _, _ in all_lines)
total_h += sum(g for _, _, _, g in all_lines[:-1])
usable_h = H - 40   # leave 40 px at bottom for credit line
y = (usable_h - total_h) // 2

for text, font, color, gap_after in all_lines:
    draw_centered(draw, y, text, font, color)
    y += text_height(draw, text, font) + gap_after

# Credit — single centered line near the bottom
draw_centered(draw, H - 26, CREDIT_LINE, f_credit, TEXT_SEC)

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(IMG_DIR, exist_ok=True)
img.save(OUT_PATH, 'PNG', optimize=True, compress_level=9)
print(f'OG image saved to {OUT_PATH}')
