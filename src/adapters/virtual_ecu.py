"""In-process virtual ECU transport for local pipeline testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.hexcodec import bytes_to_hex, normalize_hex
from core.requests import ensure_supported_request


DEFAULT_DID_PAYLOADS: dict[str, bytes] = {
    "F187": b"5Q0907530AF",
    "F188": b"0001",
    "F189": b"0123",
    "F18A": b"OpenAI",
    "F18B": b"20260620",
    "F18C": b"VECU000001",
    "F190": b"VIRTUALVIN0000001",
    "F191": b"HW-1.0",
    "F192": b"SUP-HW-1.0",
    "F193": b"A",
    "F194": b"SUP-SW-1.0",
    "F195": b"1.0.0",
    "F197": b"Virtual ECU",
}


@dataclass
class VirtualEcuConnection:
    ecu_identifier: str
    session: str = "default"
    tester_present_count: int = 0
    reset_count: int = 0
    last_reset_type: str | None = None


class VirtualEcuTransport:
    """DiagnosticTransport implementation that emulates a small ECU.

    The simulator intentionally supports only the services this project allows:
    DiagnosticSessionControl, ECUReset, TesterPresent, and ReadDataByIdentifier.
    """

    def __init__(
        self,
        did_payloads: dict[str, bytes | str] | None = None,
        *,
        strict_ecu_identifier: str | None = None,
    ):
        self.strict_ecu_identifier = strict_ecu_identifier
        configured = did_payloads or DEFAULT_DID_PAYLOADS
        self.did_payloads = {
            normalize_hex(did): payload.encode("ascii") if isinstance(payload, str) else payload
            for did, payload in configured.items()
        }
        self.connections: list[VirtualEcuConnection] = []

    def list_operations(self) -> list[str]:
        return ["connect_to_ecu", "send_raw_service", "close_connection"]

    def operation_signature(self, name: str) -> str:
        signatures = {
            "connect_to_ecu": "connect_to_ecu(ecu_identifier: str) -> VirtualEcuConnection",
            "send_raw_service": "send_raw_service(request_hex: str, ecu_identifier: str, connection=None, functional=False) -> str",
            "close_connection": "close_connection(connection) -> None",
        }
        return signatures.get(name, "unknown virtual ECU operation")

    def connect_to_ecu(self, ecu_identifier: str) -> VirtualEcuConnection:
        if self.strict_ecu_identifier is not None and ecu_identifier != self.strict_ecu_identifier:
            raise ValueError(
                f"Virtual ECU {self.strict_ecu_identifier!r} does not accept identifier {ecu_identifier!r}."
            )
        connection = VirtualEcuConnection(ecu_identifier=ecu_identifier)
        self.connections.append(connection)
        return connection

    def send_raw_service(
        self,
        request_hex: str,
        ecu_identifier: str,
        connection: Any | None = None,
        functional: bool = False,
    ) -> str:
        request_hex = ensure_supported_request(request_hex)
        active_connection = connection if isinstance(connection, VirtualEcuConnection) else None

        if request_hex == "1001":
            if active_connection is not None:
                active_connection.session = "default"
            return "5001003201"

        if request_hex == "1003":
            if active_connection is not None:
                active_connection.session = "extended"
            return "5003003201"

        if request_hex.startswith("11"):
            reset_type = request_hex[2:4]
            if active_connection is not None:
                active_connection.reset_count += 1
                active_connection.last_reset_type = reset_type
                active_connection.session = "default"
            return "51" + reset_type

        if request_hex == "3E00":
            if active_connection is not None:
                active_connection.tester_present_count += 1
            return "7E00"

        if request_hex.startswith("22"):
            did = request_hex[2:6]
            payload = self.did_payloads.get(did)
            if payload is None:
                return "7F2231"
            return "62" + did + bytes_to_hex(payload)

        return f"7F{request_hex[:2]}11"

    def close_connection(self, connection: Any | None) -> None:
        return None
