#!/usr/bin/env python3
"""
update_cv_tex.py — Syncs data/publications.json → assets/cv/JMH_CV.tex

Adds new publications, updates arXiv citations to published journal references,
and refreshes the total count, citation count, h-index, and date.

Run after fetch_publications.py. New entries may need manual review in Overleaf
for math formatting in titles (redshifts, Greek letters).
"""
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path

PUBLICATIONS_JSON = Path("data/publications.json")
CV_TEX = Path("assets/cv/JMH_CV.tex")

HELTON_LAST = "Helton"
SCIX_BASE = "https://www.scixplorer.org/abs"

# Author position thresholds
# pos 1 → First-Author, pos 2 → Second-Author,
# pos 3–MAJOR_THRESHOLD → Co-Major, pos > MAJOR_THRESHOLD → Co-Minor
MAJOR_THRESHOLD = 10

# Bibcodes manually kept in Co-Major despite position > MAJOR_THRESHOLD
MAJOR_OVERRIDE_BIBCODES = {
    "2026arXiv260115960W",  # Wu et al. galaxy overdensities — Helton's primary research area
}

SECTION_NAMES = {
    "first":    "First-Author",
    "second":   "Second-Author",
    "co_major": "Co-Author with Major Contributions",
    "co_minor": "Co-Author with Minor Contributions",
}

# Unicode accented characters → LaTeX commands (for author names)
UNICODE_TO_LATEX = {
    'Ä': '\\"{A}', 'ä': '\\"{a}',
    'Ë': '\\"{E}', 'ë': '\\"{e}',
    'Ï': '\\"{I}', 'ï': '\\"{i}',
    'Ö': '\\"{O}', 'ö': '\\"{o}',
    'Ü': '\\"{U}', 'ü': '\\"{u}',
    'Ÿ': '\\"{Y}', 'ÿ': '\\"{y}',
    'À': '\\`{A}', 'à': '\\`{a}',
    'È': '\\`{E}', 'è': '\\`{e}',
    'Ì': '\\`{I}', 'ì': '\\`{i}',
    'Ò': '\\`{O}', 'ò': '\\`{o}',
    'Ù': '\\`{U}', 'ù': '\\`{u}',
    'Á': "\\'{A}", 'á': "\\'{a}",
    'É': "\\'{E}", 'é': "\\'{e}",
    'Í': "\\'{I}", 'í': "\\'{i}",
    'Ó': "\\'{O}", 'ó': "\\'{o}",
    'Ú': "\\'{U}", 'ú': "\\'{u}",
    'Ý': "\\'{Y}", 'ý': "\\'{y}",
    'Â': '\\^{A}',  'â': '\\^{a}',
    'Ê': '\\^{E}',  'ê': '\\^{e}',
    'Î': '\\^{I}',  'î': '\\^{i}',
    'Ô': '\\^{O}',  'ô': '\\^{o}',
    'Û': '\\^{U}',  'û': '\\^{u}',
    'Ã': '\\~{A}',  'ã': '\\~{a}',
    'Ñ': '\\~{N}',  'ñ': '\\~{n}',
    'Õ': '\\~{O}',  'õ': '\\~{o}',
    'Ç': '\\c{C}',  'ç': '\\c{c}',
    'Å': '{\\AA}',  'å': '{\\aa}',
    'Ø': '{\\O}',   'ø': '{\\o}',
    'Æ': '{\\AE}',  'æ': '{\\ae}',
    'Œ': '{\\OE}',  'œ': '{\\oe}',
    'ß': '{\\ss}',
    'Ł': '{\\L}', 'ł': '{\\l}',   # Ł ł
    'Š': '\\v{S}', 'š': '\\v{s}', # Š š
    'Ž': '\\v{Z}', 'ž': '\\v{z}', # Ž ž
    'Č': '\\v{C}', 'č': '\\v{c}', # Č č
    'Ř': '\\v{R}', 'ř': '\\v{r}', # Ř ř
    'Ć': "\\'{C}", 'ć': "\\'{c}", # Ć ć
}

# Greek/math symbols appearing in titles → LaTeX math commands
GREEK_TO_LATEX = {
    'α': r'\alpha',   'β': r'\beta',   'γ': r'\gamma',   'Γ': r'\Gamma',
    'δ': r'\delta',   'Δ': r'\Delta',  'ε': r'\epsilon', 'ζ': r'\zeta',
    'η': r'\eta',     'θ': r'\theta',  'Θ': r'\Theta',   'ι': r'\iota',
    'κ': r'\kappa',   'λ': r'\lambda', 'Λ': r'\Lambda',  'μ': r'\mu',
    'ν': r'\nu',      'ξ': r'\xi',     'π': r'\pi',      'ρ': r'\rho',
    'σ': r'\sigma',   'Σ': r'\Sigma',  'τ': r'\tau',     'υ': r'\upsilon',
    'φ': r'\phi',     'Φ': r'\Phi',    'χ': r'\chi',     'ψ': r'\psi',
    'ω': r'\omega',   'Ω': r'\Omega',
    '≈': r'\approx',  '≲': r'\lesssim', '≳': r'\gtrsim',
    '≤': r'\leq',     '≥': r'\geq',    '∼': r'\sim',
}


# ---------------------------------------------------------------------------
# Author formatting
# ---------------------------------------------------------------------------

def unicode_to_latex(s: str) -> str:
    for char, cmd in UNICODE_TO_LATEX.items():
        s = s.replace(char, cmd)
    return s


def format_initials(parts: list) -> str:
    """['Jakob', 'M.'] → 'J.\\,M.'  |  ['Alex', 'J.'] → 'A.\\,J.'"""
    inits = []
    for p in parts:
        p = p.strip('.')
        if p:
            inits.append(f'{p[0].upper()}.')
    return r'\,'.join(inits) if len(inits) > 1 else (inits[0] if inits else '')


def format_author(author_str: str, bold: bool = False) -> str:
    """'Last, First M.' → 'F.\\,M.~Last', optionally wrapped in \\textbf{}."""
    if ',' not in author_str:
        return unicode_to_latex(author_str)
    last, _, first_part = author_str.partition(',')
    last = unicode_to_latex(last.strip())
    parts = first_part.strip().split()
    initials = format_initials(parts)
    result = f'{initials}~{last}'
    return f'\\textbf{{{result}}}' if bold else result


def get_helton_position(authors: list) -> int:
    """1-indexed position of Helton in the author list; 0 if absent."""
    for i, a in enumerate(authors):
        if HELTON_LAST in a:
            return i + 1
    return 0


def determine_category(helton_pos: int, bibcode: str = '') -> str:
    if helton_pos == 0:
        return 'co_minor'
    if helton_pos == 1:
        return 'first'
    if helton_pos == 2:
        return 'second'
    if bibcode in MAJOR_OVERRIDE_BIBCODES:
        return 'co_major'
    return 'co_major' if helton_pos <= MAJOR_THRESHOLD else 'co_minor'


def format_author_list(authors: list, helton_pos: int) -> str:
    """
    Positions 1–3: list first 3 authors (Helton bolded), then et~al.
    Positions 4+:  list first 2 authors, et~al., including Helton.
    """
    helton_tex = r'\textbf{J.\,M.~Helton}'

    if helton_pos <= 3:
        num = min(3, len(authors))
        explicit = [format_author(a, bold=(HELTON_LAST in a)) for a in authors[:num]]
        s = ', '.join(explicit)
        if len(authors) > num:
            s += ', et~al.'
        return s
    else:
        first_two = [format_author(authors[0]), format_author(authors[1])]
        return f'{", ".join(first_two)}, et~al., including {helton_tex}'


# ---------------------------------------------------------------------------
# Citation / journal formatting
# ---------------------------------------------------------------------------

def get_journal_abbrev(bibcode: str) -> str:
    checks = [
        ('ApJS', 'ApJS'), ('ApJL', 'ApJ'), ('ApJ.', 'ApJ'),
        ('MNRAS', 'MNRAS'), ('NatAs', 'Nature Astronomy'),
        ('Natur', 'Nature'), ('A&A.', 'A\\&A'), ('JCAP', 'JCAP'),
        ('PNAS', 'PNAS'), ('OJAp', 'OJAp'), ('AJ..', 'AJ'),
    ]
    for code, abbrev in checks:
        if code in bibcode:
            return abbrev
    return ''


def format_citation_link(pub: dict) -> tuple:
    """Return (href_url, citation_display_text)."""
    bibcode = pub['bibcode']
    url = f'{SCIX_BASE}/{bibcode}/abstract'

    if 'arXiv' in bibcode:
        arxiv_id = pub.get('arxiv_id', '')
        return url, f'arXiv:{arxiv_id}'

    journal = get_journal_abbrev(bibcode)
    volume = pub.get('volume', '')
    pages = pub.get('page', [])
    page = pages[0] if isinstance(pages, list) and pages else (pages or '')

    # Temporary/in-press bibcodes (e.g. MNRAS.tmp) have no final volume/page yet
    if '.tmp.' in bibcode or not volume or volume == 'tmp':
        return url, f'{journal}, in press' if journal else (url, 'in press')

    if journal and volume and page:
        return url, f'{journal}, {volume}, {page}'
    elif journal and volume:
        return url, f'{journal}, {volume}'
    return url, bibcode


# ---------------------------------------------------------------------------
# Title sanitization
# ---------------------------------------------------------------------------

def sanitize_title(title: str) -> str:
    """Basic cleanup: HTML entities, Unicode Greek → LaTeX math, accented chars."""
    # HTML entities
    for html, tex in [('&amp;', '\\&'), ('&lt;', '<'), ('&gt;', '>'),
                       ('&ndash;', '--'), ('&mdash;', '---'), ('&alpha;', 'α')]:
        title = title.replace(html, tex)

    # Bare <, >, = must be in math mode in LaTeX; \mathit keeps italic style inside \textit{} titles
    for char, cmd in [('<', '<'), ('>', '>'), ('=', '=')]:
        title = title.replace(char, f'$\\mathit{{{cmd}}}$')

    # Greek/math Unicode → $\mathit{cmd}$
    for char, cmd in GREEK_TO_LATEX.items():
        if char in title:
            title = title.replace(char, f'$\\mathit{{{cmd}}}$')

    # Accented characters in titles
    title = unicode_to_latex(title)

    return title


# ---------------------------------------------------------------------------
# TeX entry formatting
# ---------------------------------------------------------------------------

def format_item(pub: dict) -> str:
    """Return the full '    \\item ...' string for an etaremune entry."""
    authors = pub.get('authors', [])
    helton_pos = get_helton_position(authors)
    author_list = format_author_list(authors, helton_pos)
    title = sanitize_title(pub.get('title', 'Untitled'))
    year = pub.get('year', '')
    url, citation_text = format_citation_link(pub)
    return (
        f'    \\item {author_list}, '
        f'\\textit{{{title}}}, '
        f'{year}, '
        f'\\href{{{url}}}{{\\ul{{{citation_text}}}}}'
    )


# ---------------------------------------------------------------------------
# TeX parsing helpers
# ---------------------------------------------------------------------------

def extract_bibcodes_from_tex(tex: str) -> set:
    return set(re.findall(r'/abs/([^/]+)/abstract', tex))


def extract_arxiv_ids_from_tex(tex: str) -> set:
    return set(re.findall(r'\\ul\{arXiv:(\d{4}\.\d{4,5})\}', tex))


# ---------------------------------------------------------------------------
# TeX mutation helpers
# ---------------------------------------------------------------------------

def insert_entry_at_section_top(tex: str, section_name: str, entry: str) -> str:
    """Insert entry immediately after \\begin{etaremune} in the named section."""
    marker = f'\\begin{{rSubsection}}{{{section_name}}}'
    sec_start = tex.find(marker)
    if sec_start == -1:
        raise ValueError(f"Section '{section_name}' not found")

    era_start = tex.find(r'\begin{etaremune}', sec_start)
    if era_start == -1:
        raise ValueError(f"No \\begin{{etaremune}} in section '{section_name}'")

    line_end = tex.find('\n', era_start)
    return tex[:line_end + 1] + '\n' + entry + '\n' + tex[line_end + 1:]


def update_published_citation(tex: str, pub: dict) -> str:
    """
    Replace `, YEAR, \\href{...}{\\ul{arXiv:ID}}` with the published citation.
    Updates both the year and the citation link in one pass.
    """
    arxiv_id = pub.get('arxiv_id', '')
    if not arxiv_id:
        return tex

    url, citation_text = format_citation_link(pub)
    new_year = pub.get('year', '')

    pattern = re.compile(
        r', (\d{4}), '
        r'\\href\{[^}]+\}\{\\ul\{arXiv:' + re.escape(arxiv_id) + r'\}\}'
    )
    replacement = f', {new_year}, \\href{{{url}}}{{\\ul{{{citation_text}}}}}'

    updated, count = pattern.subn(lambda m: replacement, tex)
    if count:
        print(f'  Updated arXiv:{arxiv_id} → {citation_text} ({new_year})')
    return updated


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def compute_hindex(pubs: list) -> int:
    counts = sorted((p.get('citation_count', 0) for p in pubs), reverse=True)
    h = 0
    for i, c in enumerate(counts):
        if c >= i + 1:
            h = i + 1
        else:
            break
    return h


def update_stats_line(tex: str, keyword: str, total: int, cites: int, h: int) -> str:
    """Update number/citations/h-index on the Summary line matching keyword."""
    pattern = re.compile(
        r'(\\textbf\{Summary of ' + re.escape(keyword) + r'\}'
        r'[^\n]*?number: \$)\d+(\$; citations: \$)\d+(\$; h-index: \$)\d+(\$)'
    )
    def repl(m):
        return m.group(1) + str(total) + m.group(2) + str(cites) + m.group(3) + str(h) + m.group(4)
    return pattern.sub(repl, tex)


def update_metadata(tex: str, pubs: list) -> str:
    today = datetime.now(timezone.utc)
    date_str = f'{today.day} {today.strftime("%B")} {today.year}'

    # Last Updated date (both occurrences)
    tex = re.sub(r'Last Updated: [^}\\]+', f'Last Updated: {date_str}', tex)

    # All-publications stats
    total = len(pubs)
    total_cites = sum(p.get('citation_count', 0) for p in pubs)
    h_idx = compute_hindex(pubs)
    tex = update_stats_line(tex, 'All Publications', total, total_cites, h_idx)

    # Refereed stats — only if property field is present in the JSON
    if any('property' in p for p in pubs):
        refereed = [p for p in pubs if 'REFEREED' in p.get('property', [])]
        ref_cites = sum(p.get('citation_count', 0) for p in refereed)
        ref_h = compute_hindex(refereed)
        tex = update_stats_line(tex, 'Refereed Publications', len(refereed), ref_cites, ref_h)
    else:
        print('  NOTE: property field missing from JSON; refereed stats not updated.')
        print('        Add "property" to fetch_publications.py fmt() to enable this.')

    return tex


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not PUBLICATIONS_JSON.exists():
        print(f'ERROR: {PUBLICATIONS_JSON} not found. Run fetch_publications.py first.')
        sys.exit(1)
    if not CV_TEX.exists():
        print(f'ERROR: {CV_TEX} not found.')
        sys.exit(1)

    with open(PUBLICATIONS_JSON) as f:
        data = json.load(f)

    pubs = data.get('publications', [])
    print(f'Loaded {len(pubs)} publications from JSON')

    tex = CV_TEX.read_text(encoding='utf-8')

    tex_bibcodes = extract_bibcodes_from_tex(tex)
    tex_arxiv_ids = extract_arxiv_ids_from_tex(tex)

    new_entries: dict[str, list] = {k: [] for k in SECTION_NAMES}
    updated_count = 0
    skipped_count = 0

    for pub in pubs:
        bibcode = pub.get('bibcode', '')
        arxiv_id = pub.get('arxiv_id', '')

        # Already in TeX with its current bibcode
        if bibcode in tex_bibcodes:
            skipped_count += 1
            continue

        # arXiv ID already in TeX
        if arxiv_id and arxiv_id in tex_arxiv_ids:
            if 'arXiv' not in bibcode:
                # Now published — update the citation
                tex = update_published_citation(tex, pub)
                updated_count += 1
            else:
                skipped_count += 1
            continue

        # Genuinely new publication
        helton_pos = get_helton_position(pub.get('authors', []))
        if helton_pos == 0:
            print(f'  WARNING: Helton not in author list for {bibcode}; skipping')
            continue

        cat = determine_category(helton_pos, bibcode)
        entry = format_item(pub)
        pubdate = pub.get('pubdate', '0000-00')
        new_entries[cat].append((pubdate, entry, bibcode))

    # Insert new entries: sort newest-first per section, then insert
    # oldest-first so that the final order in the TeX is newest-at-top.
    total_new = sum(len(v) for v in new_entries.values())
    for cat, entries in new_entries.items():
        if not entries:
            continue
        entries.sort(key=lambda x: x[0], reverse=True)  # newest first
        section_name = SECTION_NAMES[cat]
        for _, entry, bibcode in reversed(entries):       # insert oldest first
            tex = insert_entry_at_section_top(tex, section_name, entry)
            print(f'  Added [{cat}]: {bibcode}')

    # Update date and publication statistics
    tex = update_metadata(tex, pubs)

    CV_TEX.write_text(tex, encoding='utf-8')

    print(
        f'\nDone: {total_new} new entries added, '
        f'{updated_count} arXiv→published updated, '
        f'{skipped_count} unchanged.'
    )
    if total_new > 0:
        print('NOTE: Review math formatting (redshifts, Greek) in new entries in Overleaf.')


if __name__ == '__main__':
    main()
