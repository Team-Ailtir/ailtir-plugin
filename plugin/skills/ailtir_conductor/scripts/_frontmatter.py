"""Minimal YAML frontmatter parser/serializer for Ailtir bid READMEs.

We only support the schema documented in `ailtir_conductor/SKILL.md` — do not
try to make this a general YAML library. Cowork has no outbound internet, so
we cannot rely on PyYAML being importable in every runtime.

Public API:
    parse(readme_text) -> (frontmatter_dict_or_None, body_text)
    serialize(frontmatter_dict) -> str   # full block including --- fences
    upsert(readme_text, frontmatter_dict) -> str  # replace or insert block
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse(readme_text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Return (parsed_frontmatter_or_None, body_after_frontmatter)."""
    m = FRONT_RE.match(readme_text)
    if not m:
        return None, readme_text
    body = readme_text[m.end():]
    try:
        fm = _parse_block(m.group(1))
    except Exception:
        return None, readme_text
    return fm, body


def _parse_block(text: str) -> Dict[str, Any]:
    """Parse the YAML-ish block. Supports scalars, inline flow mappings, and
    nested mappings/lists via indentation. Two-space indentation only."""
    lines = _pre_split(text)
    return _parse_mapping(lines, indent=0)


def _pre_split(text: str) -> List[Tuple[int, str]]:
    """Split into (indent, content) tuples, dropping blank/comment-only lines."""
    out: List[Tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = raw.rstrip()
        if not stripped.strip():
            continue
        # Skip pure comment lines
        if stripped.lstrip().startswith("#"):
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        content = stripped[indent:]
        # Strip trailing inline comments only when they are prefixed with " #"
        content = _strip_inline_comment(content)
        out.append((indent, content))
    return out


def _strip_inline_comment(s: str) -> str:
    in_single = False
    in_double = False
    depth_curly = 0
    depth_square = 0
    for i, ch in enumerate(s):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if ch == "{":
                depth_curly += 1
            elif ch == "}":
                depth_curly -= 1
            elif ch == "[":
                depth_square += 1
            elif ch == "]":
                depth_square -= 1
            elif ch == "#" and depth_curly == 0 and depth_square == 0:
                if i == 0 or s[i - 1] == " ":
                    return s[:i].rstrip()
    return s.rstrip()


def _parse_mapping(lines: List[Tuple[int, str]], indent: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    i = 0
    while i < len(lines):
        ind, content = lines[i]
        if ind < indent:
            break
        if ind > indent:
            i += 1
            continue
        if content.startswith("- "):
            # A mapping shouldn't start with a list item
            i += 1
            continue
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest == "" or rest is None:
            # Nested block (mapping or list)
            child_lines = _child_slice(lines, i + 1, indent)
            if not child_lines:
                result[key] = None
            else:
                child_indent = child_lines[0][0]
                if child_lines[0][1].startswith("- "):
                    result[key] = _parse_list(child_lines, child_indent)
                else:
                    result[key] = _parse_mapping(child_lines, child_indent)
            i += 1 + len(child_lines)
        else:
            result[key] = _parse_scalar_or_flow(rest)
            i += 1
    return result


def _parse_list(lines: List[Tuple[int, str]], indent: int) -> List[Any]:
    result: List[Any] = []
    i = 0
    while i < len(lines):
        ind, content = lines[i]
        if ind < indent:
            break
        if ind > indent:
            i += 1
            continue
        if not content.startswith("- "):
            i += 1
            continue
        item = content[2:].strip()
        if item == "":
            child_lines = _child_slice(lines, i + 1, indent)
            child_indent = child_lines[0][0] if child_lines else indent + 2
            result.append(_parse_mapping(child_lines, child_indent))
            i += 1 + len(child_lines)
        else:
            result.append(_parse_scalar_or_flow(item))
            i += 1
    return result


def _child_slice(lines: List[Tuple[int, str]], start: int, parent_indent: int) -> List[Tuple[int, str]]:
    out = []
    for j in range(start, len(lines)):
        ind, _ = lines[j]
        if ind <= parent_indent:
            break
        out.append(lines[j])
    return out


def _parse_scalar_or_flow(s: str) -> Any:
    s = s.strip()
    if s == "":
        return None
    if s == "[]":
        return []
    if s == "{}":
        return {}
    if s.startswith("{") and s.endswith("}"):
        return _parse_flow_mapping(s[1:-1])
    if s.startswith("[") and s.endswith("]"):
        return _parse_flow_list(s[1:-1])
    return _parse_scalar(s)


def _parse_scalar(s: str) -> Any:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~", ""):
        return None
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def _split_flow(s: str) -> List[str]:
    parts: List[str] = []
    buf: List[str] = []
    depth_curly = 0
    depth_square = 0
    in_single = False
    in_double = False
    for ch in s:
        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
        elif ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
        elif not in_single and not in_double:
            if ch == "{":
                depth_curly += 1
                buf.append(ch)
            elif ch == "}":
                depth_curly -= 1
                buf.append(ch)
            elif ch == "[":
                depth_square += 1
                buf.append(ch)
            elif ch == "]":
                depth_square -= 1
                buf.append(ch)
            elif ch == "," and depth_curly == 0 and depth_square == 0:
                parts.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def _parse_flow_mapping(s: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for part in _split_flow(s):
        k, _, v = part.partition(":")
        out[k.strip()] = _parse_scalar_or_flow(v.strip())
    return out


def _parse_flow_list(s: str) -> List[Any]:
    return [_parse_scalar_or_flow(p) for p in _split_flow(s)]


# ── Serialization ────────────────────────────────────────────────────────────

_KEY_ORDER = [
    "schema_version",
    "bid_id",
    "project_name",
    "client",
    "phase",
    "status",
    "next_action",
    "completed",
    "blockers",
    "key_dates",
    "auto_drive",
]


def serialize(fm: Dict[str, Any]) -> str:
    """Emit a full frontmatter block including the --- fences."""
    lines = ["---"]
    for key in _KEY_ORDER:
        if key not in fm:
            continue
        lines.extend(_emit(key, fm[key], indent=0))
    for key in fm:
        if key in _KEY_ORDER:
            continue
        lines.extend(_emit(key, fm[key], indent=0))
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _emit(key: str, value: Any, indent: int) -> List[str]:
    pad = " " * indent
    if value is None:
        return [f"{pad}{key}:"]
    if isinstance(value, dict):
        if not value:
            return [f"{pad}{key}: {{}}"]
        out = [f"{pad}{key}:"]
        for k, v in value.items():
            out.extend(_emit(k, v, indent + 2))
        return out
    if isinstance(value, list):
        if not value:
            return [f"{pad}{key}: []"]
        out = [f"{pad}{key}:"]
        for item in value:
            if isinstance(item, dict):
                # Prefer flow mapping for small dicts (fits on one line)
                out.append(f"{pad}  - {_emit_flow(item)}")
            else:
                out.append(f"{pad}  - {_emit_scalar(item)}")
        return out
    return [f"{pad}{key}: {_emit_scalar(value)}"]


def _emit_scalar(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or any(c in s for c in ":#[]{}") or s.strip() != s:
        return f'"{s}"'
    return s


def _emit_flow(d: Dict[str, Any]) -> str:
    parts = []
    for k, v in d.items():
        if isinstance(v, dict):
            parts.append(f"{k}: {_emit_flow(v)}")
        elif isinstance(v, list):
            inner = ", ".join(
                _emit_flow(x) if isinstance(x, dict) else _emit_scalar(x) for x in v
            )
            parts.append(f"{k}: [{inner}]")
        else:
            parts.append(f"{k}: {_emit_scalar(v)}")
    return "{" + ", ".join(parts) + "}"


def upsert(readme_text: str, fm: Dict[str, Any]) -> str:
    """Replace an existing frontmatter block or insert one at the top."""
    existing, body = parse(readme_text)
    return serialize(fm) + body
