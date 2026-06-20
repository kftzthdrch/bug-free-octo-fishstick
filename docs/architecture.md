# Architecture

The project is built as a small diagnostic pipeline. The main goal is to prevent SOAP, CLI, and ODIS-specific details from leaking into UDS parsing and request safety rules. Source code is organized by architecture directly under `src`.

## Layer map

```mermaid
flowchart TD
    CLI[CLI: argparse commands]
    APP[Application: pipeline use cases]
    PORT[Transport protocol boundary]
    SOAP[Adapter: ODIS SOAP/WebService]
    UDS[UDS modules: requests, responses, DIDs, NRCs]
    ODIS[Running ODIS instance]
    ECU[Target ECU]

    CLI --> APP
    APP --> PORT
    APP --> UDS
    SOAP -. implements .-> PORT
    SOAP --> ODIS
    ODIS --> ECU
```

## Dependency rules

```mermaid
flowchart LR
    Uds[core]
    Pipeline[application]
    Transport[adapters]
    Cli[cli]

    Cli --> Pipeline
    Cli --> Transport
    Pipeline --> Uds
    Pipeline --> Protocol[protocols]
    Transport --> Uds

    Transport -. forbidden .-> Cli
    Uds -. forbidden .-> Pipeline
    Uds -. forbidden .-> Transport
    Uds -. forbidden .-> Zeep[zeep / SOAP]
```

Rules:

- `core` contains no ODIS, SOAP, CLI, or framework dependency.
- `application` coordinates behavior but does not know Zeep-specific details.
- `adapters` contains external-system SOAP code and the virtual ECU.
- `cli` composes transport plus application use case.

## Runtime sequence

```mermaid
sequenceDiagram
    actor User
    participant CLI
    participant Pipeline
    participant Core
    participant SOAP as ODIS SOAP Adapter
    participant ODIS
    participant ECU

    User->>CLI: diagbridge read-identification --ecu 01 --did F190
    CLI->>Pipeline: PipelineConfig
    Pipeline->>SOAP: connect_to_ecu("01")
    SOAP->>ODIS: ConnectToEcuAndOpenConnection
    ODIS->>ECU: Open diagnostic connection
    ECU-->>ODIS: Connection ready
    ODIS-->>SOAP: Connection handle

    Pipeline->>Core: build ReadDataByIdentifier request
    Core-->>Pipeline: 22F190
    Pipeline->>SOAP: send_raw_service("22F190")
    SOAP->>ODIS: SendRawService
    ODIS->>ECU: UDS 22 F1 90
    ECU-->>ODIS: UDS 62 F1 90 ...
    ODIS-->>SOAP: Raw response
    SOAP-->>Pipeline: response object
    Pipeline->>Core: parse_uds_response
    Core-->>Pipeline: UdsResponse
    Pipeline->>SOAP: close_connection
    Pipeline-->>CLI: PipelineResult
    CLI-->>User: table / JSON
```

## Main modules

| Module | Responsibility |
| --- | --- |
| `core.hexcodec` | Hex normalization, bytes conversion, printable ASCII rendering. |
| `core.requests` | Build and validate supported UDS requests. |
| `core.responses` | Extract SOAP response data and parse UDS positive/negative responses. |
| `core.dids` | DID catalogue for common identification values. |
| `core.nrc` | Negative response code descriptions. |
| `adapters.protocols` | Transport interface expected by the pipeline. |
| `adapters.odis_soap` | Zeep/ODIS SOAP binding and operation alias fallback. |
| `adapters.virtual_ecu` | In-process ECU simulator for local tests. |
| `application.pipeline` | Identification and ECU reset orchestration. |
| `application.reporting` | Table and JSON rendering. |
| `cli.main` | Command-line argument parsing and composition. |

## Why this shape

ODIS SOAP signatures differ between installations. The project isolates that instability in `adapters.odis_soap`. If your WSDL uses different operation names or argument names, you change the adapter without touching UDS parsing or pipeline logic.
