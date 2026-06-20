from dataclasses import dataclass
from typing import Any

from application.pipeline import PipelineConfig, execute_identification_pipeline


@dataclass
class FakeTransport:
    sent: list[str]

    def list_operations(self):
        return []

    def operation_signature(self, name: str):
        return ""

    def connect_to_ecu(self, ecu_identifier: str) -> Any:
        return "connection-1"

    def send_raw_service(self, request_hex: str, ecu_identifier: str, connection: Any | None = None, functional: bool = False) -> Any:
        self.sent.append(request_hex)
        if request_hex == "3E00":
            return "7E00"
        if request_hex == "22F190":
            return "62F190575657"
        return "7F2231"

    def close_connection(self, connection: Any | None) -> None:
        self.sent.append("closed")


def test_pipeline_sequence():
    transport = FakeTransport(sent=[])
    result = execute_identification_pipeline(
        transport,
        PipelineConfig(ecu_identifier="01", dids=("F190",), use_tester_present=True, delay_seconds=0),
    )
    assert transport.sent == ["3E00", "22F190", "closed"]
    assert result.responses[-1].ascii_payload == "WVW"
