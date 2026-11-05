"""도메인 -> 사이트 어댑터."""

from __future__ import annotations

from urllib.parse import urlparse

from .adapters import QUASARZONE_DOMAIN, QuasarzoneAdapter, SiteAdapter


class UnknownSiteError(LookupError):
    """등록되지 않은 사이트. 모르는 사이트를 아는 사이트의 파서로 읽지 않는다."""


class AdapterRegistry:
    def __init__(self) -> None:
        self._by_domain: dict[str, SiteAdapter] = {}

    def register(self, domain: str, adapter: SiteAdapter) -> None:
        key = domain.strip().lower()
        if key == "":
            raise ValueError("domain must not be empty")
        if key in self._by_domain:
            raise ValueError(f"domain already registered: {key}")
        self._by_domain[key] = adapter

    def adapter_for_url(self, url: str) -> SiteAdapter:
        host = (urlparse(url).hostname or "").lower()
        for domain, adapter in self._by_domain.items():
            if host == domain or host.endswith("." + domain):
                return adapter
        raise UnknownSiteError(f"no adapter registered for {host or url!r}")

    def domains(self) -> list[str]:
        return sorted(self._by_domain)


def default_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register(QUASARZONE_DOMAIN, QuasarzoneAdapter())
    return registry
