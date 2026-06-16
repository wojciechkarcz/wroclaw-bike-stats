---
name: html
description: "Produce a rich HTML artifact for the user to SEE in a browser instead of reading raw text or Markdown, then publish it and return a tappable URL. Use this whenever the result of the work would be clearer as a visual page — specs, plans, code reviews, PR write-ups, reports, research summaries, explainers, dashboards, data tables, decision docs, diagrams, or a small purpose-built editor/interface — AND whenever the user wants to preview the actual app or site being built (a single-page app, or a multi-file web project with html/css/js/images/json). Trigger this even when the user does not say \"HTML\" or \"preview\" — if they ask for a report, a plan, a diagram, a summary of the work, \"show me\", \"let me see it\", or \"something I can look at on my phone\", reach for this skill. Do NOT use it for plain code edits, raw text answers, or when the user explicitly wants Markdown."
---
 
# HTML Preview
 
Build a web artifact, store it under the repo's gitignored `preview/` folder, upload
it to the user's preview host, and hand back a URL. Every call produces a fresh,
separately numbered artifact — previous ones are left untouched.
 
## Two modes
 
**Mode A — Document / interface preview (default).** A single self-contained `.html`
page that conveys or lets the user act on the work. This is the common case. Patterns
(from "the unreasonable effectiveness of HTML"):
- Specs, plans, explorations — mockups, data-flow diagrams, annotated code snippets.
- Code review / PR write-ups — rendered diffs, margin annotations, severity colors.
- Reports, research, explainers — long-form pages, interactive explainers, or decks.
- Decision docs, tables, dashboards.
- Small purpose-built editors that end in a "copy as prompt / JSON" button.
**Mode B — App preview.** Render the actual thing being built. A SPA that inlines into
one file, or a multi-file web app that needs a folder (html/css/js/images/json).
 
## Step 1 — Choose the output shape
 
Default to a SINGLE self-contained `.html`. Escalate to a FOLDER (with an `index.html`
entry point) ONLY when the artifact genuinely needs more than one file to run:
- it `fetch()`es local files at runtime (JSON, data, partials)
- it uses cross-file ES module imports (`import './x.js'`)
- it has multiple or large binary assets impractical to inline
- it has more than one HTML page, or is a framework build output (a `dist/`)
Mode A is almost always a single file. Mode B may be either.
 
## Step 2 — Build it well
 
- (skip it, for now use css built inside every html file, that feature will be developed in the future) Link the shared base stylesheet for consistency and to save tokens:
  `<link rel="stylesheet" href="/_assets/base.css">` (served from the same host).
  Add only the page-specific CSS the artifact needs on top of it. If `/_assets/base.css`
  is unavailable (e.g. the page must work offline), inline a minimal style block instead.
- Make deliberate, non-templated design choices: a clear type scale, a real layout, a
  palette that fits the subject. Avoid the generic "big number + gradient card" default.
- Diagrams: use inline SVG or Mermaid (never a flat raster) so they stay crisp and,
  later, annotatable.
- Make it mobile-responsive — the user often opens previews on a phone.
- Keep all JS self-contained; no private data (previews are public to anyone with the link).
- You can put links to external sources or embed images/videos inside previews when needed
- Write exactly ONE of these:
  - Single file → `preview/<NAME>.html`
  - Folder → `preview/<NAME>/` with an `index.html`
  (`<NAME>` is computed in Step 3.)
For structural inspiration only, the gallery at `github.com/anthropics/html-effectiveness`
shows worked examples per use case; adapt patterns, don't copy whole pages.
 
## Step 3 — Allocate a fresh name and publish
 
```sh
# keep previews out of git (run once; harmless if repeated)
grep -qxF '/preview/' .gitignore 2>/dev/null || echo '/preview/' >> .gitignore
mkdir -p preview
 
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" \
        | tr 'A-Z' 'a-z' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')
 
next_name() {                      # next free NNN for this project (public HEAD probe)
  local n=1 p
  while :; do
    p=$(printf '%s-preview-%03d' "$SLUG" "$n")
    if curl -fsI -o /dev/null "$PREVIEW_BASE_URL/p/$p.html" 2>/dev/null \
       || curl -fsI -o /dev/null "$PREVIEW_BASE_URL/p/$p/index.html" 2>/dev/null
    then n=$((n+1)); else printf '%s' "$p"; return; fi
  done
}
NAME=$(next_name)
 
# >>> build the artifact into preview/$NAME.html  OR  preview/$NAME/ here <<<
 
if [ -f "preview/$NAME.html" ]; then
  curl -fsS -T "preview/$NAME.html" -u "$PREVIEW_UPLOAD_AUTH" \
    "$PREVIEW_BASE_URL/p/$NAME.html"
  echo "Preview: $PREVIEW_BASE_URL/p/$NAME.html   (source: preview/$NAME.html)"
else
  ( cd "preview/$NAME" && find . -type f | sed 's|^\./||' | while read -r f; do
      curl -fsS -T "$f" -u "$PREVIEW_UPLOAD_AUTH" "$PREVIEW_BASE_URL/p/$NAME/$f"
    done )
  echo "Preview: $PREVIEW_BASE_URL/p/$NAME/   (source: preview/$NAME/)"
fi
```
 
## Step 4 — Hand back the URL
 
Print the final `Preview:` line on its own so it's tappable on mobile. Mention the
local `source:` path so a follow-up request can edit that exact artifact in place.
 
## Requires (set once in the cloud environment)
 
- `PREVIEW_BASE_URL` — e.g. `https://preview.example.com`
- `PREVIEW_UPLOAD_AUTH` — e.g. `uploader:<password>`
- the preview host domain added to the environment's Custom allowed domains
- optional, it will be implemented later: `/_assets/base.css` hosted on the same host for shared styling
