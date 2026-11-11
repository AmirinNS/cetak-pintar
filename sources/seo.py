# Baseline SEO helpers: default meta tags and canonical URLs. Pure functions.
# For JSON-LD structured data and dynamic sitemaps, use the add-capability skill (seo).
from urllib.parse import urljoin

from flask import request

from sources.config import SITE_NAME, SITE_URL

# Site-wide defaults. Override per page via the render_template() context
# or the {% block %}s in base.html.
META_DESCRIPTION = (
    "Printable A4 math worksheets for Malaysian primary school kids, "
    "with answer keys. Web app and CLI."
)
META_IMAGE = SITE_URL + "/static/img/og-default.png"


def canonical_url():
    """Absolute canonical URL for the current request (query string dropped)."""
    return urljoin(SITE_URL + "/", request.path.lstrip("/"))


def default_meta():
    """Baseline SEO context injected into every template."""
    return {
        "site_name": SITE_NAME,
        "meta_description": META_DESCRIPTION,
        "meta_image": META_IMAGE,
        "canonical_url": canonical_url(),
    }
