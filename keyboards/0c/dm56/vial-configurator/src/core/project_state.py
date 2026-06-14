"""
项目状态模型 — 贯穿整个向导的共享数据
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .kle_parser import KLEKey
from .firmware_generator import FirmwareConfig


@dataclass
class ProjectState:
    """向导各步骤共享的状态"""
    # Step 1
    kle_raw: str = ""
    keys: List[KLEKey] = field(default_factory=list)

    # Step 2
    is_split: bool = False
    split_x_threshold: float = 0.0
    diode_direction: str = "COL2ROW"
    matrix_rows: int = 0
    matrix_cols: int = 0

    # Step 3
    mcu_key: str = "RP2040"
    row_pins: List[str] = field(default_factory=list)
    col_pins: List[str] = field(default_factory=list)

    # Step 4
    serial_driver: str = "vendor"
    serial_tx: str = "GP0"
    serial_rx: str = "GP1"
    master_side: str = "left"

    # Step 5
    features: Dict[str, bool] = field(default_factory=dict)
    module_pins: Dict[str, Dict[str, str]] = field(default_factory=dict)
    rgb_led_count: int = 0
    encoders: List[Dict[str, str]] = field(default_factory=list)

    # Step 6
    vial_uid: List[int] = field(default_factory=list)
    unlock_rows: List[int] = field(default_factory=lambda: [0, 0])
    unlock_cols: List[int] = field(default_factory=lambda: [0, 1])
    layer_count: int = 5
    debounce: int = 5

    # Step 7
    keymaps: List[List[str]] = field(default_factory=list)

    # 基本信息
    keyboard_name: str = "my_keyboard"
    manufacturer: str = "Custom"
    vid: str = "0x6464"
    pid: str = "0x0001"

    def to_firmware_config(self) -> FirmwareConfig:
        from .mcu_db import MCU_DATABASE
        mcu = MCU_DATABASE.get(self.mcu_key)
        return FirmwareConfig(
            keyboard_name=self.keyboard_name,
            manufacturer=self.manufacturer,
            vid=self.vid,
            pid=self.pid,
            processor=mcu.processor if mcu else self.mcu_key,
            bootloader=mcu.bootloader if mcu else "rp2040",
            rows=self.row_pins,
            col_pins=self.col_pins,
            diode_direction=self.diode_direction,
            is_split=self.is_split,
            master_side=self.master_side,
            serial_driver=self.serial_driver,
            serial_tx_pin=self.serial_tx,
            serial_rx_pin=self.serial_rx,
            vial_uid=self.vial_uid,
            unlock_rows=self.unlock_rows,
            unlock_cols=self.unlock_cols,
            layer_count=self.layer_count,
            debounce=self.debounce,
            features=self.features,
            module_pins=self.module_pins,
            rgb_led_count=self.rgb_led_count,
            encoders=self.encoders,
            keys=self.keys,
            keymaps=self.keymaps,
            matrix_rows=self.matrix_rows,
            matrix_cols=self.matrix_cols,
        )
