"""Construction and safety validation of supported UDS requests."""

from __future__ import annotations

from dataclasses import dataclass

from .hexcodec import normalize_hex

ALLOWED_SERVICE_IDS = {0x10, 0x11, 0x22, 0x3E}
BLOCKED_SERVICE_IDS = {0x27, 0x2E, 0x31, 0x34, 0x35, 0x36, 0x37, 0x3D}
ECU_RESET_TYPES = {
    "hard": "01",
    "key-off-on": "02",
    "soft": "03",
    "enable-rapid-power-shutdown": "04",
    "disable-rapid-power-shutdown": "05",
}


@dataclass(frozen=True)
class UdsRequest:
    raw_hex: str
    label: str

    @property
    def service_id(self) -> int:
        return int(self.raw_hex[:2], 16)


def ensure_supported_request(raw_hex: str) -> str:
    normalized = normalize_hex(raw_hex)
    service_id = int(normalized[:2], 16)

    if service_id in BLOCKED_SERVICE_IDS:
        raise ValueError(f"Blocked unsafe UDS service: 0x{service_id:02X}")

    if service_id not in ALLOWED_SERVICE_IDS:
        raise ValueError(f"Unsupported UDS service in this diagnostic client: 0x{service_id:02X}")

    if service_id == 0x11 and normalized not in {"1101", "1102", "1103", "1104", "1105"}:
        raise ValueError(
            "Only ECUReset 1101 hard, 1102 key-off-on, 1103 soft, "
            "1104 enable rapid power shutdown, and 1105 disable rapid power shutdown are allowed."
        )

    if service_id == 0x22 and len(normalized) != 6:
        raise ValueError("ReadDataByIdentifier requests must be exactly 3 bytes: 22DIDHIDIDLO.")

    if service_id == 0x3E and normalized != "3E00":
        raise ValueError("Only TesterPresent 3E00 is allowed.")

    if service_id == 0x10 and normalized not in {"1001", "1003"}:
        raise ValueError("Only DiagnosticSessionControl 1001 and 1003 are allowed.")

    return normalized


def ensure_read_only_request(raw_hex: str) -> str:
    return ensure_supported_request(raw_hex)


def read_did_request(did_hex: str) -> UdsRequest:
    did = normalize_hex(did_hex)
    if len(did) != 4:
        raise ValueError(f"DID must be exactly two bytes, got: {did_hex!r}")
    return UdsRequest(raw_hex=ensure_supported_request("22" + did), label=f"Read DID {did}")


def ecu_reset_request(reset_type: str) -> UdsRequest:
    normalized_type = reset_type.strip().lower()
    subfunction = ECU_RESET_TYPES.get(normalized_type)
    if subfunction is None:
        supported = ", ".join(sorted(ECU_RESET_TYPES))
        raise ValueError(f"Unsupported ECU reset type {reset_type!r}. Supported values: {supported}.")
    return UdsRequest(raw_hex=ensure_supported_request("11" + subfunction), label=f"ECU reset {normalized_type}")


def tester_present_request() -> UdsRequest:
    return UdsRequest(raw_hex=ensure_supported_request("3E00"), label="TesterPresent")


def default_session_request() -> UdsRequest:
    return UdsRequest(raw_hex=ensure_supported_request("1001"), label="Default diagnostic session")


def extended_session_request() -> UdsRequest:
    return UdsRequest(raw_hex=ensure_supported_request("1003"), label="Extended diagnostic session")
