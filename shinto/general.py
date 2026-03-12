"""Provides functions to handle configuration settings for the application."""

import mimetypes
import zlib
from pathlib import Path

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
