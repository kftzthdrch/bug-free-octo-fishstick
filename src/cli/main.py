"""Command-line interface for DiagBridge."""

from __future__ import annotations

import argparse
import sys

from adapters.protocols import DiagnosticTransport
from adapters.virtual_ecu import VirtualEcuTransport
from application.operations import render_operations
from application.pipeline import EcuResetConfig, PipelineConfig, execute_ecu_reset, execute_identification_pipeline
from application.reporting import render_json, render_table
from core.dids import default_dids
from core.hexcodec import normalize_hex
from core.requests import ECU_RESET_TYPES


def split_dids(values: list[str]) -> tuple[str, ...]:
    dids: list[str] = []
    for value in values:
        for part in value.split(","):
            cleaned = part.strip()
            if cleaned:
                did = normalize_hex(cleaned)
                if len(did) != 4:
                    raise ValueError(f"DID must be exactly two bytes: {cleaned!r}")
                dids.append(did)
    return tuple(dids)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diagbridge",
        description="Controlled diagnostic bridge for ODIS WebService and UDS ECU workflows.",
    )
    parser.add_argument(
        "--transport",
        choices=("odis", "virtual"),
        default="odis",
        help="Diagnostic transport backend. Use 'virtual' for local ECU simulation.",
    )
    parser.add_argument("--wsdl", default="http://127.0.0.1:8081/?wsdl", help="ODIS SOAP WSDL URL.")
    parser.add_argument("--debug", action="store_true", help="Print SOAP call attempts.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    ops = subparsers.add_parser("list-ops", help="List SOAP operations exposed by the ODIS WebService WSDL.")
    ops.set_defaults(command="list-ops")

    read = subparsers.add_parser("read-identification", help="Read ECU identification DIDs with UDS 0x22.")
    read.add_argument("--ecu", required=True, help="ECU short name, logical link name, or diagnostic address expected by ODIS.")
    read.add_argument("--did", action="append", default=[], help="DID to read, e.g. F190. Repeat or comma-separate.")
    read.add_argument("--extended-session", action="store_true", help="Send 10 03 before DID reads.")
    read.add_argument("--tester-present", action="store_true", help="Send 3E 00 before DID reads.")
    read.add_argument("--functional", action="store_true", help="Use functional raw service operation if available.")
    read.add_argument("--delay", type=float, default=0.05, help="Delay between requests in seconds.")
    read.add_argument("--json", action="store_true", help="Print JSON after the table.")
    read.set_defaults(command="read-identification")

    reset = subparsers.add_parser("reset-ecu", help="Send UDS ECUReset 0x11 to one ECU.")
    reset.add_argument("--ecu", required=True, help="ECU short name, logical link name, or diagnostic address expected by ODIS.")
    reset.add_argument(
        "--reset-type",
        choices=tuple(ECU_RESET_TYPES),
        default="soft",
        help="ECUReset subfunction to send.",
    )
    reset.add_argument("--extended-session", action="store_true", help="Send 10 03 before ECUReset.")
    reset.add_argument("--tester-present", action="store_true", help="Send 3E 00 before ECUReset.")
    reset.add_argument("--functional", action="store_true", help="Use functional raw service operation if available.")
    reset.add_argument("--delay", type=float, default=0.05, help="Delay between requests in seconds.")
    reset.add_argument("--json", action="store_true", help="Print JSON after the table.")
    reset.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Required confirmation because ECUReset can interrupt a real control unit.",
    )
    reset.set_defaults(command="reset-ecu")

    return parser


def build_transport(args: argparse.Namespace) -> DiagnosticTransport:
    if args.transport == "virtual":
        return VirtualEcuTransport()

    from adapters.odis_soap import OdisSoapTransport

    return OdisSoapTransport(wsdl_url=args.wsdl, debug=args.debug)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        transport = build_transport(args)

        if args.command == "list-ops":
            print(render_operations(transport))
            return 0

        if args.command == "read-identification":
            dids = split_dids(args.did) if args.did else tuple(default_dids())
            config = PipelineConfig(
                ecu_identifier=args.ecu,
                dids=dids,
                use_extended_session=args.extended_session,
                use_tester_present=args.tester_present,
                functional=args.functional,
                delay_seconds=args.delay,
            )
            result = execute_identification_pipeline(transport, config)
            print(render_table(result))
            if args.json:
                print(render_json(result))
            return 0

        if args.command == "reset-ecu":
            if not args.confirm_reset:
                parser.error("reset-ecu requires --confirm-reset.")
            config = EcuResetConfig(
                ecu_identifier=args.ecu,
                reset_type=args.reset_type,
                use_extended_session=args.extended_session,
                use_tester_present=args.tester_present,
                functional=args.functional,
                delay_seconds=args.delay,
            )
            result = execute_ecu_reset(transport, config)
            print(render_table(result))
            if args.json:
                print(render_json(result))
            return 0

        parser.error(f"Unknown command: {args.command}")
        return 2

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
