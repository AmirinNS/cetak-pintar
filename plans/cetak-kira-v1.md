# Plan: CetakKira v1

## Goal

A free, open-source tool that generates printable A4 math worksheets with answer keys for Malaysian primary school kids (Tahun 1 to 3), Malay first with an English toggle. Parents and teachers use it as a web app (pick options, download a PDF, share a link that regenerates the same sheet) or as a CLI. It is also a public portfolio piece.

## Hard rules

1. **Original content only.**
   - Every question and every solution is generated at runtime from a seed.
   - No photos, scans, transcribed problem sets, or copied instruction wording from any published workbook.
   - Workers may read exactly one outside file, `~/Projects/kids-exercise/generate_kids_exercise_bw.py`, and only to reuse simple drawing primitives (rounded boxes, ruled lines, grid cells, header layout).
   - They must not copy its hardcoded problem or solution data (fixed blank sets, `darab_sifir_*_problems`, solution `rows_data`), its instruction sentences, or its comments, and must not read anything else in that folder.
   - When a layout needs more than a primitive, draw it fresh.
2. **No personal paths, emails, or secrets** in committed files. PDF title and author metadata are "CetakKira".
3. **No database.** Settings live in the URL; PDFs are generated per request and never stored.
4. **House style** per `CLAUDE.md` (after A1 updates it): Flask, functional modules, thin routes, imports at top, uv for everything. UI is Bootstrap 5 (CDN) + Jinja2 + vanilla JS; use the `frontend-bootstrap-evolution` skill.
5. **Narrow curriculum wording.** Presets are described by their actual ranges ("Tahun 1 style: numbers to 100, add and subtract without regrouping") and say "inspired by Tahun 1 to 3 topics". Never claim KSSR alignment, completeness, exam readiness, or ministry endorsement.

## Scope

- In scope: the worksheet types below, answer keys, Malay and English, CLI, web form with shareable URL, tests, Docker, CI, README.
- Out of scope (v2 or the e-learning repo): interactive on-screen practice with instant feedback.
- Out of scope: accounts, saved worksheets, payments, deployment (main session, with user approval), fractions, money, time, measurement, Tahun 4 to 6, tagged/accessible PDF output, cross-release reproducibility of old links.

## Spec contract (shared by web and CLI)

One canonical spec drives everything. `parse_spec(multidict)` takes a werkzeug-style multidict (web) or the CLI's equivalent and returns `(spec, errors)`; `spec_to_query(spec)` emits the canonical, fully expanded query. Contract: `parse_spec(spec_to_query(spec)) == (spec, [])`. Arbitrary input is normalized, not preserved byte for byte.

| Param | Default | Domain | Notes |
|---|---|---|---|
| `t` (topics) | none (required) | subset of `grid, add, sub, sifir_ref, sifir, div`; 1 to 6 | Comma-separated or repeated key; unknown or empty names are errors; duplicates collapse; canonical order is the order listed here |
| `pages` | 4 | 1 to 20 | Content sheets in total, see page accounting |
| `lang` | `ms` | `ms`, `en` | UI and PDF language |
| `ans` | `1` | `0`, `1` | Append answer sheets |
| `seed` | resolved once | integer 0 to 2147483647 | Missing or blank: web redirects with a new seed, CLI picks one and prints it |
| `grid_start` | 1 | 1, 101, 201, ..., 901 | Grid shows start to start+99 |
| `grid_blanks` | 30 | 15 to 60 | |
| `add_digits` | 1 | 1, 2, 3 | Both operands have exactly this many digits |
| `add_regroup` | 0 | 0, 1 | 0: no column (including incoming carry) reaches 10. 1: at least one column carries |
| `sub_digits` | 1 | 1, 2, 3 | Top operand has exactly this many digits; bottom has 1 to this many and is not greater than top |
| `sub_borrow` | 0 | 0, 1 | 1 requires `sub_digits >= 2` (single-digit borrowing is impossible without negatives) |
| `sifir_tables` | 2,3,4,5 | subset of 1 to 12, at least 1 | Duplicates collapse, stored sorted |
| `sifir_n` | 12 | 1 to min(24, 12 x number of tables) | Questions per sifir page |
| `div_digits` | 2 | 2, 3 | Dividend digits |
| `div_divisors` | 2..9 | subset of 2 to 9, at least 1 | |
| `div_rem` | 0 | 0, 1 | 0: exact division. 1: nonzero remainder required |
| `preset` | none | `t1`, `t2`, `t3` | Expanded into explicit params first, then explicit params override. Never appears in the canonical query |

- Repeated scalar keys, non-integer or out-of-range numbers, invalid booleans or languages, and impossible combinations are field errors (message keys translated in both languages).
- Options of unselected topics are ignored and dropped from the canonical query.
- Validation happens before any generation. Generator bugs are not caught and relabeled as 400.
- Presets: `t1` = grid 1-100, add 1 digit no regroup, sub 1 digit no borrow. `t2` = grid 101-200, add 2 digits regroup, sub 2 digits borrow, sifir 2,3,4,5,10. `t3` = add 3 digits regroup, sub 3 digits borrow, sifir 6,7,8,9, div 2 digits exact.

## Page accounting

- `pages` counts content sheets in total across topics. It must be at least the number of sheets the selected topics need at minimum, else error.
- `sifir_ref` needs `ceil(len(sifir_tables) / 6)` sheets (6 tables per sheet), counted against `pages`.
- Remaining sheets go round-robin to the practice topics in canonical order, starting from the first. Each practice topic gets at least one.
- Answer sheets (when `ans=1`) follow all content sheets, one per practice sheet, in the same order. `sifir_ref` has no answer sheet. Maximum PDF length is 40 pages.
- Cards per practice sheet:
  - grid: 1 grid.
  - add and sub: 20 cards (16 when digits = 3).
  - sifir: `sifir_n`.
  - div: 12 cards (2 digits) or 8 (3 digits).
- Each sifir sheet samples without replacement from the pool of `table x factor` (factor 1 to 12) for the chosen tables. `2x3` and `3x2` count as different questions. Sheets may repeat questions across sheets.
- Worked example (pages=4, t=add,sifir_ref,sifir, sifir_tables=2,3): sifir_ref takes 1. The remaining 3 go round-robin: add, sifir, add. PDF order: add, sifir_ref, sifir, add, then answers for add, sifir, add. Exact order is a test fixture.

## Determinism promise

The same normalized spec gives a byte-identical PDF within one release built from the committed `uv.lock` on Python 3.12. Implementation:
- one `random.Random(seed)` per worksheet;
- stable iteration (no set iteration in output paths);
- ReportLab `Canvas(..., invariant=1)`.

Old links may change across releases. That is stated in the README. No generator-version parameter in v1.

## Approach

### Phase A: Instructions, scaffold cleanup, spec, and the first three generators

#### Milestone A1: Remove MongoDB everywhere
1. `pyproject.toml`: `uv remove pymongo`; `uv add reportlab Flask-Limiter`; `uv add --dev pypdf`; `[tool.ruff]` line length 100, select `E,F,W,I,B`. Keep the generated `uv.lock`.
2. `sources/config.py`: drop the Mongo client and settings. Keep `APP_ENV`, `SECRET_KEY` (reject the placeholder in production), `PORT`, `SITE_URL`, `SITE_NAME`; add `TRUSTED_PROXY_HOPS` (int, default 0) and `RATELIMIT_ENABLED` (default true).
3. `cetak_kira.py`: drop the `db` import, `modules.items` and the Mongo-backed index route; delete `modules/items.py`. `.env.example`: drop Mongo lines.
4. `CLAUDE.md` and `README.md`: rewrite every MongoDB, `db`-parameter, and co-located-database statement. State "No database; worksheet functions are pure and take no db". Keep every other house-style rule.
5. `LICENSE` MIT ("Mohamad Khairulamirin"). `.gitignore`: add `*.pdf`, `.pytest_cache/`, `.ruff_cache/`, `.orchestrate/`.
→ Verify: `uv sync`; `uv run ruff check .`; with no Mongo running and no Mongo env vars, `uv run python -c "import cetak_kira"` succeeds.

#### Milestone A2: Spec contract and page accounting
1. `modules/spec.py`: `Spec` (frozen dataclass), `parse_spec`, `spec_to_query`, `expand_preset`, `PRESETS`, implementing the tables above. Error items are `(field, message_key)`.
2. `modules/layout.py`: `plan_sheets(spec)` returns the ordered list of `(kind, topic, sheet_index)` for content and answer sheets per the page-accounting rules.
3. `tests/test_spec.py`:
   - Round trip.
   - Absent vs blank seed, seed 0 and 2147483647, huge numeric strings.
   - Unknown, empty, and duplicate topics; repeated scalar keys; invalid booleans and language; empty table or divisor lists; out-of-range values.
   - `sub_borrow=1` with `sub_digits=1` rejected; `sifir_n` above capacity rejected; `pages` below minimum rejected.
   - Preset then override; inactive options dropped.
4. `tests/test_layout.py`: the worked example's exact order, `sifir_ref` pagination for 1, 6, 7, and 12 tables, the 40-page maximum.
→ Verify: `uv run pytest -q`.

#### Milestone A3: grid, add, sub generators
1. `modules/problems.py`, each function taking `random.Random`:
   - `grid_blanks(rng, start, count)`: sorted unique cells.
   - `addition(rng, digits, regroup, n)` and `subtraction(rng, digits, borrow, n)`: build operands constructively, digit by digit from the ones column with carry or borrow propagated, so generation always terminates without retry loops. Return frozen dataclasses with operands and answer.
2. `tests/test_problems.py`:
   - Directed fixtures checked by the regroup/borrow predicates: `19+81`, `99+1`, `100-1`, `100-99`, `101-2`.
   - 200-seed loops asserting each guarantee.
   - Determinism per seed.
   - Three-digit addition may produce four digits (renderer must allow it).
→ Verify: `uv run pytest -q`.

### Phase B: Renderer and CLI for grid, add, sub (first usable release)

#### Milestone B1: Renderer primitives and three page types
1. `modules/render/primitives.py`: header (title, subtitle, Nama, Tarikh, Markah), rounded box, grid cell, footer with page number and "cetakkira". Reuse primitives from the allowed file only where they generalize.
2. `modules/render/pages.py`: `draw_grid`, `draw_add`, `draw_sub` and their answer variants. Digit columns are right-aligned and computed from the widest operand plus one overflow column for addition.
3. `modules/i18n.py`: all fixed text in `ms` and `en`, freshly written. Titles, instructions, labels, error message keys, form labels.
4. `modules/render/pdf.py`: `render(spec) -> bytes` (A4, `invariant=1`, Helvetica family, metadata title and author "CetakKira").
5. `tests/test_render.py`, using `pypdf`:
   - Page count equals `plan_sheets` length; page size is A4; metadata is set.
   - Extracted answer-page text contains the expected answers for a fixed seed.
   - Byte-identical output for the same spec in two separate processes with different `PYTHONHASHSEED`.
#### Milestone B2: CLI
1. `cli.py` (argparse): `--preset`, `--topics`, one flag per spec param, `--lang`, `--no-answers`, `--seed`, `-o`. Builds the same multidict and calls `parse_spec`. Resolves a missing seed once and prints the full canonical query.
2. `tests/test_cli.py`: output file written; bad options exit non-zero with the field message; the printed query regenerates a byte-identical PDF.
→ Verify (after B2): render each type at minimum and maximum options in both languages and open every PDF. Check digits are not clipped, four-digit sums fit, and headers fit in English and Malay. Record the time for the largest 40-page worksheet on this machine as a budget note (not a CI test).

### Phase C: Multiplication slice (sifir_ref, sifir)

1. `modules/problems.py`: `multiplication(rng, tables, n)` sampling without replacement from the stable ordered pool.
2. `modules/render/pages.py`: `draw_sifir_ref` (up to 6 tables per sheet, fresh layout), `draw_sifir`, answers for `sifir`.
3. Tests: pool size, exact capacity, capacity plus one rejected (at parse time), single table with n=12, 1 and 12 reference tables.
→ Verify: visual check at 1 table, 6 tables, 12 tables, and `sifir_n=24`, both languages.

### Phase D: Division slice

1. Long-division convention, documented in `modules/problems.py`:
   - Bring down the leading prefix until it is at least the divisor.
   - Write a zero quotient digit for every later brought-down digit that is smaller than the divisor.
   - Each step records `col` (dividend column index), `brought_down`, `partial`, `q_digit`, `product`, `difference`.
2. `division(rng, digits, divisors, remainder, n)` built constructively (pick divisor and quotient, then remainder per `div_rem`).
3. `draw_div` (cards with working space) and `draw_div_answers` (full working aligned to dividend columns), drawn fresh.
4. Tests:
   - Recurrence `partial = previous_difference * 10 + brought_down`, `product = q_digit * divisor`, and `0 <= difference < divisor`.
   - Identity `dividend = divisor * quotient + remainder`.
   - Directed fixtures `12÷9`, `100÷4`, `101÷5`, `208÷2`, `999÷9`.
   - 200-seed loops.
→ Verify: visual check of answer alignment for the directed fixtures in both languages.

### Phase D2: Picture counting slice (Tahun 1)

1. New topic `count` (Malay title from i18n, for example "Kira dan Tulis"). Spec params `count_max` (5, 10, or 20, default 10) and `count_shapes` (subset of `star, circle, apple, fish, flower`, at least 1). Added to the spec table, presets (`t1` includes it), canonical order (after `grid`), and page accounting (12 boxes per sheet).
2. `modules/problems.py`: `counting(rng, max_n, shapes, n)` returns the shape, count (1 to max), and a deterministic layout (non-overlapping grid positions inside the box).
3. `modules/render/shapes.py`: each shape drawn as simple black outline vector paths in ReportLab, written fresh, no bitmaps. Answer sheet shows the number.
4. Tests: counts within range, positions inside the box and non-overlapping, every shape renders, answers match.
→ Verify: visual check of each shape at 1 and at `count_max` in both languages; print one page in black and white.

### Phase E: Web app

1. Routes (thin):
   - `GET /`: renders the form, always with a resolved `seed` in a hidden field (new random seed when absent). A full query in the URL prefills every control. Preset links are plain `?preset=t1` links that work without JS.
   - `GET /cetak`: no seed means a 302 to the same canonical URL with a new seed; errors re-render the form at 400 with field errors and the user's values kept; success returns `application/pdf` inline, filename `cetakkira-<topics>-<seed>.pdf`.
   - `GET /health`.
2. Sharing: the "Jana PDF" submit and the "Salin pautan" button serialize the same current form values, including the hidden seed. "Soalan baharu" replaces the seed. When the clipboard API is unavailable, show the URL in a selectable read-only field. The form fully works with JS disabled.
3. Rate limiting:
   - Flask-Limiter on `/cetak`, 30 per minute per client address, memory storage, single Waitress process. The ceiling is documented: counters reset on restart and are per process.
   - Apply `ProxyFix(x_for=TRUSTED_PROXY_HOPS)` only when the setting is above 0. Never read `X-Forwarded-For` directly.
   - The redirect counts as one request. The 429 page is localized and keeps `Retry-After`.
4. Accessibility and language:
   - `<html lang>` follows `lang`.
   - Every control has a label; topic options sit in fieldsets with legends; focus is visible.
   - Presets and the language toggle are keyboard operable and preserve the spec.
   - Errors are tied to fields (`aria-describedby`) with a focused error summary, and not shown by colour alone.
   - Hidden topic groups use `disabled` so they never block submit. The new-tab download is disclosed.
5. Illustrations: a friendly CetakKira mascot and one icon per topic, generated with agy image generation. They are original images. Save the final PNG/WebP files (optimized, under 200 KB each) to `static/img/`, with alt text in i18n. Record the generation prompts in `docs/assets.md`. Used on the form page and README only, never inside PDFs.
6. Templates: `base.html`, `_navbar.html`, `_footer.html` (language toggle, GitHub link, "not an official curriculum product"), `index.html`, `error.html`. All fixed copy comes from `modules/i18n.py`.
7. `tests/test_routes.py`:
   - Index 200 with a seed; seedless `/cetak` redirects; a valid spec returns a PDF whose bytes equal the CLI output for the same query.
   - Invalid input gives 400 with translated messages in both languages; 21 pages rejected.
   - 31st request in a minute is 429 when the limiter is enabled; spoofed `X-Forwarded-For` is ignored when `TRUSTED_PROXY_HOPS=0`.
→ Verify: in the browser, every preset, keyboard-only use, JS disabled, 200% zoom, phone width, copied link reproduces the downloaded PDF, Malay and English error pages.

### Phase F: Ship quality

1. `Dockerfile`: python:3.12-slim, pinned `ghcr.io/astral-sh/uv` tag, `uv sync --frozen --no-dev`, non-root, `ENV APP_ENV=production`, requires `SECRET_KEY` at runtime, runs Waitress. `.dockerignore`.
2. `.github/workflows/ci.yml`: `astral-sh/setup-uv` pinned, `uv sync --frozen`, `uv run ruff check .`, `uv run pytest -q`.
3. `tests/test_clean_repo.py`:
   - Candidates are `git ls-files --cached --others --exclude-standard`; fail on an empty list.
   - Images are allowed only under `static/img/`; no PDFs.
   - Decoded text files only (skip binaries by null byte): no absolute home paths, no emails outside `example.com`.
   - Its docstring states it checks file hygiene only, not provenance.
4. `README.md` (Malay and English): what it is, form screenshot and sample page PNGs rendered by the app into `static/img/`, quick start (web, CLI, Docker with `SECRET_KEY`), worksheet types, the determinism and "not official" notes, license.
5. Manual provenance gate before the first public push, done by the main session:
   - Diff every ported primitive against the allowed file.
   - Read all text in `modules/i18n.py` and every literal list for copied content.
   - Check that every image is app output.
→ Verify: `docker build` then `docker run -e SECRET_KEY=...` serves a PDF through Waitress; CI green after the first push.

## Acceptance Criteria

- [ ] `uv run ruff check .` and `uv run pytest -q` pass after every phase.
- [ ] The same normalized spec renders byte-identical PDFs across processes, and web and CLI agree.
- [ ] Generator guarantees hold over directed fixtures and 200 seeds; constrained generators never loop.
- [ ] Every practice sheet has an answer sheet; division answers show full working aligned to columns.
- [ ] Invalid input returns a translated 400, never a 500; impossible combinations are rejected at parse time.
- [ ] The form passes the Phase E accessibility checks in both languages.
- [ ] Automated file hygiene passes and the manual provenance gate is recorded.

## Dependencies

Runtime: Flask, python-dotenv, waitress, reportlab, Flask-Limiter. Dev: pytest, ruff, pypdf. Python 3.12 (pinned via `.python-version`), all through uv.

## Review log

- 2026-11-11, user: add mascot and topic illustrations (agy), a vector picture-counting worksheet slice (Phase D2), and defer interactive practice to v2.
- 2026-11-11, Codex plan review: 2 critical, 10 major, 4 minor. All accepted:
  - Impossible single-digit borrow rejected; constructive generators.
  - Instruction cleanup of every Mongo rule.
  - Sifir pool capacity.
  - Page accounting with worked example.
  - Full spec schema and validation-before-generation.
  - Seed resolved on the form so download and copied link match.
  - Determinism promise narrowed to one release and lockfile.
  - Drawing primitives only, with digit layouts generalized.
  - Long-division convention and step model with directed fixtures.
  - Limiter topology and proxy trust.
  - Accessibility and language criteria.
  - Provenance as a manual gate; scanner limited to text files.
  - PDF checks via pypdf.
  - CLI-dependent verify moved after B2; container sets production mode.
  - Curriculum wording kept narrow.
  - Scope split into slices (grid/add/sub first, then sifir, then division, then web).

## Decisions Log

| Decision | Chosen | Alternatives Considered | Why |
|----------|--------|------------------------|-----|
| Name | CetakKira (`cetak-kira`) | JalanKira, KiraLagi, Congak, KiraKertas | User choice; agy and Codex both ranked it top |
| Form | Web app + CLI | Web only; CLI only | User choice |
| Audience | Malaysian parents and teachers, Malay first | English first; special education | User choice |
| Database | None | Mongo for usage stats | User choice |
| Build order | Right after tradebook Phase A | After tradebook; before video host | User choice |
| Provenance | Generate all content; reuse only drawing primitives | Reuse problem sets and photos | Existing data came from a published workbook |
| Slicing | grid/add/sub, then sifir, then division, then web | All six types at once | Codex review: ship a usable CLI early, review risky layouts separately |
| Page budget | `pages` = total content sheets, answers appended, max 40 | Pages per topic | Predictable print length and CPU bound |
| Remainder option | Nonzero remainder required when on | Remainders allowed | Clear practice intent; testable |
| Sharing | Seed resolved on form render, hidden field | Seed added only by redirect | Copied link must match the download |
| Determinism | Same spec, same release and lockfile | Permanent links across releases | Cross-version guarantees are not available from Python's RNG |
| PDF tests | pypdf (dev only) | Substring token counting | `/Type /Page` also matches `/Pages` |
| Rate limit | Memory storage, single process, ProxyFix only with configured hops | Redis; trusting forwarded headers | No database; correct trust boundary |
| CLI packaging | `uv run python cli.py` | `[project.scripts]` package | Flat house-style layout |
| Prototype | Not needed | prototype-ui pass | Single form; accessibility criteria are explicit instead |
| Visuals | agy-generated mascot and topic icons for the web page and README; vector-drawn picture problems in PDFs; interactive practice deferred to v2 | AI bitmaps inside PDFs | User choice 2026-11-11; PDFs stay printable in black and white and deterministic |
| Fonts | Built-in Helvetica, glyphs checked | Embedded font | Malay is Latin script; arrows and brackets drawn as vectors |
