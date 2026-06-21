import sys
from typing import Any

import resend

from CONFIG import FEEDS_FILE, INDEX_FILE
from fetch_helpers import fetch_recent_items, load_feeds
from html_helpers import build_archive_index, build_html_email, write_archive

type HtmlContent = str


def send_email(html_content: HtmlContent) -> None:
    from CONFIG import RECIPIENT_EMAIL, RESEND_API_KEY, SENDER_EMAIL

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY environment variable is not set")

    if not RECIPIENT_EMAIL:
        raise RuntimeError("RECIPIENT_EMAIL environment variable is not set")

    if not SENDER_EMAIL:
        raise RuntimeError("SENDER_EMAIL environment variable is not set")

    resend.api_key = RESEND_API_KEY

    params: resend.Emails.SendParams = {
        "from": SENDER_EMAIL,
        "to": [RECIPIENT_EMAIL],
        "subject": "Your Weekly RSS Digest",
        "html": html_content,
    }
    email: Any = resend.Emails.send(params)

    print(email)


def main() -> None:
    send_email_flag = "--send" in sys.argv

    feed_urls = load_feeds(FEEDS_FILE)

    if not feed_urls:
        print("No feeds found in feeds.txt. Exiting.")
        return

    print(f"Loaded {len(feed_urls)} feeds. Fetching recent items...")

    items = fetch_recent_items(feed_urls)

    print(f"Found {len(items)} new items. Building email...")
    html_content = build_html_email(items)

    archive_file = write_archive(html_content)

    INDEX_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    INDEX_FILE.write_text(
        build_archive_index(),
        encoding="utf-8",
    )

    print(f"Wrote archive to {archive_file}")

    print(f"Wrote archive index to {INDEX_FILE}")

    if send_email_flag:
        print("Sending email...")
        send_email(html_content)


if __name__ == "__main__":
    main()

