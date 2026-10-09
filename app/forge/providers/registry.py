"""Provider registry and factory (Book II / Bloc II.5, Ch II.5.6).

Ch II.5.6: "Configuration selects adapters at composition root.
No `if provider == whop` spread through domain code."

- `ProviderRegistry`: typed port bindings, freeze-able, fail-closed.
- `ProviderFactory`: name -> builder table per port; extending it (e.g. adding
  a concrete adapter later) is a composition change, never a domain rewrite.
- `providers_from_config()`: the composition-root selection point. An unknown
  provider name raises ProviderConfigurationError — nothing silently degrades.

Import law: this package (including this module) must not import FastAPI,
HTTP clients, or SQL drivers — enforced by AST test.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Mapping

from app.forge.config import ForgeConfig
from app.forge.providers.commerce import CommerceProvider
from app.forge.providers.doctrine import PORTS
from app.forge.providers.errors import ProviderConfigurationError
from app.forge.providers.fakes import (
    FakeCommerceProvider,
    FakeLLMProvider,
    FakeNotificationProvider,
    FakeStorageProvider,
)
from app.forge.providers.llm import LLMProvider
from app.forge.providers.notification import NotificationProvider
from app.forge.providers.storage import StorageProvider

# Runtime structural check per port (runtime_checkable protocols).
PORT_PROTOCOLS: Mapping[str, type] = {
    "llm": LLMProvider,
    "commerce": CommerceProvider,
    "notification": NotificationProvider,
    "storage": StorageProvider,
}

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


class ProviderRegistry:
    """Frozen-able map of port -> (name, implementation)."""

    def __init__(self) -> None:
        self._bindings: dict[str, tuple[str, Any]] = {}
        self._frozen = False

    def register(self, port: str, name: str, impl: Any) -> None:
        if self._frozen:
            raise RuntimeError("provider registry is frozen")
        if port not in PORT_PROTOCOLS:
            raise ProviderConfigurationError(f"unknown provider port {port!r}")
        if not _NAME_RE.match(name or ""):
            raise ProviderConfigurationError(f"invalid provider name {name!r}")
        if port in self._bindings:
            raise ProviderConfigurationError(
                f"provider port {port!r} is already bound"
            )
        protocol = PORT_PROTOCOLS[port]
        if not isinstance(impl, protocol):
            raise TypeError(
                f"{port} implementation must satisfy the {port} provider port"
            )
        self._bindings[port] = (name, impl)

    def get(self, port: str) -> Any:
        try:
            _name, impl = self._bindings[port]
        except KeyError:
            raise ProviderConfigurationError(
                f"provider port {port!r} is not bound"
            ) from None
        return impl

    def name(self, port: str) -> str:
        try:
            name, _impl = self._bindings[port]
        except KeyError:
            raise ProviderConfigurationError(
                f"provider port {port!r} is not bound"
            ) from None
        return name

    def ports(self) -> tuple[str, ...]:
        return tuple(self._bindings)

    def bound_names(self) -> dict[str, str]:
        return {port: name for port, (name, _impl) in self._bindings.items()}

    def implementations(self) -> tuple[Any, ...]:
        return tuple(impl for _name, impl in self._bindings.values())

    def freeze(self) -> None:
        self._frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._frozen


# A builder receives the FORGE config and returns a port-conforming impl.
Builder = Callable[[ForgeConfig], Any]


class ProviderFactory:
    """name -> builder tables, one per port. The extension point for concrete
    adapters (Book IV OpenRouter, Book VI Whop, ...): register a builder here,
    select it via config, touch nothing in domain code."""

    def __init__(self) -> None:
        self._builders: dict[str, dict[str, Builder]] = {
            port: {} for port in PORTS
        }

    def register(self, port: str, name: str, builder: Builder) -> None:
        if port not in PORTS:
            raise ProviderConfigurationError(f"unknown provider port {port!r}")
        if not _NAME_RE.match(name or ""):
            raise ProviderConfigurationError(f"invalid provider name {name!r}")
        if name in self._builders[port]:
            raise ProviderConfigurationError(
                f"builder {name!r} already registered for port {port!r}"
            )
        self._builders[port][name] = builder

    def build(self, port: str, name: str, config: ForgeConfig) -> Any:
        if port not in PORTS:
            raise ProviderConfigurationError(f"unknown provider port {port!r}")
        try:
            builder = self._builders[port][name]
        except KeyError:
            raise ProviderConfigurationError(
                f"no provider builder registered for port {port!r} "
                f"name {name!r}"
            ) from None
        return builder(config)

    def names(self, port: str) -> tuple[str, ...]:
        if port not in PORTS:
            raise ProviderConfigurationError(f"unknown provider port {port!r}")
        return tuple(self._builders[port])


def default_provider_factory() -> ProviderFactory:
    """Fresh factory pre-registered with the II.5 deterministic fakes."""

    factory = ProviderFactory()
    factory.register(
        "llm", "fake", lambda config: FakeLLMProvider(name="fake")
    )
    factory.register(
        "commerce", "fake", lambda config: FakeCommerceProvider(name="fake")
    )
    factory.register(
        "notification",
        "fake",
        lambda config: FakeNotificationProvider(name="fake"),
    )
    factory.register(
        "storage", "fake", lambda config: FakeStorageProvider(name="fake")
    )
    return factory


def provider_selection(config: ForgeConfig) -> dict[str, str]:
    """Config's selected provider name per port."""

    return {
        port: getattr(config, f"provider_{port}")
        for port in PORTS
    }


def providers_from_config(
    config: ForgeConfig,
    *,
    factory: ProviderFactory | None = None,
) -> ProviderRegistry:
    """Composition-root selection: config chooses one builder per port.

    Fail-closed: an unknown/misspelled provider name raises
    ProviderConfigurationError instead of silently substituting a fake.
    The returned registry is frozen (composition is closed after wiring).
    """

    factory = factory if factory is not None else default_provider_factory()
    selection = provider_selection(config)
    registry = ProviderRegistry()
    for port, name in selection.items():
        registry.register(port, name, factory.build(port, name, config))
    registry.freeze()
    return registry
