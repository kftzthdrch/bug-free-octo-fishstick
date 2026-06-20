"""ODIS SOAP/WebService adapter.

This module is intentionally the only place that imports zeep. The core and
application layers remain independent from SOAP and ODIS implementation details.
"""

from __future__ import annotations

from typing import Any, Iterable

from zeep import Client
from zeep.exceptions import Fault, TransportError

from core.requests import ensure_supported_request


class OdisSoapError(RuntimeError):
    """Raised when ODIS SOAP interaction fails."""


class OdisSoapTransport:
    CONNECT_ALIASES = (
        "ConnectToEcuAndOpenConnection",
        "connectToEcuAndOpenConnection",
        "OpenConnection",
        "openConnection",
        "ConnectToEcu",
        "connectToEcu",
    )

    SEND_PHYSICAL_ALIASES = (
        "SendRawService",
        "sendRawService",
        "SendRawUds",
        "sendRawUds",
        "ExecuteRawService",
        "executeRawService",
    )

    SEND_FUNCTIONAL_ALIASES = (
        "SendRawServiceFunctional",
        "sendRawServiceFunctional",
        "SendFunctionalRawService",
        "sendFunctionalRawService",
    )

    CLOSE_ALIASES = (
        "CloseConnection",
        "closeConnection",
        "CloseEcuConnection",
        "closeEcuConnection",
        "DisconnectFromEcu",
        "disconnectFromEcu",
    )

    def __init__(self, wsdl_url: str, debug: bool = False):
        self.wsdl_url = wsdl_url
        self.debug = debug
        self.client = Client(wsdl_url)
        self._operations = self._collect_operations()

    def _collect_operations(self) -> dict[str, Any]:
        operations: dict[str, Any] = {}
        for service in self.client.wsdl.services.values():
            for port in service.ports.values():
                for name, operation in port.binding._operations.items():
                    operations[name] = operation
        return operations

    def list_operations(self) -> list[str]:
        return sorted(self._operations)

    def operation_signature(self, name: str) -> str:
        return self._operations[name].input.signature()

    def _resolve_operation(self, aliases: Iterable[str]) -> str:
        for name in aliases:
            if name in self._operations:
                return name
        raise OdisSoapError(
            f"No matching ODIS SOAP operation found for aliases: {list(aliases)}. "
            f"Available operations: {', '.join(self.list_operations())}"
        )

    def _call(self, operation_name: str, *args: Any, **kwargs: Any) -> Any:
        if self.debug:
            print(f"[ODIS SOAP] {operation_name} args={args!r} kwargs={kwargs!r}")
        try:
            return getattr(self.client.service, operation_name)(*args, **kwargs)
        except Fault as exc:
            raise OdisSoapError(f"SOAP fault in {operation_name}: {exc}") from exc
        except TransportError as exc:
            raise OdisSoapError(f"SOAP transport error in {operation_name}: {exc}") from exc

    def _try_patterns(self, operation_name: str, patterns: list[tuple[tuple[Any, ...], dict[str, Any]]]) -> Any:
        errors: list[str] = []
        for args, kwargs in patterns:
            try:
                return self._call(operation_name, *args, **kwargs)
            except Exception as exc:
                errors.append(f"args={args!r} kwargs={kwargs!r} -> {type(exc).__name__}: {exc}")

        signature = self.operation_signature(operation_name)
        joined_errors = "\n".join(errors)
        raise OdisSoapError(
            f"Could not call ODIS SOAP operation {operation_name}.\n"
            f"WSDL signature: {signature}\n"
            f"Tried patterns:\n{joined_errors}"
        )

    def connect_to_ecu(self, ecu_identifier: str) -> Any:
        operation_name = self._resolve_operation(self.CONNECT_ALIASES)
        patterns = [
            ((), {"ecu": ecu_identifier}),
            ((), {"ecuName": ecu_identifier}),
            ((), {"ecuShortName": ecu_identifier}),
            ((), {"logicalLinkName": ecu_identifier}),
            ((), {"diagnosticAddress": ecu_identifier}),
            ((), {"diagAddress": ecu_identifier}),
            ((), {"address": ecu_identifier}),
            ((ecu_identifier,), {}),
            ((), {}),
        ]
        return self._try_patterns(operation_name, patterns)

    def send_raw_service(self, request_hex: str, ecu_identifier: str, connection: Any | None = None, functional: bool = False) -> Any:
        request_hex = ensure_supported_request(request_hex)
        aliases = self.SEND_FUNCTIONAL_ALIASES if functional else self.SEND_PHYSICAL_ALIASES
        operation_name = self._resolve_operation(aliases)

        patterns: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        if connection is not None:
            patterns.extend(
                [
                    ((), {"connection": connection, "request": request_hex}),
                    ((), {"connection": connection, "rawService": request_hex}),
                    ((), {"connectionId": connection, "request": request_hex}),
                    ((), {"connectionId": connection, "rawService": request_hex}),
                    ((), {"handle": connection, "request": request_hex}),
                    ((), {"handle": connection, "rawService": request_hex}),
                    ((connection, request_hex), {}),
                ]
            )

        patterns.extend(
            [
                ((), {"ecu": ecu_identifier, "request": request_hex}),
                ((), {"ecu": ecu_identifier, "rawService": request_hex}),
                ((), {"ecuName": ecu_identifier, "request": request_hex}),
                ((), {"ecuName": ecu_identifier, "rawService": request_hex}),
                ((), {"logicalLinkName": ecu_identifier, "request": request_hex}),
                ((), {"logicalLinkName": ecu_identifier, "rawService": request_hex}),
                ((), {"diagnosticAddress": ecu_identifier, "request": request_hex}),
                ((), {"diagnosticAddress": ecu_identifier, "rawService": request_hex}),
                ((), {"request": request_hex}),
                ((), {"rawService": request_hex}),
                ((), {"rawRequest": request_hex}),
                ((request_hex,), {}),
            ]
        )
        return self._try_patterns(operation_name, patterns)

    def close_connection(self, connection: Any | None) -> None:
        if connection is None:
            return
        try:
            operation_name = self._resolve_operation(self.CLOSE_ALIASES)
        except OdisSoapError:
            return

        patterns = [
            ((), {"connection": connection}),
            ((), {"connectionId": connection}),
            ((), {"handle": connection}),
            ((connection,), {}),
            ((), {}),
        ]
        try:
            self._try_patterns(operation_name, patterns)
        except OdisSoapError:
            if self.debug:
                print("[ODIS SOAP] Close operation failed; continuing.")
