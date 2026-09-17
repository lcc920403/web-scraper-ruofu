#!/usr/bin/env python3
import sqlite3
import time
from collections import deque
from datetime import datetime, timezone
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://example.com"
START_URLS = [
    "https://example.com/news",
    "https://example.com/"
]
ITEM_SELECTOR = "article, .post, .news-item, .card, .item"
TITLE_SELECTOR = "h2, h3, .title, .headline"
LINK_SELECTOR = "a[href]"
CONTENT_SELECTOR = "p"
ALLOWED_DOMAINS = ["example.com"]
MAX_PAGES = 20
REQUEST_DELAY_SECONDS = 1.0
DB_PATH = "scraped_data.db"


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scraped_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT UNIQUE,
            content TEXT,
            source TEXT,
            fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def clean_text(value: str) -> str:
    return " ".join(value.split())


def extract_title(item_tag) -> str:
    for selector in TITLE_SELECTOR.split(","):
        selector = selector.strip()
        if not selector:
            continue
        match = item_tag.select_one(selector)
        if match:
            return clean_text(match.get_text(" ", strip=True))
    return clean_text(item_tag.get_text(" ", strip=True)[:200])


def extract_link(item_tag, base_url: str) -> str:
    for selector in LINK_SELECTOR.split(","):
        selector = selector.strip()
        if not selector:
            continue
        match = item_tag.select_one(selector)
        if match and match.get("href"):
            href = match.get("href")
            return urljoin(base_url, href)
    return ""


def extract_content(item_tag) -> str:
    pieces = []
    for selector in CONTENT_SELECTOR.split(","):
        selector = selector.strip()
        if not selector:
            continue
        for node in item_tag.select(selector):
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                pieces.append(text)
    if pieces:
        return " | ".join(pieces)[:3000]
    return clean_text(item_tag.get_text(" ", strip=True)[:3000])


def is_allowed_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return any(domain.lower() in host for domain in ALLOWED_DOMAINS)


def parse_page(html: str, url: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for tag in soup.select(ITEM_SELECTOR):
        title = extract_title(tag)
        link = extract_link(tag, url)
        content = extract_content(tag)
        if not title and not link:
            continue
        if link and not is_allowed_url(link):
            continue
        items.append(
            {
                "title": title[:255],
                "url": link or url,
                "content": content[:5000],
                "source": url,
            }
        )
    return items


def save_items(conn: sqlite3.Connection, items: List[Dict[str, Any]]) -> int:
    inserted = 0
    for item in items:
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO scraped_items (title, url, content, source, fetched_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item.get("title"),
                    item.get("url"),
                    item.get("content"),
                    item.get("source"),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            inserted += conn.total_changes
        except Exception:
            continue
    conn.commit()
    return inserted


def crawl() -> None:
    conn = init_db()
    queue = deque(START_URLS)
    visited = set()
    count = 0

    while queue and count < MAX_PAGES:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            html = fetch_html(url)
            items = parse_page(html, url)
            save_items(conn, items)
            count += 1

            soup = BeautifulSoup(html, "html.parser")
            for link in soup.select(LINK_SELECTOR):
                href = link.get("href")
                if not href:
                    continue
                next_url = urljoin(url, href)
                if is_allowed_url(next_url) and next_url not in visited:
                    queue.append(next_url)

        except Exception as exc:
            print(f"[ERROR] {url}: {exc}")
        time.sleep(REQUEST_DELAY_SECONDS)

    print(f"[DONE] 已完成抓取，資料已存入 {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    print("[INFO] 啟動自動抓補器...")
    crawl()
    print("[INFO] 程式結束")

