#!/usr/bin/env python3
"""
migrate_content.py
Fetches all blog posts and art pages from the live jakobhelton.github.io site
and generates HTML files in the new template format.

Run from the repository root:
  pip install requests beautifulsoup4 lxml
  python scripts/migrate_content.py
"""

import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

SITE_URL = "https://jakobhelton.github.io"
OUTPUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pages to migrate
BLOG_POSTS = [
    "blog/discovery_jades_gs_z14_0",
    "blog/interview_jades_gs_z14_0",
    "blog/2025_books_in_review",
    "blog/2025_music_in_review",
    "blog/2024_books_in_review",
    "blog/2024_music_in_review",
]

ART_PAGES = [
    "art/painting",
    "art/theamericanmidwestsouthwest",
    "art/photographyanalog",
    "art/photographydigital",
    "art/digitalart",
    "art/homemovies",
]


def fetch_page(path):
    """Fetch a page and return BeautifulSoup object."""
    url = f"{SITE_URL}/{path}/"
    print(f"  Fetching: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def extract_blog_content(soup):
    """Extract title, date, and main content from a Hugo blog page."""
    title_el = soup.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else "Untitled"

    # Find date
    date = ""
    for el in soup.select("time, .article-date, .page-header-date"):
        date = el.get_text(strip=True)
        if date:
            break
    if not date:
        # Try to find date text pattern
        text = soup.get_text()
        match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4})', text)
        if match:
            date = match.group(1)

    # Extract the article body — look for the main content area
    # Hugo academic theme puts content in article or .article-content
    content_el = soup.select_one(".article-content, article .prose, .page-body")
    if not content_el:
        # Fallback: find the main content between the header and footer
        main = soup.select_one("main, .page-content, article")
        if main:
            content_el = main

    if content_el:
        # Clean up the content
        # Remove nav elements, footers, author blocks
        for tag in content_el.select("nav, footer, .author-card, .article-widget, .related-content, .page-footer"):
            tag.decompose()

        # Convert images: make src absolute if relative
        for img in content_el.select("img"):
            src = img.get("src", "")
            if src and not src.startswith("http"):
                img["src"] = f"{SITE_URL}/{src.lstrip('/')}"
            img["loading"] = "lazy"
            img["style"] = "max-width:100%; height:auto; border-radius:8px;"

        # Convert links: make href absolute if relative to old site
        for a in content_el.select("a"):
            href = a.get("href", "")
            if href.startswith("/") and not href.startswith("//"):
                # Keep internal links but note they may need updating
                pass

        content_html = str(content_el)
    else:
        content_html = "<p>Content could not be extracted. Please add content manually.</p>"

    return title, date, content_html


def extract_art_content(soup, page_path):
    """Extract title and gallery images from an art page."""
    title_el = soup.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else "Gallery"

    # Find all images in the gallery
    images = []
    for img in soup.select("img"):
        src = img.get("src", "")
        if not src:
            continue
        # Skip tiny icons and avatars
        if "avatar" in src or "icon" in src:
            continue
        if not src.startswith("http"):
            src = f"{SITE_URL}/{src.lstrip('/')}"
        alt = img.get("alt", "")
        images.append({"src": src, "alt": alt})

    return title, images


def generate_blog_html(title, date, content, depth=2):
    """Generate a complete blog post page."""
    prefix = "../" * depth
    return f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Jakob M. Helton</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>🌌</text></svg>">
  <link rel="stylesheet" href="{prefix}css/main.css">
  <link rel="stylesheet" href="{prefix}css/pages.css">
  <link rel="stylesheet" href="{prefix}css/responsive.css">
</head>
<body>
<canvas id="star-field" aria-hidden="true"></canvas>
<div class="scroll-progress" aria-hidden="true"></div>
<nav class="site-nav">
  <a href="{prefix}" class="nav-logo"><span class="logo-icon"></span> Jakob M. Helton</a>
  <button class="nav-menu-toggle" aria-label="Toggle menu" aria-expanded="false">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  </button>
  <ul class="nav-links">
    <li><a href="{prefix}">Home</a></li>
    <li><a href="{prefix}biography/">Biography</a></li>
    <li><a href="{prefix}publications/">Publications</a></li>
    <li><a href="{prefix}blog/" class="active">Blog</a></li>
    <li><a href="{prefix}presentations/">Presentations</a></li>
    <li><a href="{prefix}art/">Art</a></li>
    <li><button class="theme-toggle" aria-label="Toggle theme"></button></li>
  </ul>
</nav>
<main class="page-content">
  <div class="container container--narrow">
    <div class="page-header reveal">
      <p class="section-label">Blog</p>
      <h1>{title}</h1>
      {f'<p class="text-secondary" style="font-family:var(--font-mono); font-size:0.8rem;">{date}</p>' if date else ''}
    </div>
    <article class="blog-article reveal">
      {content}
    </article>
    <div class="mt-2xl mb-xl">
      <a href="../" class="btn btn--outline btn--small">&larr; Back to Blog</a>
    </div>
  </div>
</main>
<footer class="site-footer">
  <div class="container">
    <p>&copy; 2026 Jakob M. Helton. Licensed under <a href="https://creativecommons.org/licenses/by-nc-nd/4.0" target="_blank" rel="noopener">CC BY-NC-ND 4.0</a>.</p>
  </div>
</footer>
<script src="{prefix}js/main.js"></script>
<script src="{prefix}js/stars.js"></script>
</body>
</html>'''


def generate_art_html(title, images, depth=2):
    """Generate an art gallery page."""
    prefix = "../" * depth
    gallery_html = ""
    for img in images:
        gallery_html += f'''
      <div class="art-gallery-item">
        <img src="{img['src']}" alt="{img['alt']}" loading="lazy">
      </div>'''

    return f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Jakob M. Helton</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>🌌</text></svg>">
  <link rel="stylesheet" href="{prefix}css/main.css">
  <link rel="stylesheet" href="{prefix}css/pages.css">
  <link rel="stylesheet" href="{prefix}css/responsive.css">
  <style>
    .art-gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: var(--space-lg); }}
    .art-gallery-item {{ border-radius: var(--border-radius-lg); overflow: hidden; border: 1px solid var(--border); cursor: pointer; transition: all var(--transition-med); }}
    .art-gallery-item:hover {{ border-color: var(--border-accent); box-shadow: var(--shadow-glow); transform: translateY(-3px); }}
    .art-gallery-item img {{ width: 100%; height: auto; display: block; }}
  </style>
</head>
<body>
<canvas id="star-field" aria-hidden="true"></canvas>
<div class="scroll-progress" aria-hidden="true"></div>
<nav class="site-nav">
  <a href="{prefix}" class="nav-logo"><span class="logo-icon"></span> Jakob M. Helton</a>
  <button class="nav-menu-toggle" aria-label="Toggle menu" aria-expanded="false">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  </button>
  <ul class="nav-links">
    <li><a href="{prefix}">Home</a></li>
    <li><a href="{prefix}biography/">Biography</a></li>
    <li><a href="{prefix}publications/">Publications</a></li>
    <li><a href="{prefix}blog/">Blog</a></li>
    <li><a href="{prefix}presentations/">Presentations</a></li>
    <li><a href="{prefix}art/" class="active">Art</a></li>
    <li><button class="theme-toggle" aria-label="Toggle theme"></button></li>
  </ul>
</nav>
<main class="page-content">
  <div class="container">
    <div class="page-header reveal">
      <p class="section-label">Art</p>
      <h1>{title}</h1>
    </div>
    <div class="art-gallery reveal">
      {gallery_html}
    </div>
    <div class="mt-2xl mb-xl">
      <a href="../" class="btn btn--outline btn--small">&larr; Back to Art</a>
    </div>
  </div>
</main>
<footer class="site-footer">
  <div class="container">
    <p>&copy; 2026 Jakob M. Helton. Licensed under <a href="https://creativecommons.org/licenses/by-nc-nd/4.0" target="_blank" rel="noopener">CC BY-NC-ND 4.0</a>.</p>
  </div>
</footer>
<script src="{prefix}js/main.js"></script>
<script src="{prefix}js/stars.js"></script>
</body>
</html>'''


def main():
    print("=" * 60)
    print("Content Migration: jakobhelton.github.io")
    print("=" * 60)

    # Migrate blog posts
    print(f"\\nMigrating {len(BLOG_POSTS)} blog posts...")
    for path in BLOG_POSTS:
        soup = fetch_page(path)
        if not soup:
            continue

        title, date, content = extract_blog_content(soup)
        html = generate_blog_html(title, date, content)

        out_path = os.path.join(OUTPUT_DIR, path, "index.html")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ {path} → {title}")

        time.sleep(1)  # Be polite

    # Migrate art pages
    print(f"\\nMigrating {len(ART_PAGES)} art pages...")
    for path in ART_PAGES:
        soup = fetch_page(path)
        if not soup:
            continue

        title, images = extract_art_content(soup, path)
        html = generate_art_html(title, images)

        out_path = os.path.join(OUTPUT_DIR, path, "index.html")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ {path} → {title} ({len(images)} images)")

        time.sleep(1)

    print(f"\\n{'=' * 60}")
    print("Migration complete!")
    print("Review the generated HTML files and adjust as needed.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
