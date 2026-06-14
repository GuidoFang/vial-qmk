"""
MCU 主控数据库
包含 QMK 支持的主要主控及其引脚信息
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class MCUPin:
    name: str           # 引脚名（如 GP0, PB0, PA1）
    number: int         # 物理编号
    functions: List[str] = field(default_factory=list)  # 支持的功能
    is_usable: bool = True


@dataclass
class MCU:
    name: str
    processor: str      # QMK processor 字段
    bootloader: str     # QMK bootloader 字段
    pins: List[MCUPin] = field(default_factory=list)
    serial_drivers: List[str] = field(default_factory=list)
    max_matrix_pins: int = 30
    supports_usb: bool = True
    notes: str = ""

    def usable_pins(self) -> List[MCUPin]:
        return [p for p in self.pins if p.is_usable]

    def pin_names(self) -> List[str]:
        return [p.name for p in self.usable_pins()]


def _rp2040_pins() -> List[MCUPin]:
    pins = []
    # GP0-GP29，GP23/24/25/29 部分板子保留
    reserved = {23, 24, 25, 29}  # 部分开发板保留，但仍可配置
    for i in range(30):
        funcs = ["GPIO", "UART", "SPI", "I2C", "PWM"]
        if i in (0, 1, 4, 5, 8, 9, 12, 13, 16, 17, 20, 21):
            funcs.append("UART_TX" if i % 4 < 2 else "UART_RX")
        if i in (2, 3, 6, 7, 10, 11, 14, 15, 18, 19, 22, 26, 27):
            funcs.append("I2C")
        if i in range(26, 30):
            funcs.append("ADC")
        pins.append(MCUPin(
            name=f"GP{i}",
            number=i,
            functions=funcs,
            is_usable=True
        ))
    return pins


def _atmega32u4_pins() -> List[MCUPin]:
    pins = []
    port_map = {
        'B': range(0, 8),
        'C': [6, 7],
        'D': range(0, 8),
        'E': [2, 6],
        'F': range(0, 8),
    }
    for port, nums in port_map.items():
        for n in nums:
            name = f"P{port}{n}"
            funcs = ["GPIO"]
            if port == 'D' and n in (2, 3):
                funcs.append("UART")
            if port in ('B', 'D') and n in (1, 2, 3):
                funcs.append("SPI")
            if port == 'D' and n in (0, 1):
                funcs.append("I2C")
            if port == 'F':
                funcs.append("ADC")
            # USB 引脚不可用于矩阵
            is_usable = not (port == 'D' and n in (4, 5, 6, 7) and False)
            pins.append(MCUPin(name=name, number=n, functions=funcs, is_usable=is_usable))
    return pins


def _stm32f411_pins() -> List[MCUPin]:
    pins = []
    port_configs = {
        'A': range(0, 16),
        'B': range(0, 16),
        'C': range(0, 16),
    }
    for port, nums in port_configs.items():
        for n in nums:
            name = f"P{port}{n}"
            funcs = ["GPIO"]
            if port == 'A' and n in (9, 10):
                funcs.append("UART")
            if port == 'B' and n in (6, 7, 8, 9):
                funcs.append("I2C")
            if port == 'A' and n in (4, 5, 6, 7):
                funcs.append("SPI")
            if port == 'A' and n in range(0, 8):
                funcs.append("ADC")
            pins.append(MCUPin(name=name, number=n, functions=funcs, is_usable=True))
    return pins


# 主控数据库
MCU_DATABASE: Dict[str, MCU] = {
    "RP2040": MCU(
        name="RP2040 (Pi Pico / Pro Micro RP2040)",
        processor="RP2040",
        bootloader="rp2040",
        pins=_rp2040_pins(),
        serial_drivers=["vendor", "usart"],
        max_matrix_pins=26,
        notes="推荐用于新设计。支持 USB Full-Duplex USART 分体通信。双击 Boot 按钮进入 UF2 烧录模式。"
    ),
    "atmega32u4": MCU(
        name="ATmega32U4 (Pro Micro / Elite-C)",
        processor="atmega32u4",
        bootloader="caterina",
        pins=_atmega32u4_pins(),
        serial_drivers=["bitbang", "usart"],
        max_matrix_pins=18,
        notes="经典方案，IO 口有限。分体串口推荐使用 D2/D3（UART）。"
    ),
    "STM32F411": MCU(
        name="STM32F411 (Blackpill)",
        processor="STM32F411",
        bootloader="stm32-dfu",
        pins=_stm32f411_pins(),
        serial_drivers=["usart", "bitbang"],
        max_matrix_pins=30,
        notes="高性能方案。需要 DFU 烧录工具或 USB DFU bootloader。"
    ),
    "STM32F072": MCU(
        name="STM32F072",
        processor="STM32F072",
        bootloader="stm32-dfu",
        pins=_stm32f411_pins(),
        serial_drivers=["usart", "bitbang"],
        max_matrix_pins=28,
        notes="低功耗 STM32，支持 USB DFU。"
    ),
    "atmega328p": MCU(
        name="ATmega328P (Converter/HandWired)",
        processor="atmega328p",
        bootloader="arduino",
        pins=[MCUPin(f"P{'BCD'[i//8]}{i%8}", i, ["GPIO"]) for i in range(24)],
        serial_drivers=["bitbang"],
        max_matrix_pins=20,
        notes="无原生 USB，需配合 USB 转串口芯片使用。"
    ),
}


# 各主控推荐的分体通信引脚组合
SPLIT_SERIAL_PRESETS: Dict[str, List[Dict]] = {
    "RP2040": [
        {
            "tx": "GP0", "rx": "GP1", "driver": "vendor",
            "desc": "双线全双工（VCC+GND+TX+RX）推荐",
            "note": "TRRS 4芯线：VCC/GND/TX/RX，左右分别刷写固件"
        },
        {"tx": "GP4", "rx": "GP5", "driver": "vendor", "desc": "UART1 备用"},
        {"tx": "GP8", "rx": "GP9", "driver": "vendor", "desc": "UART1 备用2"},
    ],
    "atmega32u4": [
        {
            "tx": "PD0", "rx": "PD0", "driver": "bitbang",
            "desc": "单线半双工（VCC+GND+1引脚）推荐",
            "note": "TRRS 4芯线：VCC/GND/Data/NC，TX和RX使用同一引脚"
        },
        {"tx": "PD3", "rx": "PD2", "driver": "usart", "desc": "双线 UART1"},
        {"tx": "PD1", "rx": "PD1", "driver": "bitbang", "desc": "单线备用"},
    ],
    "STM32F411": [
        {"tx": "PA9", "rx": "PA10", "driver": "usart", "desc": "USART1 (推荐)"},
        {"tx": "PA2", "rx": "PA3", "driver": "usart", "desc": "USART2"},
    ],
}


# 功能模块预设
FEATURE_MODULES = [
    {
        "key": "RGBLIGHT_ENABLE",
        "name": "RGB 灯带 (WS2812)",
        "rules_mk": "RGBLIGHT_ENABLE = yes",
        "config_defines": ["#define RGBLIGHT_ANIMATIONS", "#define RGBLED_NUM {count}"],
        "pins_needed": ["data"],
        "pin_labels": {"data": "Data 引脚"},
        "default_enabled": False,
    },
    {
        "key": "RGB_MATRIX_ENABLE",
        "name": "RGB Matrix (逐键 RGB)",
        "rules_mk": "RGB_MATRIX_ENABLE = yes",
        "config_defines": ["#define RGB_MATRIX_LED_COUNT {count}"],
        "pins_needed": ["data"],
        "pin_labels": {"data": "Data 引脚"},
        "default_enabled": False,
    },
    {
        "key": "ENCODER_ENABLE",
        "name": "旋转编码器",
        "rules_mk": "ENCODER_ENABLE = yes",
        "config_defines": ["#define ENCODER_RESOLUTION 4"],
        "pins_needed": ["a", "b"],
        "pin_labels": {"a": "A 相引脚", "b": "B 相引脚"},
        "default_enabled": False,
        "repeatable": True,
    },
    {
        "key": "OLED_ENABLE",
        "name": "OLED 显示屏",
        "rules_mk": "OLED_ENABLE = yes",
        "config_defines": [],
        "pins_needed": ["sda", "scl"],
        "pin_labels": {"sda": "SDA (I2C Data)", "scl": "SCL (I2C Clock)"},
        "default_enabled": False,
    },
    {
        "key": "AUDIO_ENABLE",
        "name": "蜂鸣器 / 音频",
        "rules_mk": "AUDIO_ENABLE = yes",
        "config_defines": ["#define AUDIO_PIN {pin}"],
        "pins_needed": ["audio"],
        "pin_labels": {"audio": "音频引脚"},
        "default_enabled": False,
    },
    {
        "key": "EXTRAKEY_ENABLE",
        "name": "多媒体键（音量/播放）",
        "rules_mk": "EXTRAKEY_ENABLE = yes",
        "config_defines": [],
        "pins_needed": [],
        "default_enabled": True,
    },
    {
        "key": "NKRO_ENABLE",
        "name": "全键无冲 (NKRO)",
        "rules_mk": "NKRO_ENABLE = yes",
        "config_defines": [],
        "pins_needed": [],
        "default_enabled": True,
    },
    {
        "key": "MOUSEKEY_ENABLE",
        "name": "鼠标按键",
        "rules_mk": "MOUSEKEY_ENABLE = yes",
        "config_defines": [],
        "pins_needed": [],
        "default_enabled": False,
    },
    {
        "key": "COMMAND_ENABLE",
        "name": "QMK 调试命令",
        "rules_mk": "COMMAND_ENABLE = yes",
        "config_defines": [],
        "pins_needed": [],
        "default_enabled": True,
    },
    {
        "key": "BOOTMAGIC_ENABLE",
        "name": "Bootmagic（长按 ESC 进入 Boot）",
        "rules_mk": "BOOTMAGIC_ENABLE = yes",
        "config_defines": [],
        "pins_needed": [],
        "default_enabled": False,
    },
]
