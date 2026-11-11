import os

from dotenv import load_dotenv

load_dotenv()

# Run mode: development | testing | production
#   development — native Flask server, debug on
#   testing     — native Flask server, debug on
#   production  — waitress WSGI server, debug off
APP_ENV = os.environ.get("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"
DEBUG = not IS_PRODUCTION

# Secret key. Production must replace the placeholder that ships in .env.example.
PLACEHOLDER_SECRET_KEY = "dev-secret-change-me"
INSECURE_SECRET_KEYS = {"", PLACEHOLDER_SECRET_KEY, "change-me-in-production"}
SECRET_KEY = os.environ.get("SECRET_KEY", PLACEHOLDER_SECRET_KEY)
if IS_PRODUCTION and SECRET_KEY.strip() in INSECURE_SECRET_KEYS:
    raise RuntimeError("Set a real SECRET_KEY in the environment before running in production.")

PORT = int(os.environ.get("PORT", "5000"))

# Reverse-proxy hops to trust when resolving the client address. 0 means the
# X-Forwarded-For header is ignored entirely.
# Positive hops preserve forwarded headers at Waitress for ProxyFix to interpret.
# Restrict backend access to the configured proxy chain, which must overwrite or
# append X-Forwarded-For correctly. Direct client access permits address spoofing.
TRUSTED_PROXY_HOPS = int(os.environ.get("TRUSTED_PROXY_HOPS", "0"))

# Rate limiting on the PDF route. Memory storage, single process, so counters
# reset on restart.
RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Site identity — used for SEO meta tags, canonical URLs, robots/sitemap.
SITE_NAME = os.environ.get("SITE_NAME", "CetakKira")
SITE_URL = os.environ.get("SITE_URL", "http://localhost:5000").rstrip("/")
