# DiagBridge

A controlled Python diagnostic bridge for ODIS WebService and UDS ECU workflows.

The project is structured to keep diagnostic intent, UDS parsing, transport binding, and CLI concerns separate.

## Quick start on Windows

Create and activate the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e .[dev]
```

Run the project against the virtual ECU first:

```powershell
diagbridge --transport virtual read-identification --ecu 01 --did F190,F1FF --delay 0 --json
```

Run the test suite:

```powershell
python -m pytest
```

## Supported scope

Allowed by this implementation:

- `0x10` DiagnosticSessionControl, limited to configured session requests.
- `0x11` ECUReset, limited to known reset subfunctions and requiring explicit CLI confirmation.
- `0x3E` TesterPresent.
- `0x22` ReadDataByIdentifier for SW/HW/version identification DIDs.
- ODIS SOAP/WSDL operation inspection.

Not implemented:

- `0x27` SecurityAccess.
- `0x2E` WriteDataByIdentifier.
- `0x31` RoutineControl.
- Coding, adaptation, flashing, immobilizer, component protection, or seed-key logic.

## CLI structure

```bash
diagbridge [--transport odis|virtual] [--wsdl URL] COMMAND
```

Available commands:

```text
list-ops
read-identification
reset-ecu
```

Transport choices:

- `--transport odis` uses the real ODIS SOAP/WebService adapter. This is the default.
- `--transport virtual` uses the in-process virtual ECU for local testing.

## Use with the virtual ECU

The virtual ECU does not require ODIS, a VCI, DoIP, CAN, or a real control unit. Use it to verify the Python pipeline, request validation, response parsing, JSON/table output, and reset command behavior.

Read identification DIDs:

```powershell
diagbridge --transport virtual read-identification `
  --ecu 01 `
  --did F187,F188,F189,F190,F195,F1FF `
  --delay 0 `
  --json
```

`F1FF` is intentionally unknown in the simulator and returns a negative UDS response:

```text
7F 22 31
```

That means `requestOutOfRange`.

Test ECU reset:

```powershell
diagbridge --transport virtual reset-ecu `
  --ecu 01 `
  --reset-type soft `
  --confirm-reset `
  --delay 0 `
  --json
```

Expected reset request/response for soft reset:

```text
Request:  11 03
Response: 51 03
```

## Use with real ODIS

Before using the real transport:

1. Start ODIS.
2. Load the correct project/diagnostic data.
3. Connect the VCI, DoIP, or CAN interface.
4. Enable or start the ODIS WebService/SOAP interface.
5. Confirm the WSDL endpoint is reachable, commonly:

```text
http://127.0.0.1:8081/?wsdl
```

Inspect SOAP operations:

```bash
diagbridge --wsdl "http://127.0.0.1:8081/?wsdl" list-ops
```

Read common ECU identification DIDs:

```bash
diagbridge --wsdl "http://127.0.0.1:8081/?wsdl" read-identification \
  --ecu "01" \
  --tester-present \
  --did F187,F188,F189,F18C,F190,F191,F192,F193,F194,F195
```

Use `--extended-session` only when the ECU requires it for the DIDs you read.

```bash
diagbridge read-identification --ecu "01" --extended-session --tester-present --did F188,F189,F191,F195
```

## ECU reset

ECU reset is an active diagnostic operation. The CLI requires `--confirm-reset` so it cannot be triggered by accident.

```bash
diagbridge --wsdl "http://127.0.0.1:8081/?wsdl" reset-ecu \
  --ecu "01" \
  --reset-type soft \
  --confirm-reset
```

Supported reset types are `hard`, `key-off-on`, `soft`, `enable-rapid-power-shutdown`, and `disable-rapid-power-shutdown`.

Reset type mapping:

```text
hard                         -> 11 01
key-off-on                   -> 11 02
soft                         -> 11 03
enable-rapid-power-shutdown  -> 11 04
disable-rapid-power-shutdown -> 11 05
```

## Project layout

```text
src/
  core/          UDS hex validation, request/response models, DID catalogue
  adapters/      ODIS SOAP adapter, virtual ECU, and transport protocol
  application/   Pipeline orchestration, reporting, and use cases
  cli/           argparse CLI entrypoint

docs/            Markdown documentation with Mermaid diagrams
tests/           Unit tests for parsing, pipeline behavior, CLI, and virtual ECU
```

## Documentation

Start here:

- [Architecture](docs/architecture.md)
- [Usage](docs/usage.md)
- [ODIS SOAP integration](docs/odis_webservice.md)
- [Safety model](docs/safety.md)
- [Development notes](docs/development.md)
