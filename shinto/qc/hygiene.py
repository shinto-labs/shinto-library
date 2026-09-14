"""
QC hygiene helpers: whitespace, HTML, embedded images, ISO temporal.

Used by qc_runner kinds (detect-only). Cleanup (Phase B) can reuse the same
detectors later; this module does not mutate project data.
"""

from __future__ import annotations

import base64
import re
from datetime import datetime
from typing import Any, Iterator

# Well-formed HTML open/close/void tags: <tag ...> or </tag>
_HTML_TAG_RE = re.compile(
    r"</?\s*([A-Za-z][A-Za-z0-9:-]*)\b[^<>]*>",
    re.IGNORECASE,
)

_DATA_IMAGE_RE = re.compile(
    r"data:image\/[a-z0-9.+-]+;base64,([A-Za-z0-9+/=\s]+)",
    re.IGNORECASE,
)

_IMAGE_SIGNATURES: list[tuple[str, bytes]] = [
    ("png", b"\x89PNG\r\n\x1a\n"),
    ("jpeg", b"\xff\xd8\xff"),
    ("gif", b"GIF8"),
    ("bmp", b"BM"),
    ("webp", b"RIFF"),  # refined below
]


def has_leading_or_trailing_whitespace(value: str) -> bool:
    return value != value.strip()


def find_html_tags(value: str) -> list[str]:
    """Return lowercased tag names for well-formed tags in value."""
    return [m.group(1).lower() for m in _HTML_TAG_RE.finditer(value or "")]


def html_violations(
    value: str,
    *,
    field_type: str | None,
    string_forbid_html: bool,
    allowed_tags: set[str],
    forbidden_tags: set[str],
) -> list[str]:
    """
    Return human-readable violation messages (empty if ok).

    - string / unknown: any HTML tag fails when string_forbid_html
    - text: forbidden tags always fail; other tags must be in allowlist
    """
    tags = find_html_tags(value)
    if not tags:
        return []

    messages: list[str] = []
    if field_type == "text":
        for tag in sorted(set(tags)):
            if tag in forbidden_tags:
                messages.append(f'Verboden HTML-tag "<{tag}>"')
            elif tag not in allowed_tags:
                messages.append(f'HTML-tag "<{tag}>" niet in allowlist')
        return messages

    # string or untyped nested string
    if string_forbid_html:
        uniq = ", ".join(f"<{t}>" for t in sorted(set(tags)))
        messages.append(f"HTML-tags niet toegestaan in string: {uniq}")
    return messages


def _looks_like_webp(decoded: bytes) -> bool:
    return (
        len(decoded) >= 12
        and decoded.startswith(b"RIFF")
        and decoded[8:12] == b"WEBP"
    )


def detect_image_type(decoded: bytes) -> str | None:
    if not decoded:
        return None
    if _looks_like_webp(decoded):
        return "webp"
    for name, sig in _IMAGE_SIGNATURES:
        if name == "webp":
            continue
        if decoded.startswith(sig):
            return name
    return None


def find_embedded_images(
    value: str,
    *,
    min_length: int = 256,
) -> list[dict[str, Any]]:
    """
    Detect data-URL images and long Base64 runs that decode to image magic bytes.
    """
    if not isinstance(value, str) or not value:
        return []

    results: list[dict[str, Any]] = []

    for match in _DATA_IMAGE_RE.finditer(value):
        payload = re.sub(r"\s+", "", match.group(1))
        entry = _try_decode_image(payload, index=match.start(), via="data_url")
        if entry:
            entry["match"] = match.group(0)
            entry["end"] = match.end()
            results.append(entry)

    # Standard Base64 runs (exclude regions already covered by data URLs)
    pattern = re.compile(rf"[A-Za-z0-9+/]{{{min_length},}}={{0,2}}")
    covered = [(m.start(), m.end()) for m in _DATA_IMAGE_RE.finditer(value)]

    def overlaps(start: int, end: int) -> bool:
        return any(start < c_end and end > c_start for c_start, c_end in covered)

    for match in pattern.finditer(value):
        candidate = match.group(0)
        if len(candidate) % 4 != 0:
            continue
        if overlaps(match.start(), match.end()):
            continue
        entry = _try_decode_image(candidate, index=match.start(), via="base64_run")
        if entry:
            entry["match"] = candidate
            entry["end"] = match.end()
            results.append(entry)

    return results


def _try_decode_image(
    candidate: str, *, index: int, via: str
) -> dict[str, Any] | None:
    try:
        decoded = base64.b64decode(candidate, validate=False)
    except Exception:
        return None
    if len(decoded) < 32:
        return None
    image_type = detect_image_type(decoded)
    if not image_type:
        return None
    return {
        "index": index,
        "via": via,
        "encodedLength": len(candidate),
        "decodedBytes": len(decoded),
        "imageType": image_type,
    }


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")
# No offsets: require trailing Z
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def is_iso_temporal(value: Any, field_type: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        if field_type == "date":
            if not _DATE_RE.match(value):
                return False
            datetime.strptime(value, "%Y-%m-%d")
            return True
        if field_type == "time":
            if not _TIME_RE.match(value):
                return False
            datetime.strptime(value, "%H:%M:%S")
            return True
        if field_type == "datetime":
            if not _DATETIME_RE.match(value):
                return False
            datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            return True
    except ValueError:
        return False
    return False


def default_matches_type(
    default: Any, field_type: str | None, field: dict, settings: dict
) -> bool:
    if field_type is None:
        return False
    string_like = set(settings.get("stringLikeTypes") or ["string", "text"])
    if field_type in string_like:
        return isinstance(default, str)
    if field_type == "integer":
        return isinstance(default, int) and not isinstance(default, bool)
    if field_type in {"decimal", "number"}:
        return isinstance(default, (int, float)) and not isinstance(default, bool)
    if field_type == "boolean":
        return isinstance(default, bool)
    if field_type == "uuid":
        return isinstance(default, str)
    if field_type == "object":
        return isinstance(default, dict)
    if field_type == "array":
        return isinstance(default, list)
    if field_type in {"date", "time", "datetime"}:
        return isinstance(default, str) and is_iso_temporal(default, field_type)
    if field_type == "categorical":
        if not isinstance(default, (str, int, float)) or isinstance(default, bool):
            return False
        allowed = {
            str(entry.get("value"))
            for entry in (field.get("values") or [])
            if isinstance(entry, dict) and entry.get("value") is not None
        }
        return not allowed or str(default) in allowed
    if field_type == "multi_categorical":
        if not isinstance(default, list):
            return False
        allowed = {
            str(entry.get("value"))
            for entry in (field.get("values") or [])
            if isinstance(entry, dict) and entry.get("value") is not None
        }
        return all(str(item) in allowed for item in default) if allowed else True
    return True


def iter_string_leaves(
    value: Any,
    path: str = "",
    *,
    skip_keys: set[str] | None = None,
    depth: int = 0,
) -> Iterator[tuple[str, str]]:
    """Yield (path, string) for all string leaves under value."""
    if depth > 32:
        return
    skip = skip_keys or {"qc"}
    if isinstance(value, str):
        yield path or "(root)", value
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if key in skip:
                continue
            child_path = f"{path}.{key}" if path else str(key)
            yield from iter_string_leaves(
                child, child_path, skip_keys=skip, depth=depth + 1
            )
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield from iter_string_leaves(
                child, child_path, skip_keys=skip, depth=depth + 1
            )


def path_field_name(path: str) -> str | None:
    """Last segment of a path, without list indices."""
    if not path or path == "(root)":
        return None
    segment = path.split(".")[-1]
    segment = re.sub(r"\[\d+\]$", "", segment)
    return segment or None


def build_field_type_map(taxonomy: dict | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for field in (taxonomy or {}).get("fields") or []:
        if isinstance(field, dict) and field.get("field") and field.get("type"):
            out[str(field["field"])] = str(field["type"])
    return out
