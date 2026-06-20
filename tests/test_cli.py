from cli.main import main


def test_cli_read_identification_with_virtual_transport(capsys):
    exit_code = main(
        [
            "--transport",
            "virtual",
            "read-identification",
            "--ecu",
            "01",
            "--did",
            "F190",
            "--delay",
            "0",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ECU: 01" in captured.out
    assert "Value" in captured.out
    assert "Raw response" in captured.out
    assert "22F190" in captured.out
    assert "VIRTUALVIN0000001" in captured.out


def test_cli_reset_ecu_with_virtual_transport(capsys):
    exit_code = main(
        [
            "--transport",
            "virtual",
            "reset-ecu",
            "--ecu",
            "01",
            "--reset-type",
            "soft",
            "--confirm-reset",
            "--delay",
            "0",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "1103" in captured.out
    assert "5103" in captured.out
