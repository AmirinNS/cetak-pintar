# Standard library
import urllib.parse
from dataclasses import replace
from datetime import UTC, datetime

# Third-party
from flask import Flask, Response, jsonify, redirect, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from waitress import serve
from werkzeug.datastructures import MultiDict
from werkzeug.middleware.proxy_fix import ProxyFix

# Local
from modules.i18n import t
from modules.render.pdf import render
from modules.spec import parse_spec, spec_to_query
from sources import seo
from sources.config import (
    APP_ENV,
    DEBUG,
    IS_PRODUCTION,
    PORT,
    RATELIMIT_ENABLED,
    SECRET_KEY,
    SITE_URL,
    TRUSTED_PROXY_HOPS,
)
from sources.errors import init_errors
from sources.form import build_form_context, resolve_seed

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configure reverse-proxy trust only when configured hops > 0
if TRUSTED_PROXY_HOPS > 0:
    app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
        app.wsgi_app, x_for=TRUSTED_PROXY_HOPS, x_proto=0,
    )

# Memory storage rate limiter: 30 requests/minute per client address
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
    enabled=RATELIMIT_ENABLED,
)

init_errors(app)  # themed error pages for every HTTP status


@app.context_processor
def inject_globals():
    """Globals available in every template (year, i18n, baseline SEO, lang switcher)."""

    def lang_url(target_lang: str) -> str:
        args = MultiDict(request.args)
        args["lang"] = target_lang
        encoded = urllib.parse.urlencode(args, doseq=True)
        return f"{request.path}?{encoded}" if encoded else request.path

    ctx = {
        "current_year": datetime.now(UTC).year,
        "t": t,
        "lang_url": lang_url,
    }
    ctx.update(seo.default_meta())
    return ctx


@app.route("/")
def index():
    """Render the worksheet configuration form with a resolved seed in a hidden field."""
    ctx = build_form_context(request.args)
    return render_template("index.html", **ctx)


@app.route("/cetak")
@limiter.limit("30 per minute")
def cetak():
    """Generate and return inline worksheet PDF or re-render form on validation errors."""
    args = MultiDict(request.args)
    if "preset" not in args and "t" not in args and not args.get("seed", "").strip():
        args["preset"] = "t1"
    # Parse original scalar multiplicity before resolving a missing or blank seed.
    spec, errors = parse_spec(args)
    if errors or spec is None:
        ctx = build_form_context(request.args, errors=errors)
        return render_template("index.html", **ctx), 400

    if spec.seed is None:
        spec = replace(spec, seed=resolve_seed(None))
        return redirect(f"/cetak?{spec_to_query(spec)}", code=302)

    pdf_bytes = render(spec)
    topics_part = "_".join(spec.t)
    filename = f"cetakkira-{topics_part}-{spec.seed}.pdf"
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Content-Type": "application/pdf",
    }
    return Response(pdf_bytes, headers=headers, mimetype="application/pdf")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "env": APP_ENV})


@app.route("/robots.txt")
def robots_txt():
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        "Sitemap: " + SITE_URL + "/sitemap.xml",
    ]) + "\n"
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    urls = [SITE_URL + "/"]
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{u}</loc></url>" for u in urls)
        + "</urlset>"
    )
    return Response(body, mimetype="application/xml")


if __name__ == "__main__":
    if IS_PRODUCTION:
        # Production: proper WSGI server. The native Flask server is dev-only.
        serve(
            app, host="0.0.0.0", port=PORT,
            clear_untrusted_proxy_headers=TRUSTED_PROXY_HOPS <= 0,
        )
    else:
        # development / testing: native Flask server with the debugger.
        app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
