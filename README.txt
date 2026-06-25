AUTOMATED SITEMAP / DOCUMENT-ARCHIVE GENERATOR
================================================

WHAT IT DOES
  generate.py reads index.html (your single source of truth), finds every
  PDF link, and regenerates sitemap.xml and documents.html to match exactly.
  No separate list to maintain -- it all comes from index.html.

ONE-TIME SETUP
  1. Put generate.py in your repo root (same folder as index.html).
  2. Make sure Python is installed (you have it).
  3. Install the one dependency:
        pip install beautifulsoup4

EVERY TIME YOU ADD DOCUMENTS
  1. Add the document's link to the case card in index.html (as you do now).
  2. Drop the PDF into press_pdfs/.
  3. From the repo root, run:
        python generate.py
  4. It rewrites sitemap.xml and documents.html, and prints a report:
       - total PDFs and groups
       - ORPHANS: files in press_pdfs/ that nothing links to
       - BROKEN: links pointing to files that aren't in press_pdfs/
  5. Commit and push all changed files (index.html, sitemap.xml, documents.html).
  6. In Google Search Console, resubmit sitemap.xml to prompt a re-crawl.

NOTES
  - Case cards and their "Explore the Further Documentary Record" sections are
    automatically merged into one group (via the #doc- link on the card).
  - Documents not inside any case card (CV, op-eds, profile pieces) are grouped
    under "Profile & Career".
  - YouTube/video links are intentionally excluded from the document archive
    (it lists PDFs only); they still live on the case cards.
  - The orphan report is your cleanup aid: review orphans periodically and
    either link them (preferred, if they name you / corroborate your role) or
    delete genuine duplicates.
