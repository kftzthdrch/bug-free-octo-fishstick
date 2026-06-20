"""Hex encoding and decoding helpers for UDS payloads."""

from __future__ import annotations


def normalize_hex(value: str) -> str:
    """Return uppercase compact hex without separators.

    Raises:
        ValueError: if the value is empty, has odd length, or is not hex.
    """

    cleaned = (
        value.replace("0x", "")
        .replace("0X", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace(":", "")
        .upper()
    )

    if not cleaned:
        raise ValueError("Hex value must not be empty.")

    if len(cleaned) % 2 != 0:
        raise ValueError(f"Hex value must contain full bytes: {value!r}")

    try:
        bytes.fromhex(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid hex value: {value!r}") from exc

    return cleaned


def hex_to_bytes(value: str) -> bytes:
    """Convert human-entered hex into bytes."""

    return bytes.fromhex(normalize_hex(value))


def bytes_to_hex(value: bytes) -> str:
    """Convert bytes into uppercase compact hex."""

    return value.hex().upper()


def safe_ascii(value: bytes) -> str:
    """Render printable ASCII and replace binary bytes with dots."""

    return "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in value).strip()
