"""Provides functions to handle configuration settings for the application."""

import mimetypes
import zlib
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Union, Optional

try:
    from dateutil.parser import parse as parse_datetime
except ImportError:
    parse_datetime = None

CHUNK_SIZE = 65536  # Default chunk size for CRC32 calculation

def calculate_crc32_for_file(filename: Path, chunk_size: int = CHUNK_SIZE) -> int:
    """Calculate the CRC32 checksum for a file."""
    crc = 0
    with filename.open("rb") as f:
        while chunk := f.read(chunk_size):
            crc = zlib.crc32(chunk, crc)
    return crc & 0xffffffff

def get_mimetype_for_file(file_path: str) -> str:
    """Get MIME type from file path using built-in mimetypes module."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"

def normalize_timestamp(timestamp: Optional[Union[datetime, str]]) -> Optional[datetime]:
    """
    Normalize a timestamp argument to a timezone-aware datetime object.
    Accepts a datetime, ISO 8601 string, or None. If no timezone is present, assumes UTC.
    Returns None if input is None.
    Raises ValueError for invalid input.
    """
    if timestamp is None:
        return None
    if isinstance(timestamp, str):
        if parse_datetime is not None:
            dt = parse_datetime(timestamp)
        else:
            dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    elif isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp
    else:
        raise ValueError("timestamp must be a datetime, ISO 8601 string, or None")

def compare_json(json1: dict, json2: dict) -> bool:
    """Compare two JSON objects for equality, ignoring key order."""
    return json.dumps(json1, sort_keys=True) == json.dumps(json2, sort_keys=True)