import os
import re

from pathlib import Path

FEEDS_FILE = Path("feeds.txt")
SITE_DIR = Path("site")
ARCHIVE_DIR = SITE_DIR / "archive"
INDEX_FILE = SITE_DIR / "index.html"

SEEN_FILE = SITE_DIR / "seen_articles.json"
MAX_ARTICLE_AGE_DAYS = 180

RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
ARCHIVE_BASE_URL = os.environ.get("ARCHIVE_BASE_URL")

DAYS_BACK = 30

TAG_RE = re.compile(r"<[^>]+>")
