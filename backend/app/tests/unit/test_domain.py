import pytest

from app.utils.domain import canonicalize_domain


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://www.foo.com/about", "foo.com"),
        ("foo.com", "foo.com"),
        ("FOO.COM/", "foo.com"),
        ("https://foo.com", "foo.com"),
        ("http://www.sub.foo.com/path?x=1", "sub.foo.com"),
        ("  HTTPS://Anthropic.com  ", "anthropic.com"),
    ],
)
def test_canonicalize_domain(raw: str, expected: str) -> None:
    assert canonicalize_domain(raw) == expected


def test_canonicalize_domain_rejects_empty() -> None:
    with pytest.raises(ValueError):
        canonicalize_domain("")
    with pytest.raises(ValueError):
        canonicalize_domain("https://")
