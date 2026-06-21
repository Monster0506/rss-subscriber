import html
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import feedparser

from CONFIG import DAYS_BACK, TAG_RE
from storage_helpers import (
    article_id,
    load_seen_articles,
    prune_seen_articles,
    save_seen_articles,
)


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
    seen: dict[str, dict],
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
        published_struct = item.get("published_parsed") or item.get("updated_parsed")

        if not published_struct:
            continue

        pub_date = datetime(
            *published_struct[:6],
            tzinfo=timezone.utc,
        )
        article_key = article_id(item)

        if article_key in seen:
            print(f"Found: {item.title}")
            continue

        if pub_date < cutoff:
            continue

        seen[article_key] = {
            "link": str(item.link),
            "first_seen": datetime.now(timezone.utc).isoformat(),
        }

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
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)

    seen = prune_seen_articles(load_seen_articles())

    all_items: list[FeedItem] = []

    max_workers = min(
        32,
        len(feed_urls),
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                fetch_feed,
                url,
                cutoff,
                seen,
            ): url
            for url in feed_urls
        }

        for future in as_completed(futures):
            url = futures[future]

            try:
                all_items.extend(future.result())
            except Exception as exc:
                print(f"Error fetching {url}: {exc}")

    save_seen_articles(seen)

    all_items.sort(
        key=lambda item: item.published,
        reverse=True,
    )

    return all_items
