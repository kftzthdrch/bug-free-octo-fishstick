import pytest

from adapters.virtual_ecu import VirtualEcuConnection, VirtualEcuTransport
from application.pipeline import EcuResetConfig, PipelineConfig, execute_ecu_reset, execute_identification_pipeline


def test_virtual_ecu_positive_services():
    transport = VirtualEcuTransport({"F190": b"WVWZZZTESTVIN123"})
    connection = transport.connect_to_ecu("01")

    assert transport.send_raw_service("10 03", "01", connection) == "5003003201"
    assert connection.session == "extended"
    assert transport.send_raw_service("3E00", "01", connection) == "7E00"
    assert connection.tester_present_count == 1
    assert transport.send_raw_service("22F190", "01", connection) == "62F1905756575A5A5A5445535456494E313233"


def test_virtual_ecu_unknown_did_returns_request_out_of_range():
    transport = VirtualEcuTransport({})

    assert transport.send_raw_service("22F1FF", "01") == "7F2231"


def test_virtual_ecu_reset():
    transport = VirtualEcuTransport()
    connection = transport.connect_to_ecu("01")
    transport.send_raw_service("1003", "01", connection)

    assert transport.send_raw_service("1103", "01", connection) == "5103"
    assert connection.reset_count == 1
    assert connection.last_reset_type == "03"
    assert connection.session == "default"


def test_virtual_ecu_reuses_pipeline():
    transport = VirtualEcuTransport({"F190": "VIRTUALVIN0000001"})
    result = execute_identification_pipeline(
        transport,
        PipelineConfig(
            ecu_identifier="01",
            dids=("F190", "F1FF"),
            use_extended_session=True,
            use_tester_present=True,
            delay_seconds=0,
        ),
    )

    assert [response.request_hex for response in result.responses] == ["1003", "3E00", "22F190", "22F1FF"]
    assert result.responses[0].positive is True
    assert result.responses[2].ascii_payload == "VIRTUALVIN0000001"
    assert result.responses[3].negative is True
    assert "requestOutOfRange" in result.responses[3].note


def test_virtual_ecu_reset_reuses_pipeline():
    transport = VirtualEcuTransport()
    result = execute_ecu_reset(
        transport,
        EcuResetConfig(ecu_identifier="01", reset_type="hard", use_extended_session=True, delay_seconds=0),
    )

    assert [response.request_hex for response in result.responses] == ["1003", "1101"]
    assert result.responses[-1].response_hex == "5101"
    assert result.responses[-1].positive is True


def test_virtual_ecu_strict_identifier():
    transport = VirtualEcuTransport(strict_ecu_identifier="VECU")

    with pytest.raises(ValueError, match="does not accept"):
        transport.connect_to_ecu("01")

    assert isinstance(transport.connect_to_ecu("VECU"), VirtualEcuConnection)
