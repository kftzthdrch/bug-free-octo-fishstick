"""Transport boundaries for diagnostic communication."""

from __future__ import annotations

from typing import Any, Protocol


class DiagnosticTransport(Protocol):
    """Minimal interface required by the application pipeline."""

    def list_operations(self) -> list[str]:
        """Return available transport operations."""

    def operation_signature(self, name: str) -> str:
        """Return a human-readable operation signature."""

    def connect_to_ecu(self, ecu_identifier: str) -> Any:
        """Open or resolve a connection to one ECU/logical link."""

    def send_raw_service(self, request_hex: str, ecu_identifier: str, connection: Any | None = None, functional: bool = False) -> Any:
        """Send one validated raw UDS request and return transport-specific response data."""

    def close_connection(self, connection: Any | None) -> None:
        """Close the ECU connection if supported."""
