(function () {
  'use strict';
  const YOUR_NAME = 'Helton';
  const MONTH_ABBR = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  function fmtMonth(pubdate) {
    if (!pubdate) return '';
    const m = parseInt((pubdate.split('-')[1] || '0'), 10);
    return (m >= 1 && m <= 12) ? MONTH_ABBR[m - 1] : '';
  }
  let allPubs = [], currentFilter = 'all', searchQuery = '';
  const bibtexCache = new Map();

  async function loadPublications() {
    const c = document.getElementById('publications-list');
    const cnt = document.getElementById('pub-count');
    const statsEl = document.getElementById('pub-stats');
    if (!c) return;
    try {
      const r = await fetch('../data/publications.json');
      if (!r.ok) throw new Error('Failed');
      const d = await r.json();
      allPubs = d.publications || [];
      if (statsEl) renderStats(statsEl, allPubs);
      render(c, cnt);
    } catch (e) {
      console.error(e);
      c.innerHTML = '<div class="card" style="text-align:center;padding:3rem;"><p class="text-secondary">Publications are loading from SciX. Check back soon.</p><p class="mt-md"><a href="https://www.scixplorer.org/public-libraries/57nm1ouuTMusp62fvjiXYg" target="_blank" rel="noopener" class="btn btn--outline btn--small">View on SciX</a></p></div>';
    }
  }

  function isFA(p) {
    if (p.first_author) return p.first_author.toLowerCase().includes(YOUR_NAME.toLowerCase());
    if (p.authors && p.authors.length > 0) return p.authors[0].toLowerCase().includes(YOUR_NAME.toLowerCase());
    return false;
  }

  function calcHIndex(pubs) {
    const sorted = pubs.map(p => p.citation_count || 0).sort((a, b) => b - a);
    let h = 0;
    for (let i = 0; i < sorted.length; i++) {
      if (sorted[i] >= i + 1) h = i + 1; else break;
    }
    return h;
  }

  function fmtNum(n) {
    return n.toLocaleString();
  }

  function renderStats(el, pubs) {
    const allCites = pubs.reduce((s, p) => s + (p.citation_count || 0), 0);
    const allH = calcHIndex(pubs);
    const published = pubs.filter(p => {
      const j = p.journal || '';
      return j && !j.toLowerCase().includes('arxiv');
    });
    const pubCites = published.reduce((s, p) => s + (p.citation_count || 0), 0);
    const pubH = calcHIndex(published);
    el.innerHTML =
      `<p class="pub-stat-row"><strong>Summary Statistics for All Papers:</strong> ${fmtNum(pubs.length)} papers; ${fmtNum(allCites)} citations; h&#8209;index:&nbsp;${allH}</p>` +
      `<p class="pub-stat-row"><strong>Summary Statistics for Published Papers:</strong> ${fmtNum(published.length)} papers; ${fmtNum(pubCites)} citations; h&#8209;index:&nbsp;${pubH}</p>`;
  }

  function fmtRef(p) {
    const journal = p.journal || '';
    if (!journal || journal.toLowerCase().includes('arxiv')) {
      return p.arxiv_id ? `eprint arXiv:${p.arxiv_id}` : '';
    }
    let ref = journal;
    if (p.volume) ref += `, Volume ${p.volume}`;
    const page = Array.isArray(p.page) ? p.page[0] : (p.page || '');
    if (page && !page.toLowerCase().includes('arxiv')) ref += `, p. ${page}`;
    return ref;
  }

  function filter() {
    let f = [...allPubs];
    if (currentFilter === 'first-author') f = f.filter(p => isFA(p));
    else if (currentFilter === 'co-author') f = f.filter(p => !isFA(p));
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      f = f.filter(p =>
        (p.title || '').toLowerCase().includes(q) ||
        (p.authors || []).join(' ').toLowerCase().includes(q) ||
        String(p.year || '').includes(q) ||
        (p.journal || '').toLowerCase().includes(q));
    }
    return f;
  }

  function normalizeAuthor(name) {
    if (!name) return '';
    const comma = name.indexOf(',');
    if (comma === -1) return name;
    const last = name.substring(0, comma).trim();
    const first = name.substring(comma + 1).trim();
    return first ? `${first} ${last}` : last;
  }

  function fmtAuth(a, h, full) {
    if (!a || !a.length) return '';
    const mx = full ? Infinity : 8;
    const arr = full ? a : a.slice(0, mx);
    const fm = arr.map(x => {
      const normalized = normalizeAuthor(x);
      return normalized.toLowerCase().includes(h.toLowerCase())
        ? `<span class="highlight-author">${normalized}</span>` : normalized;
    });
    if (!full && a.length > mx) fm.push(`<em>et al.</em> (${a.length} authors)`);
    return fm.join(', ');
  }

  function escapeAttr(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function primaryClass(keywords) {
    const kw = (keywords || []).map(k => k.toLowerCase());
    if (kw.some(k => k.includes('galaxies'))) return 'astro-ph.GA';
    if (kw.some(k => k.includes('cosmology'))) return 'astro-ph.CO';
    if (kw.some(k => k.includes('stellar') || k.includes('solar'))) return 'astro-ph.SR';
    if (kw.some(k => k.includes('high energy'))) return 'astro-ph.HE';
    return 'astro-ph.GA';
  }

  function buildBibtex(p) {
    const cacheKey = p.bibcode || p.title || '';
    if (bibtexCache.has(cacheKey)) return bibtexCache.get(cacheKey);

    const isArxiv = !p.journal || p.journal.toLowerCase().includes('arxiv');
    const type = isArxiv ? 'misc' : 'article';
    const key = p.bibcode || ((p.first_author || '').split(',')[0].trim() + (p.year || ''));
    const authStr = (p.authors || []).join(' and ');
    const fields = [];
    fields.push(`  author = {${authStr}}`);
    fields.push(`  title = {{${p.title || ''}}}`);
    if (!isArxiv && p.journal) fields.push(`  journal = {${p.journal}}`);
    fields.push(`  year = {${p.year || ''}}`);
    if (!isArxiv && p.volume) fields.push(`  volume = {${p.volume}}`);
    const pg = Array.isArray(p.page) ? p.page[0] : (p.page || '');
    if (!isArxiv && pg && !pg.toLowerCase().includes('arxiv')) fields.push(`  pages = {${pg}}`);
    if (p.doi) fields.push(`  doi = {${p.doi}}`);
    if (p.arxiv_id) {
      fields.push(`  archivePrefix = {arXiv}`);
      fields.push(`  eprint = {${p.arxiv_id}}`);
      fields.push(`  primaryClass = {${primaryClass(p.keywords)}}`);
    }
    const result = `@${type}{${key},\n${fields.join(',\n')}\n}`;
    bibtexCache.set(cacheKey, result);
    return result;
  }

  function buildLinks(p) {
    const ax = p.arxiv_id || '';
    const doi = p.doi || '';
    const bib = p.bibcode || '';
    const cacheKey = escapeAttr(p.bibcode || p.title || '');
    buildBibtex(p); // ensure cached
    const parts = [
      doi ? `<a href="https://doi.org/${doi}" target="_blank" rel="noopener" class="pub-link" onclick="event.stopPropagation()">DOI</a>` : '',
      ax ? `<a href="https://arxiv.org/abs/${ax}" target="_blank" rel="noopener" class="pub-link" onclick="event.stopPropagation()">arXiv</a>` : '',
      bib ? `<a href="https://www.scixplorer.org/abs/${encodeURIComponent(bib)}/abstract" target="_blank" rel="noopener" class="pub-link" onclick="event.stopPropagation()">ADS/SciX</a>` : '',
      ax ? `<a href="https://arxiv.org/pdf/${ax}" target="_blank" rel="noopener" class="pub-link" onclick="event.stopPropagation()">Download PDF</a>` : '',
      `<button class="pub-link pub-abstract-btn" aria-expanded="false">Abstract &#9662;</button>`,
      `<button class="pub-link pub-cite-btn" data-key="${cacheKey}">Cite</button>`,
    ];
    return parts.filter(Boolean).join(' ');
  }

  function render(c, cnt) {
    const f = filter();
    if (cnt) cnt.textContent = `${f.length} publication${f.length !== 1 ? 's' : ''}`;
    if (!f.length) {
      c.innerHTML = '<div class="card" style="text-align:center;padding:2rem;"><p class="text-secondary">No publications match your search.</p></div>';
      return;
    }
    c.innerHTML = f.map((p, idx) => {
      const fa = isFA(p);
      const id = `pub-${idx}`;
      const shortAuth = fmtAuth(p.authors || [], YOUR_NAME, false);
      const fullAuth = fmtAuth(p.authors || [], YOUR_NAME, true);
      const fig = fa ? '' : (p.figure_url || '');
      const ref = fmtRef(p);
      const abstract = p.abstract || '';
      const links = buildLinks(p);

      const figHtml = fig
        ? `<div class="pub-figure"><img src="${fig}" alt="Figure" loading="lazy"></div>`
        : '';
      const refHtml = ref ? `<p class="pub-ref">${ref}</p>` : '';
      const month = fmtMonth(p.pubdate);
      const yr = (month ? month + ' ' : '') + (p.year || '');
      const citeTxt = p.citation_count === 1 ? '1&#x202F;citation' : `${p.citation_count}&#x202F;citations`;

      return `<div class="${fa ? 'pub-first-author' : ''} reveal" id="${id}">
        <div class="pub-card" tabindex="0">
          <div class="pub-card-inner">
            ${figHtml}
            <div class="pub-details">
              <div class="pub-year">${yr}${fa ? ' · First Author' : ''}${p.citation_count ? ` &middot; <span class="pub-cites">${citeTxt}</span>` : ''}</div>
              <h3 class="pub-title">${p.title || 'Untitled'}</h3>
              <p class="pub-authors">${shortAuth}</p>
              ${refHtml}
              <div class="pub-links">${links}</div>
            </div>
          </div>
          <div class="pub-abstract-panel" style="display:none;">
            <p class="pub-abstract-authors">${fullAuth}</p>
            ${abstract ? `<p class="pub-abstract-text">${abstract}</p>` : ''}
          </div>
        </div>
      </div>`;
    }).join('');

    // Event delegation for all interactive elements
    c.onclick = function (e) {
      // BibTeX copy button
      if (e.target.classList.contains('pub-cite-btn')) {
        e.stopPropagation();
        const key = e.target.dataset.key;
        const bibText = bibtexCache.get(key) || '';
        navigator.clipboard.writeText(bibText).then(() => {
          e.target.textContent = 'Copied!';
          setTimeout(() => { e.target.textContent = 'Cite'; }, 2000);
        }).catch(() => {
          e.target.textContent = 'Failed';
          setTimeout(() => { e.target.textContent = 'Cite'; }, 2000);
        });
        return;
      }
      // Abstract toggle button
      if (e.target.classList.contains('pub-abstract-btn')) {
        const card = e.target.closest('.pub-card');
        if (!card) return;
        const panel = card.querySelector('.pub-abstract-panel');
        if (!panel) return;
        const isOpen = panel.style.display !== 'none';
        panel.style.display = isOpen ? 'none' : 'block';
        card.classList.toggle('pub-card--expanded', !isOpen);
        e.target.innerHTML = isOpen ? 'Abstract &#9662;' : 'Abstract &#9652;';
        e.target.setAttribute('aria-expanded', String(!isOpen));
        return;
      }
      // Card-click toggle (skip links)
      if (e.target.closest('a')) return;
      const card = e.target.closest('.pub-card');
      if (!card) return;
      const panel = card.querySelector('.pub-abstract-panel');
      if (!panel) return;
      const abstractBtn = card.querySelector('.pub-abstract-btn');
      const isOpen = panel.style.display !== 'none';
      panel.style.display = isOpen ? 'none' : 'block';
      card.classList.toggle('pub-card--expanded', !isOpen);
      if (abstractBtn) {
        abstractBtn.innerHTML = isOpen ? 'Abstract &#9662;' : 'Abstract &#9652;';
        abstractBtn.setAttribute('aria-expanded', String(!isOpen));
      }
    };

    c.onkeydown = function(e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const card = e.target.closest('.pub-card');
      if (!card || e.target.matches('button, a')) return;
      e.preventDefault();
      const panel = card.querySelector('.pub-abstract-panel');
      const abstractBtn = card.querySelector('.pub-abstract-btn');
      if (!panel) return;
      const isOpen = panel.style.display !== 'none';
      panel.style.display = isOpen ? 'none' : 'block';
      card.classList.toggle('pub-card--expanded', !isOpen);
      if (abstractBtn) {
        abstractBtn.innerHTML = isOpen ? 'Abstract &#9662;' : 'Abstract &#9652;';
        abstractBtn.setAttribute('aria-expanded', String(!isOpen));
      }
    };

    initReveal();
    if (typeof renderMathInElement === 'function') {
      renderMathInElement(c, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true },
        ],
        throwOnError: false,
      });
    }
  }

  function initReveal() {
    const obs = new IntersectionObserver(es => {
      es.forEach(e => {
        if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
      });
    }, { threshold: 0.05 });
    document.querySelectorAll('#publications-list .reveal').forEach(el => obs.observe(el));
  }

  document.addEventListener('DOMContentLoaded', () => {
    const c = document.getElementById('publications-list');
    const cnt = document.getElementById('pub-count');
    const si = document.getElementById('pub-search');
    const fb = document.querySelectorAll('.pub-filter-btn');
    if (!c) return;
    fb.forEach(b => b.addEventListener('click', () => {
      fb.forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      currentFilter = b.dataset.filter;
      render(c, cnt);
    }));
    if (si) {
      let db;
      si.addEventListener('input', () => {
        clearTimeout(db);
        db = setTimeout(() => { searchQuery = si.value; render(c, cnt); }, 250);
      });
    }
    loadPublications();
  });
})();
