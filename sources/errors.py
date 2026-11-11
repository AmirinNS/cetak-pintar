# Themed error handling. One template (error.html) serves every HTTP status;
# API/XHR callers get JSON. Registered for all codes so nothing falls back to
# Flask's default page.
import logging

from flask import jsonify, make_response, render_template, request
from werkzeug.exceptions import default_exceptions

from modules.i18n import t

log = logging.getLogger(__name__)


def _get_request_lang() -> str:
    """Extract and validate the request language ('ms' or 'en', default 'ms')."""
    try:
        lang = request.args.get("lang", "").strip().lower()
        if lang in ("ms", "en"):
            return lang
    except Exception:
        pass
    return "ms"


def _wants_json() -> bool:
    """API/XHR callers should get JSON, not an HTML page."""
    if request.path.startswith("/api"):
        return True
    accept = request.accept_mimetypes
    return accept.best == "application/json" and accept["application/json"] >= accept["text/html"]


def _render_error(error):
    code = getattr(error, "code", 500) or 500
    status_label = getattr(error, "name", "Error")
    lang = _get_request_lang()

    heading_key = f"error_{code}_heading"
    message_key = f"error_{code}_message"
    heading = t(heading_key, lang=lang)
    message = t(message_key, lang=lang)

    # If i18n key was missing and returned the key itself, provide clean fallbacks
    if heading == heading_key:
        heading = status_label
    if message == message_key:
        message = (
            "Sesuatu ralat berlaku. Sila cuba lagi."
            if lang == "ms"
            else "An unexpected error occurred. Please try again."
        )

    if _wants_json():
        resp = jsonify(success=False, error=status_label, code=code, message=message)
        response = make_response(resp, code)
        if code == 429:
            response.headers["Retry-After"] = "60"
        return response

    try:
        html = render_template(
            "error.html",
            code=code,
            status_label=status_label,
            heading=heading,
            message=message,
            lang=lang,
            t=t,
        )
    except Exception:
        # Last-resort fallback if template/context rendering itself fails.
        # Keep it dependency-free.
        log.exception("error page render failed")
        back_label = "Kembali ke Laman Utama" if lang == "ms" else "Back to Home"
        html = (
            f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'>"
            f"<title>{code}</title></head><body>"
            f"<h1>{code} — {heading}</h1><p>{message}</p>"
            f"<p><a href='/?lang={lang}'>{back_label}</a></p></body></html>"
        )

    response = make_response(html, code)
    if code == 429:
        response.headers["Retry-After"] = "60"
    return response


def init_errors(app):
    """Register the themed handler for every HTTP status Werkzeug knows about."""
    for code in default_exceptions:
        app.register_error_handler(code, _render_error)
