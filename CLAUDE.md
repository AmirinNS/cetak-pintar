# CLAUDE.md — CetakKira

Printable A4 math worksheets for Malaysian primary school kids, with answer keys. Web app and CLI.

## Stack

- **Backend:** Flask (`cetak_kira.py` entrypoint, thin routes)
- **Database:** none. Worksheet settings live in the URL and PDFs are generated per request, never stored.
- **Frontend:** Jinja2 templates + Bootstrap 5 (CDN) + vanilla JS

## Python environment (mandatory)

Never use system python/pip or bare virtualenvs. Always use `uv`:

    uv run python <script>
    uv add <package>
    uv run pytest
    uv run ruff check .

## Architecture rules

- Functional only. No classes for business logic or views. A class is allowed only when a framework demands one (for example `flask-login`'s `User(UserMixin)`), for a custom exception type, or for a `frozen=True` dataclass value object.
- Business logic lives in `modules/` as pure functions. No database; worksheet functions are pure and take no `db`.
- Route handlers stay thin: parse request → call a `modules/` function → render/return.
- Shared helpers and config live in `sources/`.
- Shared page chrome (navbar, footer) lives in `templates/_navbar.html` / `templates/_footer.html`, pulled in with `{% include %}`.
- Baseline SEO lives in `base.html` (meta/OG/Twitter/canonical) + `sources/seo.py` (defaults, `canonical_url()`) + `/robots.txt` and `/sitemap.xml` routes. Override per page via `{% block title %}` / `{% block meta_description %}`. JSON-LD and dynamic sitemaps come from the `add-capability` skill (seo).
- All imports at the top of the file. Never import inside a function.
- 4-space indentation.
- If you add a Python dependency, run `uv add <package>` (or `uv add --dev <package>` for dev tools).
- Stack changes (a different framework or storage layer) require explicit user approval.
- Use the `python-development` skill when writing or editing Python. It carries the depth these bullets cannot: PEP 8 specifics, error handling at trust boundaries, stdlib choices, and the footguns to check for.

## Run modes

`APP_ENV` (in `.env`) selects the mode. One mode-aware entrypoint:

- **development** (default) — native Flask server, debug on
- **testing** — native Flask server, debug on
- **production** — waitress WSGI server, debug off

The native Flask server is dev/testing only; production is served by waitress (`sources/config.py` sets `IS_PRODUCTION`/`DEBUG`, the entrypoint picks the server). There is nothing else to configure per environment beyond `.env`; the app keeps no database and stores no worksheets.

    # development
    uv run python cetak_kira.py
    # production (waitress)
    APP_ENV=production uv run python cetak_kira.py
    # http://localhost:5000

## Plans

Feature plans go in `plans/` as kebab-case markdown.
