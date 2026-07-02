#!/usr/bin/env python3
"""
generate.py - Regenerates sitemap.xml and documents.html from index.html.

USAGE:  python generate.py

Reads index.html (the single source of truth), finds every PDF link,
groups them by case (or Profile/Career for non-case documents), and writes
fresh sitemap.xml and documents.html. Also reports orphan files (in
press_pdfs/ but not linked) and broken links (linked but file missing).

No external dependencies beyond beautifulsoup4:  pip install beautifulsoup4
"""
import os, re, sys, html, urllib.parse, glob
from collections import OrderedDict

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: BeautifulSoup not installed. Run:  pip install beautifulsoup4")
    sys.exit(1)

SITE = "https://philliphalpern.com"
INDEX = "index.html"
PDF_DIR = "press_pdfs"
PROFILE_GROUP = "Profile & Career"

def encurl(href):
    # percent-encode each path segment, build absolute URL
    return SITE + "/" + "/".join(urllib.parse.quote(s) for s in href.split('/'))

def build_docid_map(soup):
    """Map each doc-section id to its canonical case-card name, via the
    card's 'Explore the Further Documentary Record' (#doc-*) link.
    This merges a case card and its documentary section into one group."""
    m = {}
    for card in soup.find_all('div', class_='case-card'):
        h = card.find('h3', class_='case-name')
        if not h:
            continue
        ex = card.find('a', href=lambda x: x and x.startswith('#doc-'))
        if ex:
            m[ex['href'].lstrip('#')] = (h.get_text(strip=True), card.get('id') or '')
    return m

def get_group(a, docid_map):
    """Resolve a link to its case grouping by walking up the DOM.
    A doc-section is mapped back to its parent case card when possible."""
    for anc in a.parents:
        cls = anc.get('class') or []
        aid = anc.get('id') or ''
        if 'case-card' in cls:
            h = anc.find('h3', class_='case-name')
            cid = anc.get('id') or ''
            anchor = cid.replace('case-', 'archive-', 1) if cid else ''
            return (h.get_text(strip=True) if h else "Uncategorized", anchor)
        if aid.startswith('doc-'):
            if aid in docid_map:
                name, cid = docid_map[aid]
                return (name, cid.replace('case-', 'archive-', 1) if cid else aid.replace('doc-', 'archive-', 1))
            h = anc.find('h3')
            return (h.get_text(strip=True) if h else aid, aid.replace('doc-', 'archive-', 1))
    return (PROFILE_GROUP, 'archive-profile-career')  # links not in a card/doc section

def main():
    if not os.path.exists(INDEX):
        print(f"ERROR: {INDEX} not found. Run this from the repo root."); sys.exit(1)

    soup = BeautifulSoup(open(INDEX, encoding='utf-8').read(), 'html.parser')
    docid_map = build_docid_map(soup)
    links = soup.find_all('a', href=lambda h: h and 'press_pdfs/' in h and h.endswith('.pdf'))

    # Build ordered, de-duplicated records: first occurrence wins (preserves page order)
    groups = OrderedDict()
    seen = set()
    records = []
    for a in links:
        href = a['href']
        if href in seen:
            continue
        seen.add(href)
        text = a.get_text(strip=True).lstrip('⇓▶').strip()
        group, anchor = get_group(a, docid_map)
        records.append({'href': href, 'text': text, 'group': group, 'anchor': anchor})
        groups.setdefault(group, []).append(records[-1])

    # ---- Write sitemap.xml ----
    today = __import__('datetime').date.today().isoformat()
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    # homepage
    out += ['  <url>', f'    <loc>{SITE}/</loc>', f'    <lastmod>{today}</lastmod>',
            '    <changefreq>monthly</changefreq>', '    <priority>1.0</priority>', '  </url>']
    # documents.html page itself
    out += ['  <url>', f'    <loc>{SITE}/documents.html</loc>', f'    <lastmod>{today}</lastmod>',
            '    <changefreq>monthly</changefreq>', '    <priority>0.9</priority>', '  </url>']
    for r in records:
        out += ['  <url>', f'    <loc>{html.escape(encurl(r["href"]))}</loc>',
                f'    <lastmod>{today}</lastmod>', '    <changefreq>yearly</changefreq>',
                '    <priority>0.8</priority>', '  </url>']
    out.append('</urlset>')
    open('sitemap.xml', 'w', encoding='utf-8').write('\n'.join(out) + '\n')

    # ---- Write documents.html ----
    body = []
    for group, items in groups.items():
        anchor = items[0].get('anchor') or ''
        body.append(f'<section class="doc-case" id="{anchor}">' if anchor else '<section class="doc-case">')
        body.append(f'  <h2>{html.escape(group)}</h2>')
        body.append('  <ul>')
        for r in items:
            body.append(f'    <li><a href="{html.escape(encurl(r["href"]))}">{html.escape(r["text"])}</a></li>')
        body.append('  </ul>')
        body.append('</section>')
    body = "\n".join(body)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Document Archive — Phillip L.B. Halpern, Federal Prosecutor</title>
<meta name="description" content="Complete archive of indictments, informations, sentencing and trial memoranda, appellate opinions, and contemporary press coverage from the 36-year federal prosecutorial career of Assistant U.S. Attorney Phillip L.B. Halpern, Southern District of California.">
<link rel="canonical" href="{SITE}/documents.html">
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
<style>
:root {{ --navy:#0e1a2b; --ink:#1a1a1a; --gold:#b8943f; --gold-light:#d4a843; --cream:#f5f0e8; --warm-white:#faf8f4; --mid-gray:#6b6b6b; --rule:#c8bfa8; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'EB Garamond',Georgia,serif; background:var(--warm-white); color:var(--ink); font-size:18px; line-height:1.7; }}
header {{ background:var(--navy); color:var(--cream); padding:48px 24px; text-align:center; }}
header h1 {{ font-family:'Playfair Display',Georgia,serif; font-size:34px; font-weight:700; letter-spacing:0.5px; }}
header p {{ margin-top:12px; font-size:18px; color:var(--gold-light); font-style:italic; }}
header a {{ color:var(--cream); }}
main {{ max-width:880px; margin:0 auto; padding:48px 24px 80px; }}
.intro {{ font-size:18px; color:var(--mid-gray); margin-bottom:40px; border-bottom:1px solid var(--rule); padding-bottom:28px; }}
.doc-case {{ margin-bottom:40px; }}
.doc-case h2 {{ font-family:'Playfair Display',Georgia,serif; font-size:22px; font-weight:600; color:var(--navy); border-bottom:1px solid var(--gold); padding-bottom:8px; margin-bottom:16px; }}
.doc-case ul {{ list-style:none; }}
.doc-case li {{ margin-bottom:14px; padding-left:18px; border-left:2px solid var(--rule); }}
.doc-case a {{ color:var(--gold); text-decoration:none; font-weight:500; font-size:18px; }}
.doc-case a:hover {{ text-decoration:underline; color:var(--navy); }}
footer {{ text-align:center; padding:32px; color:var(--mid-gray); font-size:14px; border-top:1px solid var(--rule); }}
footer a {{ color:var(--gold); }}
</style>
</head>
<body>
<header>
<h1>Document Archive</h1>
<p>Phillip L.B. Halpern — Assistant United States Attorney (Ret.)</p>
<p style="font-size:15px;"><a href="/">&larr; Return to philliphalpern.com</a></p>
</header>
<main>
<p class="intro">A complete, searchable archive of the primary-source documents underlying these federal prosecutions — indictments, informations, sentencing and trial memoranda, appellate opinions — together with contemporary press and broadcast coverage. All documents are full-text searchable. Southern District of California.</p>
{body}
</main>
<footer>
<p>&copy; Phillip L.B. Halpern. &nbsp;<a href="/">philliphalpern.com</a> &nbsp;&middot;&nbsp; <a href="/sitemap.xml">sitemap</a></p>
</footer>
</body>
</html>
"""
    open('documents.html', 'w', encoding='utf-8').write(page)

    # ---- Report ----
    print(f"Generated sitemap.xml and documents.html from {INDEX}")
    print(f"  {len(records)} unique PDFs across {len(groups)} groups")
    # orphan + broken-link check (only if press_pdfs/ exists locally)
    if os.path.isdir(PDF_DIR):
        on_disk = set(os.path.basename(p) for p in glob.glob(f'{PDF_DIR}/*.pdf'))
        linked = set(os.path.basename(r['href']) for r in records)
        orphans = sorted(on_disk - linked)
        broken = sorted(linked - on_disk)
        print(f"\n  Files in {PDF_DIR}/: {len(on_disk)}  |  Linked: {len(linked)}")
        if orphans:
            print(f"\n  ORPHANS ({len(orphans)}) — in folder but not linked anywhere:")
            for o in orphans: print(f"      {o}")
        if broken:
            print(f"\n  *** BROKEN ({len(broken)}) — linked but file missing: ***")
            for b in broken: print(f"      {b}")
        if not orphans and not broken:
            print("  No orphans, no broken links. Clean.")
    else:
        print(f"  (Run from repo root to also get orphan/broken-link report.)")

if __name__ == '__main__':
    main()
