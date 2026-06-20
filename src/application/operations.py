"""Operation listing use case."""

from __future__ import annotations

from adapters.protocols import DiagnosticTransport


def render_operations(transport: DiagnosticTransport) -> str:
    lines = ["Available SOAP operations:"]
    for name in transport.list_operations():
        lines.append(f"  - {name}: {transport.operation_signature(name)}")
    return "\n".join(lines)
