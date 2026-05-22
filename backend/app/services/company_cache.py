import json
import logging
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.schemas.company import CompanyOut

log = logging.getLogger(__name__)
settings = get_settings()
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

CACHE_VERSION = "v1"


def _key(domain: str) -> str:
    return f"company-cache:{CACHE_VERSION}:{domain.lower()}"


def get_company(domain: str) -> CompanyOut | None:
    try:
        payload = redis_client.get(_key(domain))
    except RedisError as exc:
        log.warning("company_cache_get_failed domain=%s err=%s", domain, exc)
        return None

    if not payload:
        return None

    try:
        return CompanyOut.model_validate(json.loads(payload))
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("company_cache_decode_failed domain=%s err=%s", domain, exc)
        delete_company(domain)
        return None


def set_company(company: CompanyOut) -> None:
    try:
        redis_client.setex(
            _key(company.domain),
            settings.company_cache_ttl_seconds,
            company.model_dump_json(),
        )
    except RedisError as exc:
        log.warning("company_cache_set_failed domain=%s err=%s", company.domain, exc)


def delete_company(domain: str) -> None:
    try:
        redis_client.delete(_key(domain))
    except RedisError as exc:
        log.warning("company_cache_delete_failed domain=%s err=%s", domain, exc)


def cache_status(domain: str) -> dict[str, Any]:
    key = _key(domain)
    try:
        return {
            "key": key,
            "exists": bool(redis_client.exists(key)),
            "ttl_seconds": redis_client.ttl(key),
        }
    except RedisError as exc:
        log.warning("company_cache_status_failed domain=%s err=%s", domain, exc)
        return {"key": key, "exists": False, "ttl_seconds": None}
