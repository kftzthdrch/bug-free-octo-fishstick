"""UDS response extraction and parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .hexcodec import bytes_to_hex, hex_to_bytes, normalize_hex, safe_ascii
from .nrc import nrc_text

NEGATIVE_RESPONSE_SID = 0x7F


@dataclass(frozen=True)
class UdsResponse:
    request_hex: str
    response_hex: str
    positive: bool
    negative: bool
    service_id: int | None
    did: str | None
    payload_hex: str
    ascii_payload: str
    display_value: str
    note: str


def extract_hex_response(response_any: Any) -> str:
    if response_any is None:
        return ""

    if isinstance(response_any, bytes):
        return bytes_to_hex(response_any)

    if isinstance(response_any, str):
        candidate = response_any.strip()
        try:
            return normalize_hex(candidate)
        except ValueError:
            tokens = []
            for token in candidate.replace("\n", " ").replace("\t", " ").split(" "):
                cleaned = token.strip().replace("0x", "").replace("0X", "")
                if len(cleaned) == 2:
                    try:
                        int(cleaned, 16)
                        tokens.append(cleaned)
                    except ValueError:
                        continue
            if tokens:
                return normalize_hex("".join(tokens))
            raise

    if isinstance(response_any, dict):
        for key in ("response", "responseData", "rawResponse", "rawServiceResponse", "data", "value", "result", "return"):
            if key in response_any:
                try:
                    return extract_hex_response(response_any[key])
                except ValueError:
                    continue

    if isinstance(response_any, (list, tuple)):
        for item in response_any:
            try:
                return extract_hex_response(item)
            except ValueError:
                continue

    for key in ("response", "responseData", "rawResponse", "rawServiceResponse", "data", "value", "result"):
        if hasattr(response_any, key):
            try:
                return extract_hex_response(getattr(response_any, key))
            except ValueError:
                continue

    return extract_hex_response(str(response_any))


def parse_uds_response(request_hex: str, response_any: Any) -> UdsResponse:
    request_hex = normalize_hex(request_hex)
    response_hex = extract_hex_response(response_any)
    request_bytes = hex_to_bytes(request_hex)
    response_bytes = hex_to_bytes(response_hex) if response_hex else b""

    service_id = request_bytes[0] if request_bytes else None
    did = request_hex[2:6] if service_id == 0x22 and len(request_bytes) >= 3 else None

    if not response_bytes:
        return UdsResponse(request_hex, "", False, False, service_id, did, "", "", "", "Empty response.")

    if response_bytes[0] == NEGATIVE_RESPONSE_SID:
        rejected_sid = response_bytes[1] if len(response_bytes) > 1 else None
        nrc = response_bytes[2] if len(response_bytes) > 2 else None
        note = "Malformed negative response."
        if rejected_sid is not None and nrc is not None:
            note = f"Negative response. Rejected SID=0x{rejected_sid:02X}, NRC=0x{nrc:02X} {nrc_text(nrc)}."
        return UdsResponse(request_hex, response_hex, False, True, service_id, did, "", "", "", note)

    expected_positive_sid = service_id + 0x40 if service_id is not None else None
    positive = expected_positive_sid is not None and response_bytes[0] == expected_positive_sid
    payload = b""
    note = "Positive response." if positive else "Unexpected response."

    if service_id == 0x22 and positive:
        if len(response_bytes) >= 3:
            response_did = f"{response_bytes[1]:02X}{response_bytes[2]:02X}"
            payload = response_bytes[3:]
            if did and response_did != did:
                note = f"Positive response but DID mismatch: requested {did}, got {response_did}."
        else:
            note = "Malformed positive ReadDataByIdentifier response."
    elif positive:
        payload = response_bytes[1:]

    ascii_payload = safe_ascii(payload)
    display_value = ascii_payload if positive and ascii_payload.strip(".") else bytes_to_hex(payload)

    return UdsResponse(
        request_hex=request_hex,
        response_hex=response_hex,
        positive=positive,
        negative=False,
        service_id=service_id,
        did=did,
        payload_hex=bytes_to_hex(payload),
        ascii_payload=ascii_payload,
        display_value=display_value,
        note=note,
    )
