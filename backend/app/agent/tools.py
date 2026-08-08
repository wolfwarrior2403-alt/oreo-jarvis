"""Tool registry for the reasoning agent (section 3.5).

Every tool is declared as a ToolSpec with `read_only` set explicitly.
- read_only=True tools execute immediately when the agent calls them
  (looking something up changes nothing, so there's nothing to gate).
- read_only=False tools NEVER run inline. The agent layer (app/agent/
  reasoning.py) intercepts any call to a non-read-only tool and turns it
  into a PendingAction instead of running `executor` — the executor only
  ever runs from app/agent/actions.py's execute_action(), after explicit
  approval. This is the enforcement point for the confirmation gate
  described in section 3.5 / 6; do not call `.executor` directly from
  anywhere except execute_action().

Custom, team-defined tools can be added at runtime with `register_tool`,
e.g. from a deployment-specific plugin module loaded at startup.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# All file tool operations are sandboxed under this directory — the agent
# can never read/write arbitrary paths on the host.
SANDBOX_ROOT = Path(os.environ.get("OREO_FILE_SANDBOX", "./data/files")).resolve()
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)


@dataclass
class ToolSpec:
    name: str
    description: str
    read_only: bool
    executor: Callable[..., str]
    args_schema: dict[str, str] = field(default_factory=dict)  # arg name -> description


_REGISTRY: dict[str, ToolSpec] = {}


def register_tool(spec: ToolSpec) -> None:
    if spec.name in _REGISTRY:
        logger.warning("tool_overwritten", tool=spec.name)
    _REGISTRY[spec.name] = spec


def get_tool(name: str) -> ToolSpec | None:
    return _REGISTRY.get(name)


def list_tools() -> list[ToolSpec]:
    return list(_REGISTRY.values())


# --- Web search (read-only) ---
def _web_search(query: str, max_results: int = 5) -> str:
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return "No results found."
    lines = [f"- {r.get('title')}: {r.get('href')} — {r.get('body', '')[:200]}" for r in results]
    return "\n".join(lines)


register_tool(
    ToolSpec(
        name="web_search",
        description="Search the web for current information (news, facts, prices, etc).",
        read_only=True,
        executor=_web_search,
        args_schema={"query": "search query", "max_results": "max number of results (default 5)"},
    )
)


# --- Calendar (stub) ---
# In-memory for now — a real deployment would swap this for a Google/Outlook
# calendar API client behind the same ToolSpec interface.
_CALENDAR_EVENTS: list[dict[str, Any]] = []


def _calendar_list(date: str | None = None) -> str:
    events = _CALENDAR_EVENTS
    if date:
        events = [e for e in events if e["date"] == date]
    if not events:
        return "No events found."
    return "\n".join(f"- {e['date']} {e['time']}: {e['title']}" for e in events)


def _calendar_create(title: str, date: str, time: str) -> str:
    _CALENDAR_EVENTS.append({"title": title, "date": date, "time": time})
    return f"Created event '{title}' on {date} at {time}."


register_tool(
    ToolSpec(
        name="calendar_list",
        description="List calendar events, optionally filtered by date (YYYY-MM-DD).",
        read_only=True,
        executor=_calendar_list,
        args_schema={"date": "optional YYYY-MM-DD filter"},
    )
)
register_tool(
    ToolSpec(
        name="calendar_create_event",
        description="Create a new calendar event. Requires confirmation.",
        read_only=False,
        executor=_calendar_create,
        args_schema={"title": "event title", "date": "YYYY-MM-DD", "time": "HH:MM"},
    )
)


# --- File read/write (sandboxed) ---
def _resolve_sandbox_path(relative_path: str) -> Path:
    candidate = (SANDBOX_ROOT / relative_path).resolve()
    if SANDBOX_ROOT not in candidate.parents and candidate != SANDBOX_ROOT:
        raise ValueError("Path escapes the file sandbox.")
    return candidate


def _file_read(path: str) -> str:
    target = _resolve_sandbox_path(path)
    if not target.exists():
        return f"File not found: {path}"
    return target.read_text(encoding="utf-8", errors="replace")[:5000]


def _file_write(path: str, content: str) -> str:
    target = _resolve_sandbox_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {path}."


register_tool(
    ToolSpec(
        name="file_read",
        description="Read a text file from the sandboxed Oreo data directory.",
        read_only=True,
        executor=_file_read,
        args_schema={"path": "relative path within the sandbox"},
    )
)
register_tool(
    ToolSpec(
        name="file_write",
        description="Write/overwrite a text file in the sandboxed Oreo data directory. Requires confirmation.",
        read_only=False,
        executor=_file_write,
        args_schema={"path": "relative path within the sandbox", "content": "file contents"},
    )
)
