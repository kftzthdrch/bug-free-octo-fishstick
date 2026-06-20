# Usage

## 1. Prepare ODIS

Before running the Python client:

1. Start ODIS.
2. Load the correct project and diagnostic data.
3. Connect the VCI / DoIP / CAN interface.
4. Ensure the ODIS WebService/SOAP interface is enabled.
5. Confirm the WSDL endpoint is reachable, usually similar to:

```text
http://127.0.0.1:8081/?wsdl
```

## 2. Install the project

```bash
python -m venv .venv
pip install -e .[dev]
```

## 3. Inspect the WebService operations

```bash
diagbridge --wsdl "http://127.0.0.1:8081/?wsdl" list-ops
```

The adapter searches for operation names like:

```text
ConnectToEcuAndOpenConnection
SendRawService
SendRawServiceFunctional
CloseConnection
```

If your WSDL uses different names, edit the alias lists in:

```text
src/adapters/odis_soap.py
```

## 4. Read common SW/HW identification DIDs

```bash
diagbridge --wsdl "http://127.0.0.1:8081/?wsdl" read-identification \
  --ecu "01" \
  --tester-present \
  --did F187,F188,F189,F18C,F190,F191,F192,F193,F194,F195
```

On Windows PowerShell:

```powershell
diagbridge --wsdl "http://127.0.0.1:8081/?wsdl" read-identification `
  --ecu "01" `
  --tester-present `
  --did F187,F188,F189,F18C,F190,F191,F192,F193,F194,F195
```

## 5. Use extended session only when required

Some ECUs require an extended diagnostic session for certain identification DIDs:

```bash
diagbridge read-identification --ecu "01" --extended-session --tester-present --did F188,F189,F191,F195
```

This sends:

```text
10 03
3E 00
22 F1 88
22 F1 89
22 F1 91
22 F1 95
```

## 6. JSON output

```bash
diagbridge read-identification --ecu "01" --did F190 --json
```

## 7. Reset an ECU

ECU reset is an active operation. The CLI requires explicit confirmation:

```bash
diagbridge --wsdl "http://127.0.0.1:8081/?wsdl" reset-ecu \
  --ecu "01" \
  --reset-type soft \
  --confirm-reset
```

Supported reset types:

- `hard` sends `11 01`.
- `key-off-on` sends `11 02`.
- `soft` sends `11 03`.
- `enable-rapid-power-shutdown` sends `11 04`.
- `disable-rapid-power-shutdown` sends `11 05`.

Test the same path without ODIS:

```bash
diagbridge --transport virtual reset-ecu --ecu "01" --reset-type soft --confirm-reset --delay 0 --json
```

## 8. Typical UDS responses

Positive response:

```text
Request:  22 F1 90
Response: 62 F1 90 ...
```

Negative response:

```text
Request:  22 F1 90
Response: 7F 22 31
```

`31` means `requestOutOfRange`.
