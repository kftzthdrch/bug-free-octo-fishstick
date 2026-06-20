from core.responses import parse_uds_response


def test_positive_read_did_response():
    result = parse_uds_response("22 F1 90", "62 F1 90 57 56 57")
    assert result.positive is True
    assert result.negative is False
    assert result.did == "F190"
    assert result.payload_hex == "575657"
    assert result.ascii_payload == "WVW"
    assert result.display_value == "WVW"


def test_negative_response():
    result = parse_uds_response("22 F1 90", "7F 22 31")
    assert result.positive is False
    assert result.negative is True
    assert result.display_value == ""
    assert "requestOutOfRange" in result.note


def test_dict_response_extraction():
    result = parse_uds_response("22 F1 88", {"responseData": "62F188313233"})
    assert result.positive is True
    assert result.ascii_payload == "123"
