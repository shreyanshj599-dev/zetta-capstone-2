from urllib.parse import urlparse


def canonicalize_domain(url: str) -> str:
    """Reduce any URL or bare host to a single canonical domain.

    https://www.foo.com/about, foo.com, FOO.COM/ all → 'foo.com'.
    """
    raw = url.strip()
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        raise ValueError(f"Could not extract domain from: {url!r}")
    return host
