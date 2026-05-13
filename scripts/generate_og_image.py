"""
Generates a dark-mode OG image (1200x630 px) for social sharing.
Output: assets/images/og_image.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG = (8, 9, 12)          # #08090c
ACCENT = (0, 168, 120)   # #00a878
TEXT_PRI = (235, 237, 242)
TEXT_SEC = (140, 148, 158)
BORDER = (30, 34, 40)

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images')
OUT_PATH = os.path.join(OUT_DIR, 'og_image.png')

def load_font(size, bold=False):
    candidates = [
        '/System/Library/Fonts/Supplemental/Palatino.ttc',
        '/System/Library/Fonts/Supplemental/Georgia.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

img = Image.new('RGB', (W, H), BG)
draw = ImageDraw.Draw(img)

# Subtle star field
import random
random.seed(42)
for _ in range(300):
    x, y = random.randint(0, W), random.randint(0, H)
    r = random.random()
    if r < 0.7:
        brightness = random.randint(60, 120)
    elif r < 0.9:
        brightness = random.randint(120, 180)
    else:
        brightness = random.randint(180, 240)
    draw.point((x, y), fill=(brightness, brightness, brightness))

# Border
draw.rectangle([0, 0, W - 1, H - 1], outline=BORDER, width=2)

# Accent top bar
draw.rectangle([0, 0, W, 4], fill=ACCENT)

# Name
font_name = load_font(62, bold=True)
draw.text((80, 160), 'Jakob M. Helton', font=font_name, fill=TEXT_PRI)

# Title
font_title = load_font(28)
draw.text((82, 248), 'Astrophysicist', font=font_title, fill=ACCENT)

# Divider
draw.rectangle([80, 302, 480, 304], fill=BORDER)

# Affiliation
font_aff = load_font(22)
draw.text((82, 320), 'Evolving Universe Postdoctoral Fellow', font=font_aff, fill=TEXT_SEC)
draw.text((82, 352), 'The Pennsylvania State University', font=font_aff, fill=TEXT_SEC)

# URL
font_url = load_font(20)
draw.text((82, 420), 'jakobhelton.github.io', font=font_url, fill=ACCENT)

# Decorative accent circle (bottom-right)
draw.ellipse([900, 350, 1180, 610], outline=(*ACCENT, 30), width=1)
draw.ellipse([960, 400, 1140, 570], outline=(*BORDER,), width=1)

os.makedirs(OUT_DIR, exist_ok=True)
img.save(OUT_PATH, 'PNG', optimize=True)
print(f'OG image saved to {OUT_PATH}')
