# jakobhelton.github.io

This is the source repository for my personal website at [jakobhelton.github.io](https://jakobhelton.github.io). I am an astrophysicist and Evolving Universe Postdoctoral Fellow at Penn State. The site covers my research, publications, presentations, blog, and art.

## Setup

```bash
# 1. Add images to assets/images/:
#    avatar.jpg              — headshot (biography page)
#    hero_1.png              — hero slideshow (landing page)
#    hero_2.png              — hero slideshow (landing page)

# 2. Add art gallery thumbnails (each gallery uses its own featured.jpg):
#    art/painting/featured.jpg
#    art/theamericanmidwestsouthwest/featured.jpg
#    art/photographyanalog/featured.jpg
#    art/photographydigital/featured.jpg
#    art/digitalart/featured.jpg
#    art/homemovies/featured.jpg

# 3. Place CV at assets/cv/JMH_CV.pdf and assets/cv/JMH_CV.tex

# 4. Add ADS API token as a GitHub secret (ADS_API_TOKEN)
#    Get from: https://ui.adsabs.harvard.edu → Account → API Token

# 5. Enable GitHub Pages (Settings → Pages → Deploy from a branch → main, root)

# 6. Trigger the first data update (Actions → Daily Data Update → Run workflow)
```

## Architecture

```
├── index.html                    # Landing page (hero slideshow + scroll sections)
├── biography/index.html          # Research, education, and background
├── publications/index.html       # Auto-populated from SciX via JSON
├── blog/index.html               # Blog listing
│   └── <post-slug>/index.html    # Individual posts
├── presentations/index.html      # Talks, colloquia, and public lectures
├── art/index.html                # Art gallery listing
│   └── <gallery>/index.html      # Individual galleries
│
├── css/
│   ├── main.css                  # Core styles, variables, dark/light themes
│   ├── landing.css               # Hero slideshow, scroll sections
│   ├── pages.css                 # Biography, publications, blog, art, presentations
│   └── responsive.css            # Mobile and tablet breakpoints
│
├── js/
│   ├── main.js                   # Theme toggle, navigation, scroll reveal
│   ├── stars.js                  # Animated star field canvas
│   ├── landing.js                # Hero slideshow, scroll sections, JWST image loader
│   └── publications.js           # Load, filter, and search publications from JSON
│
├── data/
│   ├── publications.json         # Auto-generated daily by GitHub Actions
│   └── jwst_image.json           # Auto-generated daily by GitHub Actions
│
├── assets/
│   ├── images/                   # Headshot and hero slideshow images
│   ├── cv/                       # JMH_CV.pdf and JMH_CV.tex
│   └── papers/                   # Auto-populated: arXiv PDFs and extracted figures
│
├── scripts/
│   ├── fetch_publications.py     # Fetches publication data from the SciX/ADS API
│   ├── update_cv_tex.py          # Syncs publications.json → JMH_CV.tex
│   ├── extract_figures.py        # Downloads arXiv PDFs and extracts figures
│   ├── fetch_jwst_image.py       # Fetches the latest JWST featured image from NASA
│   └── migrate_content.py        # One-time migration of blog and art from old site
│
└── .github/workflows/
    └── update_data.yml           # Runs daily at 06:00 UTC
```

## Design

I designed the site around a deep space dark theme (`#08090c` base) with a jade green (`#00a878`) accent color. Typography follows LaTeX conventions: Playfair Display for headings and Libre Franklin for body text, with fully justified alignment and no word hyphenation. An animated star field with twinkling stars and faint galaxy smudges runs on every page as a background canvas. Dark and light modes are both supported, with the user's preference persisted in `localStorage`. The layout is fully responsive, with hamburger navigation on mobile. All NASA/JWST images include credited attribution with a clickable source link.

## Auto-Updating Pipeline

A GitHub Actions workflow (`.github/workflows/update_data.yml`) runs daily at 06:00 UTC and on manual dispatch. The pipeline executes four scripts in order.

**`fetch_publications.py`** queries the SciX/ADS API for my public library (`LIBRARY_ID = "57nm1ouuTMusp62fvjiXYg"`) and writes `data/publications.json`. Fields include bibcodes, authors, journal, DOI, arXiv ID, citation count, abstract, and refereed status.

**`update_cv_tex.py`** syncs `data/publications.json` into `assets/cv/JMH_CV.tex`. New entries are inserted at the top of their respective section, and arXiv-only citations are updated to their published journal references once a DOI and volume become available. The script recomputes CV summary statistics (total papers, first-author papers, refereed papers, h-index, total citations) on every run. Entries are categorized by author position: First-Author (position 1), Second-Author (position 2), Co-Major (positions 3–10), and Co-Minor (position 11+). The script is idempotent, detecting existing entries by bibcode and arXiv ID and skipping duplicates.

**`extract_figures.py`** downloads arXiv PDFs for my first-author papers and extracts the first figure from each, storing them at `assets/papers/<arxiv_id>/figures/fig1.png` for display on the publications page.

**`fetch_jwst_image.py`** fetches the latest JWST featured image from NASA and writes `data/jwst_image.json` for display on the landing page.

All changes are committed and pushed automatically with the message `chore: daily data update [YYYY-MM-DD]`.

## Presentations

The presentations page lists my colloquia, public lectures, and conference talks. Each entry can link to Google Slides and/or a PDF download. To add a new presentation, edit `presentations/index.html` using the template in the HTML comments.

## License

© 2026 Jakob M. Helton. Content licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0).
