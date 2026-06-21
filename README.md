# rss-subscriber

A weekly automated RSS digest. A GitHub Actions workflow reads the feeds in [`feeds.txt`](feeds.txt), emails a digest of new articles, and publishes/updates an HTML archive on GitHub Pages

## Automation

[`.github/workflows/weekly.yml`](.github/workflows/weekly.yml) runs every
Sunday at 13:00 UTC (and on demand via `workflow_dispatch`):

1. Installs dependencies with `uv` and runs `main.py --send`, which fetches new items and emails the digest via [Resend](https://resend.com).
2. Commits the generated `site/` directory back to the repo if it changed, archiving that week's digest under `site/archive/` and refreshing `site/index.html`.
3. Deploys `site/` to GitHub Pages, so the full archive stays browsable at `https://monster0506.github.io/rss-subscriber`.

The workflow needs these repository secrets:

| Secret             | Purpose                          |
| ------------------ | --------------------------------- |
| `RESEND_API_KEY`   | Resend API key                    |
| `RECIPIENT_EMAIL`  | Address the digest is sent to     |
| `SENDER_EMAIL`     | Address the digest is sent from   |
| `GIT_AUTHOR_NAME`  | Commit author for the site update |
| `GIT_AUTHOR_EMAIL` | Commit author for the site update |

## Adding feeds

Add a feed URL to `feeds.txt`, one per line, the next scheduled run will pick it up. Items older than `MAX_ARTICLE_AGE_DAYS` are skipped entirely, and only items from the last `DAYS_BACK` days are included in each digest (both configured in `CONFIG.py`).

## Running locally

```bash
uv sync
uv run python main.py
uv run python main.py --send
```
