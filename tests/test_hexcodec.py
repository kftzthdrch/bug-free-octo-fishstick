import pytest

from core.hexcodec import bytes_to_hex, hex_to_bytes, normalize_hex, safe_ascii


def test_normalize_hex_accepts_common_separators():
    assert normalize_hex("22 F1 90") == "22F190"
    assert normalize_hex("0x22-0xF1-0x90") == "22F190"
    assert normalize_hex("22_F1_90") == "22F190"


def test_normalize_hex_rejects_bad_values():
    with pytest.raises(ValueError):
        normalize_hex("22F19")
    with pytest.raises(ValueError):
        normalize_hex("22ZZ90")


def test_byte_helpers():
    assert hex_to_bytes("62 F1 90 41") == b"\x62\xF1\x90A"
    assert bytes_to_hex(b"\x62\xF1\x90A") == "62F19041"
    assert safe_ascii(b"ABC\x00\xff") == "ABC.."
