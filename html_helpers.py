import html
from datetime import datetime

from CONFIG import ARCHIVE_BASE_URL, ARCHIVE_DIR, DAYS_BACK


def build_archive_index() -> str:
    files = sorted(
        ARCHIVE_DIR.glob("*.html"),
        reverse=True,
    )

    items = []

    for file in files:
        items.append(
            f"""
            <li style="margin:12px 0;">
                <a href="archive/{file.name}">
                    {file.stem}
                </a>
            </li>
            """
        )

    return f"""
    <html>
    <body style="
        background:#d4d0c8;
        font-family:Segoe UI,Tahoma,Arial,sans-serif;
        padding:24px;
        font-size:18px;
    ">
        <div style="
            max-width:1000px;
            margin:0 auto;
            background:white;
            border:1px solid #404040;
        ">
            <div style="
                background:#ececec;
                padding:16px;
                font-size:24px;
                font-weight:600;
            ">
                RSS Digest Archive
            </div>

            <div style="padding:24px;">
                <ul>
                    {"".join(items)}
                </ul>
            </div>
        </div>
    </body>
    </html>
    """


def write_archive(
    html_content: str,
) -> Path:
    ARCHIVE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = datetime.now().strftime("%Y-%m-%d") + ".html"

    outfile = ARCHIVE_DIR / filename

    outfile.write_text(
        html_content,
        encoding="utf-8",
    )

    return outfile


def build_html_email(items: Sequence[FeedItem]) -> HtmlContent:
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    today = datetime.now().strftime("%Y-%m-%d")
    current_file = today + ".html"

    archive_url = f"{ARCHIVE_BASE_URL}/archive/{today}.html"

    archive_files = sorted(f.name for f in ARCHIVE_DIR.glob("*.html"))

    previous_link = None

    if archive_files:
        previous_link = archive_files[-1]

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
                <strong><a href="{ARCHIVE_BASE_URL}">Home</a></strong>
            </span>
            
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
        f"""
        <div style="
            background:#f3f3f3;
            border-bottom:1px solid #d0d0d0;
            padding:10px 14px;
            font-weight:600;
            font-size:17px;
        ">
            <a href="{archive_url}">Weekly Summary</a>
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
    if previous_link:
        html_parts.append(
            f"""
            <div style="
                padding:14px;
                border-top:1px solid #d0d0d0;
                background:#f7f7f7;
            ">
                <a href="{ARCHIVE_BASE_URL}/archive/{previous_link}">
                    ← Previous Week
                </a>
            </div>
            """
        )
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

