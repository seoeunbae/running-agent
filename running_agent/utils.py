"""Immutable, section-based prompt builder for agent instruction composition."""

from __future__ import annotations

from collections import OrderedDict
from typing import Awaitable, Callable, Union

from google.adk.agents.readonly_context import ReadonlyContext

InstructionProvider = Union[
    Callable[[ReadonlyContext], str],
    Callable[[ReadonlyContext], Awaitable[str]],
]


class PromptBuilder:
    """Ordered, named sections assembled into a single prompt.

    Immutable: every mutation returns a new instance.
    Child agents call ``override()`` to replace or add sections by key.
    """

    __slots__ = ("_sections",)

    def __init__(self, sections: OrderedDict[str, str]) -> None:
        self._sections: OrderedDict[str, str] = OrderedDict(sections)

    @property
    def sections(self) -> OrderedDict[str, str]:
        return OrderedDict(self._sections)

    def build(self) -> str:
        return "\n\n".join(v for v in self._sections.values() if v)

    def static(self, *keys: str) -> str:
        return "\n\n".join(self._sections[k] for k in keys if k in self._sections)

    def dynamic(
        self, *, exclude: tuple[str, ...] = ()
    ) -> Callable[[ReadonlyContext], Awaitable[str]]:
        remaining = OrderedDict(
            (k, v) for k, v in self._sections.items() if k not in exclude and v
        )

        async def _provider(ctx: ReadonlyContext) -> str:
            return "\n\n".join(remaining.values())

        return _provider

    def override(self, **sections: str) -> PromptBuilder:
        merged = OrderedDict(self._sections)
        merged.update(sections)
        return PromptBuilder(merged)
