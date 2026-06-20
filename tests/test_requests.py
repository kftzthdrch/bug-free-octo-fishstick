import pytest

from core.requests import (
    ecu_reset_request,
    ensure_read_only_request,
    read_did_request,
    tester_present_request as build_tester_present_request,
)


def test_read_did_request():
    request = read_did_request("F190")
    assert request.raw_hex == "22F190"


def test_tester_present_request():
    assert build_tester_present_request().raw_hex == "3E00"


def test_ecu_reset_request():
    assert ecu_reset_request("hard").raw_hex == "1101"
    assert ecu_reset_request("key-off-on").raw_hex == "1102"
    assert ecu_reset_request("soft").raw_hex == "1103"


def test_blocks_security_access():
    with pytest.raises(ValueError, match="Blocked unsafe"):
        ensure_read_only_request("2701")


def test_blocks_write_did():
    with pytest.raises(ValueError, match="Blocked unsafe"):
        ensure_read_only_request("2EF19000")


def test_blocks_unsupported_arbitrary_service():
    with pytest.raises(ValueError, match="Unsupported"):
        ensure_read_only_request("1902FF")


def test_blocks_unknown_reset_type():
    with pytest.raises(ValueError, match="Unsupported ECU reset type"):
        ecu_reset_request("factory")


def test_blocks_unsupported_reset_subfunction():
    with pytest.raises(ValueError, match="Only ECUReset"):
        ensure_read_only_request("117F")
