"""Application pipeline for ECU identification and reset operations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from adapters.protocols import DiagnosticTransport
from core.requests import (
    UdsRequest,
    ecu_reset_request,
    extended_session_request,
    read_did_request,
    tester_present_request,
)
from core.responses import UdsResponse, parse_uds_response


@dataclass(frozen=True)
class PipelineConfig:
    ecu_identifier: str
    dids: tuple[str, ...]
    use_extended_session: bool = False
    use_tester_present: bool = False
    functional: bool = False
    delay_seconds: float = 0.05


@dataclass(frozen=True)
class PipelineResult:
    ecu_identifier: str
    responses: tuple[UdsResponse, ...]


@dataclass(frozen=True)
class EcuResetConfig:
    ecu_identifier: str
    reset_type: str
    use_extended_session: bool = False
    use_tester_present: bool = False
    functional: bool = False
    delay_seconds: float = 0.05


def build_identification_requests(config: PipelineConfig) -> list[UdsRequest]:
    requests: list[UdsRequest] = []
    if config.use_extended_session:
        requests.append(extended_session_request())
    if config.use_tester_present:
        requests.append(tester_present_request())
    requests.extend(read_did_request(did) for did in config.dids)
    return requests


def execute_identification_pipeline(transport: DiagnosticTransport, config: PipelineConfig) -> PipelineResult:
    connection: Any | None = None
    responses: list[UdsResponse] = []

    try:
        connection = transport.connect_to_ecu(config.ecu_identifier)
        for request in build_identification_requests(config):
            raw_response = transport.send_raw_service(
                request_hex=request.raw_hex,
                ecu_identifier=config.ecu_identifier,
                connection=connection,
                functional=config.functional,
            )
            responses.append(parse_uds_response(request.raw_hex, raw_response))
            if config.delay_seconds > 0:
                time.sleep(config.delay_seconds)
        return PipelineResult(ecu_identifier=config.ecu_identifier, responses=tuple(responses))
    finally:
        transport.close_connection(connection)


def build_ecu_reset_requests(config: EcuResetConfig) -> list[UdsRequest]:
    requests: list[UdsRequest] = []
    if config.use_extended_session:
        requests.append(extended_session_request())
    if config.use_tester_present:
        requests.append(tester_present_request())
    requests.append(ecu_reset_request(config.reset_type))
    return requests


def execute_ecu_reset(transport: DiagnosticTransport, config: EcuResetConfig) -> PipelineResult:
    connection: Any | None = None
    responses: list[UdsResponse] = []

    try:
        connection = transport.connect_to_ecu(config.ecu_identifier)
        for request in build_ecu_reset_requests(config):
            raw_response = transport.send_raw_service(
                request_hex=request.raw_hex,
                ecu_identifier=config.ecu_identifier,
                connection=connection,
                functional=config.functional,
            )
            responses.append(parse_uds_response(request.raw_hex, raw_response))
            if config.delay_seconds > 0:
                time.sleep(config.delay_seconds)
        return PipelineResult(ecu_identifier=config.ecu_identifier, responses=tuple(responses))
    finally:
        transport.close_connection(connection)
