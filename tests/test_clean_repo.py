"""File hygiene checks for the repository as git reports it.

This checks hygiene only, not provenance. It cannot tell whether a line of text
was written fresh or copied, and it never looks inside the worksheet generators,
the rendered PDFs, or the images. Provenance is a separate manual gate.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = "static/img/"
IMAGE_SUFFIXES = frozenset({
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".svg",
    ".ico",
    ".tif",
    ".tiff",
})
ABSOLUTE_HOME_PATH = re.compile(r"/(Users|home)/")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALLOWED_EMAIL_DOMAIN = "example.com"


def candidate_files() -> list[str]:
    """Staged, tracked, and untracked-but-not-ignored paths, relative to the repo root."""
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def text_files() -> list[tuple[str, str]]:
    """Decoded text files with their paths. Binaries and undecodable files are skipped."""
    found = []
    for rel_path in candidate_files():
        data = (REPO_ROOT / rel_path).read_bytes()
        if b"\x00" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        found.append((rel_path, text))
    return found


def test_candidate_list_is_not_empty() -> None:
    """The git query must return files, otherwise every check below would pass vacuously."""
    candidates = candidate_files()
    assert candidates, "git ls-files --cached --others --exclude-standard returned no files"


def test_no_pdfs_and_images_live_only_in_static_img() -> None:
    """No PDF is committed, and images live only under static/img/."""
    offenders = []
    for rel_path in candidate_files():
        suffix = Path(rel_path).suffix.lower()
        if suffix == ".pdf":
            offenders.append(f"{rel_path}: PDFs are generated per request, never stored")
        elif suffix in IMAGE_SUFFIXES and not rel_path.startswith(IMAGES_DIR):
            offenders.append(f"{rel_path}: images belong under {IMAGES_DIR}")
    assert not offenders, "; ".join(offenders)


def test_no_absolute_home_paths() -> None:
    """No absolute macOS or Linux home path leaks into a committed text file."""
    offenders = [
        f"{rel_path}: {ABSOLUTE_HOME_PATH.search(text).group(0)}"
        for rel_path, text in text_files()
        if ABSOLUTE_HOME_PATH.search(text)
    ]
    assert not offenders, "; ".join(offenders)


def test_no_personal_email_addresses() -> None:
    """Only reserved example.com addresses appear, so no personal email is committed."""
    offenders = []
    for rel_path, text in text_files():
        for match in EMAIL.finditer(text):
            domain = match.group(0).rsplit("@", 1)[1]
            if domain != ALLOWED_EMAIL_DOMAIN and not domain.endswith("." + ALLOWED_EMAIL_DOMAIN):
                offenders.append(f"{rel_path}: {match.group(0)}")
    assert not offenders, "; ".join(offenders)
