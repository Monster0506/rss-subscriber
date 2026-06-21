import html
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed


import feedparser
import resend


type HtmlContent = str

FEEDS_FILE = Path("feeds.txt")

RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

DAYS_BACK = 7

TAG_RE = re.compile(r"<[^>]+>")


@dataclass(slots=True, frozen=True)
class FeedItem:
    title: str
    link: str
    summary: str
    source: str
    published: datetime


def clean_summary(summary: str) -> str:
    summary = TAG_RE.sub(" ", summary)
    summary = html.unescape(summary)
    summary = " ".join(summary.split())
    return summary[:300]
def fetch_feed(
    url: str,
    cutoff: datetime,
) -> list[FeedItem]:
    print(f"Fetching: {url}")

    feed: Any = feedparser.parse(url)

    if feed.bozo:
        print(
            f"  Warning: Could not parse {url} properly.",
            feed.bozo_exception,
        )

    items: list[FeedItem] = []

    for item in feed.entries:
        published_struct = (
            item.get("published_parsed")
            or item.get("updated_parsed")
        )

        if not published_struct:
            continue

        pub_date = datetime(
            *published_struct[:6],
            tzinfo=timezone.utc,
        )

        if pub_date < cutoff:
            continue

        items.append(
            FeedItem(
                title=str(item.title),
                link=str(item.link),
                summary=clean_summary(
                    item.get(
                        "summary",
                        "No summary available.",
                    )
                ),
                source=str(
                    feed.feed.get(
                        "title",
                        "Unknown Source",
                    )
                ),
                published=pub_date,
            )
        )

    return items

def load_feeds(filepath: Path) -> list[str]:
    feeds: list[str] = []

    try:
        with filepath.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if line and not line.startswith("#"):
                    feeds.append(line)

    except FileNotFoundError:
        print(f"Error: {filepath} not found.")

    return feeds

def fetch_recent_items(
    feed_urls: Sequence[str],
) -> list[FeedItem]:
    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=DAYS_BACK)
    )

    all_items: list[FeedItem] = []

    max_workers = min(32, len(feed_urls))

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:
        futures = {
            executor.submit(
                fetch_feed,
                url,
                cutoff,
            ): url
            for url in feed_urls
        }

        for future in as_completed(futures):
            url = futures[future]

            try:
                all_items.extend(
                    future.result()
                )
            except Exception as exc:
                print(
                    f"Error fetching {url}: {exc}"
                )

    all_items.sort(
        key=lambda item: item.published,
        reverse=True,
    )

    return all_items



def build_html_email(items: Sequence[FeedItem]) -> HtmlContent:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    sources: dict[str, list[FeedItem]] = {}

    for item in items:
        sources.setdefault(item.source, []).append(item)

    if not sources:
        return """
        <html>
        <body style="
            background:#d4d0c8;
            font-family:Segoe UI,Tahoma,Arial,sans-serif;
            padding:24px;
            font-size:16px;
        ">
            <div style="
                max-width:1600px;
                margin:0 auto;
                border:1px solid #404040;
                background:#ffffff;
            ">
                <div style="
                    background:#e6e6e6;
                    padding:12px 16px;
                    font-size:18px;
                    font-weight:600;
                ">
                    Weekly RSS Digest
                </div>

                <div style="padding:32px;">
                    No new posts this week.
                </div>
            </div>
        </body>
        </html>
        """

    html_parts: list[str] = [
        """
        <html>
        <body style="
            margin:0;
            padding:24px;
            background:#d4d0c8;
            font-family:Segoe UI,Tahoma,Arial,sans-serif;
            font-size:16px;
            line-height:1.5;
            color:#000;
        ">
        <div style="
            max-width:1200px;
            margin:0 auto;
            border:1px solid #404040;
            background:#ffffff;
        ">
        """
    ]

    html_parts.append(
        f"""
        <div style="
            background:#e6e6e6;
            border-bottom:1px solid #bdbdbd;
            padding:10px 14px;
            font-size:15px;
        ">
            <span style="margin-right:28px;">
                <strong>Feeds:</strong> {len(sources)}
            </span>

            <span style="margin-right:28px;">
                <strong>Articles:</strong> {len(items)}
            </span>

            <span>
                <strong>Period:</strong> Last {DAYS_BACK} Days
            </span>
        </div>
        """
    )

    html_parts.append(
        """
        <div style="
            background:#f3f3f3;
            border-bottom:1px solid #d0d0d0;
            padding:10px 14px;
            font-weight:600;
            font-size:17px;
        ">
            Weekly Summary
        </div>
        """
    )

    html_parts.append("<div style='padding:18px;'>")

    for source in sorted(sources):
        source_items = sorted(
            sources[source],
            key=lambda item: item.published,
            reverse=True,
        )

        html_parts.append(
            f"""
            <div style="
                margin-bottom:28px;
                border:1px solid #d5d5d5;
            ">
                <div style="
                    background:#ececec;
                    padding:10px 14px;
                    border-bottom:1px solid #d5d5d5;
                    font-weight:600;
                    font-size:18px;
                ">
                    {html.escape(source)}

                    <span style="
                        float:right;
                        color:#666;
                        font-weight:normal;
                        font-size:14px;
                    ">
                        {len(source_items)} items
                    </span>
                </div>
            """
        )

        for idx, item in enumerate(source_items):
            bg = "#ffffff" if idx % 2 == 0 else "#f8f8f8"

            title = html.escape(item.title)
            summary = html.escape(item.summary)
            link = html.escape(item.link, quote=True)
            date = item.published.strftime("%Y-%m-%d")

            html_parts.append(
                f"""
                <div style="
                    padding:14px 16px;
                    border-bottom:1px solid #ececec;
                    background:{bg};
                ">
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        gap:16px;
                        align-items:flex-start;
                    ">
                        <div style="
                            flex:1;
                            font-weight:600;
                            font-size:18px;
                            line-height:1.4;
                        ">
                            <a href="{link}"
                               style="
                                    color:#004a9f;
                                    text-decoration:none;
                               ">
                                {title}
                            </a>
                        </div>

                        <div style="
                            color:#666;
                            white-space:nowrap;
                            font-family:Consolas,monospace;
                            font-size:14px;
                        ">
                            {date}
                        </div>
                    </div>

                    <div style="
                        margin-top:8px;
                        color:#555;
                        line-height:1.6;
                        font-size:15px;
                    ">
                        {summary}
                    </div>
                </div>
                """
            )

        html_parts.append("</div>")

    html_parts.append("</div>")

    html_parts.append(
        f"""
        <div style="
            border-top:1px solid #bdbdbd;
            background:#e6e6e6;
            padding:10px 14px;
            color:#555;
            font-size:14px;
        ">
            Generated {generated}
        </div>
        """
    )

    html_parts.append("</div></body></html>")

    return "".join(html_parts)


def send_email(html_content: HtmlContent) -> None:
    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY environment variable is not set"
        )

    if not RECIPIENT_EMAIL:
        raise RuntimeError(
            "RECIPIENT_EMAIL environment variable is not set"
        )

    if not SENDER_EMAIL:
        raise RuntimeError(
            "SENDER_EMAIL environment variable is not set"
        )

    resend.api_key = RESEND_API_KEY

    email: Any = resend.Emails.send(
        {
            "from": SENDER_EMAIL,
            "to": [RECIPIENT_EMAIL],
            "subject": "Your Weekly RSS Digest",
            "html": html_content,
        }
    )

    print(email)


def main() -> None:
    send_email_flag = "--send" in sys.argv

    feed_urls = load_feeds(FEEDS_FILE)

    if not feed_urls:
        print("No feeds found in feeds.txt. Exiting.")
        return

    print(
        f"Loaded {len(feed_urls)} feeds. "
        "Fetching recent items..."
    )

    items = fetch_recent_items(feed_urls)

    print(
        f"Found {len(items)} new items. "
        "Building email..."
    )

    html_content = build_html_email(items)

    if send_email_flag:
        print("Sending email...")
        send_email(html_content)
    output_file = Path("feed.html")

    output_file.write_text(
        html_content,
        encoding="utf-8",
    )

    print(f"Wrote preview to {output_file}")


if __name__ == "__main__":
    main()