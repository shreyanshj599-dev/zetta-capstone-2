"""Lightweight site scraper.

We hit the homepage plus a few well-known company pages and return cleaned
text per URL. Not trying to bypass JS-rendered sites or bot protections —
the goal is enough text for an LLM to extract company facts, not full
crawling.

The @retry decorator (Bucket 1: Decorator pattern) handles transient
network failures with exponential backoff.
"""

from dataclasses import dataclass

import httpx
from selectolax.parser import HTMLParser
from tenacity import retry, stop_after_attempt, wait_exponential

CANDIDATE_PATHS = ["", "/about", "/about-us", "/company", "/careers", "/jobs"]
USER_AGENT = "ZettaLeadEnrichBot/0.1 (+https://github.com/shreyanshj599-dev/zetta-capstone)"
TIMEOUT = 10.0
MAX_TEXT_PER_PAGE = 6000


@dataclass(slots=True)
class FetchedPage:
    url: str
    text: str


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4), reraise=True)
def _fetch(client: httpx.Client, url: str) -> httpx.Response | None:
    """Fetch a single URL. Returns None on 4xx (we just skip the page)."""
    resp = client.get(url, follow_redirects=True)
    if 400 <= resp.status_code < 500:
        return None
    resp.raise_for_status()
    return resp


def _extract_text(html: str) -> str:
    parser = HTMLParser(html)
    # Strip noise — selectolax has no built-in helper, so iterate.
    for tag in ("script", "style", "noscript", "svg", "iframe", "header", "footer", "nav"):
        for node in parser.css(tag):
            node.decompose()
    body = parser.body
    if body is None:
        return ""
    text = body.text(separator=" ", strip=True)
    return text[:MAX_TEXT_PER_PAGE]


def fetch_pages(domain: str) -> list[FetchedPage]:
    """Try each candidate path on the domain; return whatever responds with text."""
    base = f"https://{domain}"
    pages: list[FetchedPage] = []
    seen_text: set[str] = set()

    with httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        follow_redirects=True,
    ) as client:
        for path in CANDIDATE_PATHS:
            url = base + path
            try:
                resp = _fetch(client, url)
            except (httpx.HTTPError, httpx.TimeoutException):
                continue
            if resp is None or not resp.text:
                continue
            text = _extract_text(resp.text)
            if not text or text in seen_text:
                continue
            seen_text.add(text)
            pages.append(FetchedPage(url=str(resp.url), text=text))

    return pages
