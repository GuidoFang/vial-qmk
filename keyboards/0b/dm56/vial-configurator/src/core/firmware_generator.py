"""
固件文件生成器 v2
输入：KeyboardModel + ProjectConfig
输出：keyboard.json / keymap.c / vial.json / config.h / rules.mk
"""
import json
import os
from typing import List, Dict
from .key_model import KeyboardModel


class ProjectConfig:
    def __init__(self):
        self.keyboard_name = "my_keyboard"
        self.manufacturer = "Custom"
        self.vid = "0x6464"
        self.pid = "0x0001"
        self.device_version = "1.0.0"
        self.processor = "RP2040"
        self.bootloader = "rp2040"
        self.mcu_key = "RP2040"
        self.row_pins: List[str] = []
        self.col_pins: List[str] = []
        self.row_pins_right: List[str] = []  # 不对称分体右手引脚
        self.col_pins_right: List[str] = []
        self.diode_direction = "COL2ROW"
        self.is_split = False
        self.is_asymmetric = False  # 是否不对称分体
        self.master_side = "left"
        self.serial_driver = "vendor"
        self.serial_tx = "GP0"
        self.serial_rx = "GP1"
        self.vial_uid: List[int] = []
        self.unlock_rows: List[int] = [0, 0]
        self.unlock_cols: List[int] = [0, 1]
        self.layer_count = 4
        self.debounce = 5
        self.features: Dict[str, bool] = {
            "EXTRAKEY_ENABLE": True, "NKRO_ENABLE": True,
            "COMMAND_ENABLE": False, "MOUSEKEY_ENABLE": False,
            "BOOTMAGIC_ENABLE": False, "RGBLIGHT_ENABLE": False,
            "RGB_MATRIX_ENABLE": False, "ENCODER_ENABLE": False,
            "OLED_ENABLE": False, "AUDIO_ENABLE": False,
        }
        self.module_pins: Dict[str, Dict[str, str]] = {}
        self.rgb_led_count = 0
        self.encoders: List[Dict[str, str]] = []

    def uid_str(self) -> str:
        if not self.vial_uid:
            import random
            self.vial_uid = [random.randint(0, 255) for _ in range(8)]
        return "{" + ", ".join(f"0x{b:02X}" for b in self.vial_uid) + "}"


class FirmwareGenerator:

    def __init__(self, kb: KeyboardModel, cfg: ProjectConfig):
        self.kb = kb
        self.cfg = cfg

    def gen_keyboard_json(self, side: str = "left") -> str:
        cfg = self.cfg
        layout_keys = []
        for k in self.kb.keys:
            entry: Dict = {"matrix": [k.row, k.col],
                           "x": round(k.x, 4), "y": round(k.y, 4)}
            if abs(k.w - 1.0) > 0.001: entry["w"] = round(k.w, 4)
            if abs(k.h - 1.0) > 0.001: entry["h"] = round(k.h, 4)
            if k.is_rotated():
                entry["r"] = round(k.r, 4)
                entry["rx"] = round(k.rx, 4)
                entry["ry"] = round(k.ry, 4)
            if k.label: entry["label"] = k.label
            layout_keys.append(entry)

        # 选择引脚：不对称分体需要区分左右手
        row_pins = cfg.row_pins
        col_pins = cfg.col_pins
        if cfg.is_split and cfg.is_asymmetric and side == "right":
            row_pins = cfg.row_pins_right
            col_pins = cfg.col_pins_right

        data = {
            "keyboard_name": cfg.keyboard_name,
            "manufacturer": cfg.manufacturer,
            "url": "", "maintainer": "qmk",
            "usb": {"vid": cfg.vid, "pid": cfg.pid,
                    "device_version": cfg.device_version},
            "matrix_pins": {"cols": col_pins, "rows": row_pins},
            "diode_direction": cfg.diode_direction,
            "processor": cfg.processor, "bootloader": cfg.bootloader,
            "layouts": {"LAYOUT": {"layout": layout_keys}},
        }
        if cfg.is_split:
            data["split"] = {"enabled": True}
        return json.dumps(data, indent=4, ensure_ascii=False)

    def gen_keymap_c(self) -> str:
        keys = sorted(self.kb.keys, key=lambda k: (k.row, k.col))
        layer_count = self.kb.layer_count()
        lines = ["#include QMK_KEYBOARD_H", ""]
        names = [f"_L{i}" for i in range(layer_count)]
        for i, n in enumerate(names):
            lines.append(f"#define {n} {i}")
        lines.append("\nconst uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {")
        for li in range(layer_count):
            kcs = [k.get_keycode(li) for k in keys]
            chunks = [kcs[i:i+12] for i in range(0, len(kcs), 12)]
            sep = "," if li < layer_count - 1 else ""
            lines.append(f"    [{names[li]}] = LAYOUT(")
            for chunk in chunks:
                lines.append("        " + ", ".join(f"{c:<16}" for c in chunk) + ",")
            if lines[-1].endswith(","):
                lines[-1] = lines[-1][:-1]
            lines.append(f"    ){sep}")
        lines.append("};")
        return "\n".join(lines)

    def gen_vial_json(self) -> str:
        rows, cols = self.kb.matrix_size()
        data = {"matrix": {"rows": rows, "cols": cols},
                "layouts": {"keymap": self._build_vial_layout()}}
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _build_vial_layout(self) -> list:
        Y_TOL = 0.3
        normal  = [k for k in self.kb.keys if not k.is_rotated()]
        rotated = [k for k in self.kb.keys if k.is_rotated()]

        row_groups: Dict[float, list] = {}
        for k in sorted(normal, key=lambda k: k.y):
            placed = False
            for ey in list(row_groups.keys()):
                if abs(k.y - ey) < Y_TOL:
                    row_groups[ey].append(k); placed = True; break
            if not placed:
                row_groups[k.y] = [k]

        result = []
        cur_y = 0.0
        for ey in sorted(row_groups.keys()):
            group = sorted(row_groups[ey], key=lambda k: k.x)
            row_arr = []
            props: Dict = {}
            dy = ey - cur_y
            if abs(dy - 1.0) > 0.01: props["y"] = round(dy - 1.0, 4)
            if abs(group[0].x) > 0.01: props["x"] = round(group[0].x, 4)
            if props: row_arr.append(props)
            cur_x = group[0].x
            for k in group:
                gap = k.x - cur_x
                if abs(gap) > 0.01: row_arr.append({"x": round(gap, 4)})
                ep: Dict = {}
                if abs(k.w - 1.0) > 0.01: ep["w"] = round(k.w, 4)
                if abs(k.h - 1.0) > 0.01: ep["h"] = round(k.h, 4)
                if ep: row_arr.append(ep)
                row_arr.append(f"{k.row},{k.col}")
                cur_x = k.x + k.w
            cur_y = ey + 1.0
            result.append(row_arr)

        for k in rotated:
            props = {"r": round(k.r,4), "rx": round(k.rx,4), "ry": round(k.ry,4),
                     "y": round(k.y-k.ry,4), "x": round(k.x-k.rx,4)}
            if abs(k.w-1.0)>0.001: props["w"] = round(k.w,4)
            if abs(k.h-1.0)>0.001: props["h"] = round(k.h,4)
            result.append([props, f"{k.row},{k.col}"])
        return result

    def gen_config_h(self) -> str:
        lines = ["#pragma once", ""]
        if "RP2040" in self.cfg.processor:
            lines += ["#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET",
                      "#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET_TIMEOUT 500U", ""]
        return "\n".join(lines)

    def gen_rules_mk(self) -> str:
        cfg = self.cfg
        lines = [f"BOOTMAGIC_ENABLE = {'yes' if cfg.features.get('BOOTMAGIC_ENABLE') else 'no'}"]
        if cfg.is_split: lines.append(f"SERIAL_DRIVER = {cfg.serial_driver}")
        lines.append("")
        for f in ["EXTRAKEY_ENABLE","NKRO_ENABLE","COMMAND_ENABLE","MOUSEKEY_ENABLE"]:
            lines.append(f"{f} = {'yes' if cfg.features.get(f) else 'no'}")
        lines.append("")
        for f in ["RGBLIGHT_ENABLE","RGB_MATRIX_ENABLE","ENCODER_ENABLE","OLED_ENABLE","AUDIO_ENABLE"]:
            if cfg.features.get(f): lines.append(f"{f} = yes")
        return "\n".join(lines)

    def gen_keymap_config_h(self, side: str = "left") -> str:
        cfg = self.cfg
        lines = ["#pragma once", "",
                 f"#define VIAL_KEYBOARD_UID {cfg.uid_str()}",
                 f"#define VIAL_UNLOCK_COMBO_ROWS {{ {', '.join(str(r) for r in cfg.unlock_rows)} }}",
                 f"#define VIAL_UNLOCK_COMBO_COLS {{ {', '.join(str(c) for c in cfg.unlock_cols)} }}", ""]
        if cfg.is_split:
            m = "MASTER_LEFT" if side == "left" else "MASTER_RIGHT"
            lines += [f"#define {m}", "",
                      "#define SERIAL_USART_FULL_DUPLEX",
                      f"#define SERIAL_USART_TX_PIN {cfg.serial_tx}",
                      f"#define SERIAL_USART_RX_PIN {cfg.serial_rx}", ""]
        lines += [f"#define DYNAMIC_KEYMAP_LAYER_COUNT {cfg.layer_count}", "",
                  f"#define DEBOUNCE {cfg.debounce}", ""]
        if cfg.features.get("RGBLIGHT_ENABLE") and cfg.rgb_led_count:
            lines += [f"#define RGBLED_NUM {cfg.rgb_led_count}", "#define RGBLIGHT_ANIMATIONS", ""]
        if cfg.features.get("RGB_MATRIX_ENABLE") and cfg.rgb_led_count:
            lines += [f"#define RGB_MATRIX_LED_COUNT {cfg.rgb_led_count}", ""]
        if cfg.features.get("ENCODER_ENABLE") and cfg.encoders:
            ap = ", ".join(e["a"] for e in cfg.encoders)
            bp = ", ".join(e["b"] for e in cfg.encoders)
            lines += [f"#define ENCODERS_PAD_A {{ {ap} }}", f"#define ENCODERS_PAD_B {{ {bp} }}",
                      "#define ENCODER_RESOLUTION 4", ""]
        if cfg.features.get("OLED_ENABLE"):
            lines += ["#define OLED_TIMEOUT 30000", ""]
        if cfg.features.get("AUDIO_ENABLE"):
            pin = cfg.module_pins.get("AUDIO_ENABLE", {}).get("audio", "")
            if pin: lines += [f"#define AUDIO_PIN {pin}", ""]
        return "\n".join(lines)

    def gen_keymap_rules_mk(self) -> str:
        lines = ["VIA_ENABLE = yes", "VIAL_ENABLE = yes"]
        if self.cfg.is_split: lines.append("SPLIT_USB_DETECT = yes")
        return "\n".join(lines)

    def generate_all(self, output_dir: str) -> List[str]:
        cfg = self.cfg
        files = []

        def write(path, content):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            files.append(path)

        # 不对称分体：生成两个独立的固件文件夹
        if cfg.is_split and cfg.is_asymmetric:
            for side in ["left", "right"]:
                kb_dir = os.path.join(output_dir, f"{cfg.keyboard_name}_{side}")
                write(os.path.join(kb_dir, "keyboard.json"), self.gen_keyboard_json(side))
                write(os.path.join(kb_dir, "config.h"),      self.gen_config_h())
                write(os.path.join(kb_dir, "rules.mk"),       self.gen_rules_mk())

                km = os.path.join(kb_dir, "keymaps", f"vial_{side}")
                write(os.path.join(km, "config.h"),  self.gen_keymap_config_h(side))
                write(os.path.join(km, "rules.mk"),  self.gen_keymap_rules_mk())
                write(os.path.join(km, "keymap.c"),  self.gen_keymap_c())
                write(os.path.join(km, "vial.json"), self.gen_vial_json())
        else:
            # 对称分体或整体键盘：生成单个固件文件夹
            kb_dir = os.path.join(output_dir, cfg.keyboard_name)
            write(os.path.join(kb_dir, "keyboard.json"), self.gen_keyboard_json())
            write(os.path.join(kb_dir, "config.h"),      self.gen_config_h())
            write(os.path.join(kb_dir, "rules.mk"),       self.gen_rules_mk())

            sides = ["vial_left", "vial_right"] if cfg.is_split else ["vial"]
            for side in sides:
                s = "left" if "left" in side else "right"
                km = os.path.join(kb_dir, "keymaps", side)
                write(os.path.join(km, "config.h"),  self.gen_keymap_config_h(s))
                write(os.path.join(km, "rules.mk"),  self.gen_keymap_rules_mk())
                write(os.path.join(km, "keymap.c"),  self.gen_keymap_c())
                write(os.path.join(km, "vial.json"), self.gen_vial_json())

        return files
