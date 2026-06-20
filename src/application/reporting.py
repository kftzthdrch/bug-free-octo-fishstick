"""Presentation helpers for CLI output."""

from __future__ import annotations

import json
from dataclasses import asdict

from application.pipeline import PipelineResult
from core.dids import did_name_map


def render_table(result: PipelineResult) -> str:
    names = did_name_map()
    lines = [
        "",
        f"ECU: {result.ecu_identifier}",
        "=" * 132,
        f"{'DID':<8} {'Name':<42} {'Request':<10} {'Value':<28} {'Raw response':<30} Status",
        "-" * 132,
    ]

    for response in result.responses:
        did = response.did or "-"
        name = names.get(did, "-") if did != "-" else "-"
        response_short = response.response_hex[:28] + ("..." if len(response.response_hex) > 28 else "")
        value = response.display_value or "-"
        value_short = value[:26] + ("..." if len(value) > 26 else "")
        status = "OK" if response.positive else response.note
        lines.append(
            f"{did:<8} {name:<42} {response.request_hex:<10} {value_short:<28} {response_short:<30} {status}"
        )

    lines.append("=" * 132)
    return "\n".join(lines)


def render_json(result: PipelineResult) -> str:
    return json.dumps(
        {
            "ecu_identifier": result.ecu_identifier,
            "responses": [asdict(item) for item in result.responses],
        },
        indent=2,
    )
