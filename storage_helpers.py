import hashlib
import json
from datetime import datetime, timedelta, timezone

from CONFIG import MAX_ARTICLE_AGE_DAYS, SEEN_FILE


def article_id(item: Any) -> str:
    raw = item.get("id") or item.get("guid") or item.get("link") or item.get("title")

    return hashlib.sha256(str(raw).encode("utf-8")).hexdigest()


def load_seen_articles() -> dict[str, dict]:
    if not SEEN_FILE.exists():
        return {}

    try:
        return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_seen_articles(seen: dict[str, dict]) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(
        json.dumps(
            seen,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def prune_seen_articles(seen: dict[str, dict]) -> dict[str, dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_ARTICLE_AGE_DAYS)

    result = {}

    for key, value in seen.items():
        try:
            first_seen = datetime.fromisoformat(value["first_seen"])

            if first_seen >= cutoff:
                result[key] = value

        except Exception:
            pass

    return result

