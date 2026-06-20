"""Known identification DIDs commonly used for read-only ECU identification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DidDefinition:
    did: str
    name: str
    description: str


COMMON_IDENTIFICATION_DIDS: tuple[DidDefinition, ...] = (
    DidDefinition("F187", "vehicle_manufacturer_spare_part_number", "Vehicle manufacturer spare part number."),
    DidDefinition("F188", "vehicle_manufacturer_ecu_software_number", "Vehicle manufacturer ECU software number."),
    DidDefinition("F189", "vehicle_manufacturer_ecu_software_version", "Vehicle manufacturer ECU software version."),
    DidDefinition("F18A", "system_supplier_identifier", "System supplier identifier."),
    DidDefinition("F18B", "ecu_manufacturing_date", "ECU manufacturing date."),
    DidDefinition("F18C", "ecu_serial_number", "ECU serial number."),
    DidDefinition("F190", "vin", "Vehicle identification number when exposed by the ECU."),
    DidDefinition("F191", "vehicle_manufacturer_ecu_hardware_number", "Vehicle manufacturer ECU hardware number."),
    DidDefinition("F192", "system_supplier_ecu_hardware_number", "System supplier ECU hardware number."),
    DidDefinition("F193", "system_supplier_ecu_hardware_version", "System supplier ECU hardware version."),
    DidDefinition("F194", "system_supplier_ecu_software_number", "System supplier ECU software number."),
    DidDefinition("F195", "system_supplier_ecu_software_version", "System supplier ECU software version."),
    DidDefinition("F197", "system_name_or_engine_type", "System name or engine type, if provided by the ECU."),
)


def did_name_map() -> dict[str, str]:
    return {item.did: item.name for item in COMMON_IDENTIFICATION_DIDS}


def default_dids() -> list[str]:
    return [item.did for item in COMMON_IDENTIFICATION_DIDS]
