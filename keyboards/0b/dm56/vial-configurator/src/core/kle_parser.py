"""
KLE JSON 解析器 v3 — 支持从标签自动推断键值
"""
import json
import re
from typing import List
from .key_model import KeyModel


# KLE 标签到 QMK 键码的映射表
LABEL_TO_KEYCODE = {
    # 字母
    "A": "KC_A", "B": "KC_B", "C": "KC_C", "D": "KC_D", "E": "KC_E",
    "F": "KC_F", "G": "KC_G", "H": "KC_H", "I": "KC_I", "J": "KC_J",
    "K": "KC_K", "L": "KC_L", "M": "KC_M", "N": "KC_N", "O": "KC_O",
    "P": "KC_P", "Q": "KC_Q", "R": "KC_R", "S": "KC_S", "T": "KC_T",
    "U": "KC_U", "V": "KC_V", "W": "KC_W", "X": "KC_X", "Y": "KC_Y", "Z": "KC_Z",
    # 数字
    "1": "KC_1", "2": "KC_2", "3": "KC_3", "4": "KC_4", "5": "KC_5",
    "6": "KC_6", "7": "KC_7", "8": "KC_8", "9": "KC_9", "0": "KC_0",
    # 符号
    "-": "KC_MINS", "=": "KC_EQL", "[": "KC_LBRC", "]": "KC_RBRC",
    "\\": "KC_BSLS", ";": "KC_SCLN", "'": "KC_QUOT", "`": "KC_GRV",
    ",": "KC_COMM", ".": "KC_DOT", "/": "KC_SLSH",
    # 功能键
    "Esc": "KC_ESC", "Tab": "KC_TAB", "Caps": "KC_CAPS", "Shift": "KC_LSFT",
    "Ctrl": "KC_LCTL", "Alt": "KC_LALT", "Win": "KC_LGUI", "Space": "KC_SPC",
    "Enter": "KC_ENT", "Backspace": "KC_BSPC", "Delete": "KC_DEL",
    # F键
    "F1": "KC_F1", "F2": "KC_F2", "F3": "KC_F3", "F4": "KC_F4",
    "F5": "KC_F5", "F6": "KC_F6", "F7": "KC_F7", "F8": "KC_F8",
    "F9": "KC_F9", "F10": "KC_F10", "F11": "KC_F11", "F12": "KC_F12",
    # 导航
    "Home": "KC_HOME", "End": "KC_END", "PgUp": "KC_PGUP", "PgDn": "KC_PGDN",
    "Up": "KC_UP", "Down": "KC_DOWN", "Left": "KC_LEFT", "Right": "KC_RGHT",
}


class KLEParser:

    def parse_string(self, text: str) -> List[KeyModel]:
        return self.parse(json.loads(text))

    def parse_file(self, path: str) -> List[KeyModel]:
        with open(path, encoding="utf-8") as f:
            return self.parse(json.load(f))

    def parse(self, data) -> List[KeyModel]:
        rows = data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if any(k in data[0] for k in ("name", "author", "background")):
                rows = data[1:]

        keys: List[KeyModel] = []
        uid_counter = 0
        cur_x = cur_y = cur_r = cur_rx = cur_ry = 0.0
        cur_color = "#cccccc"
        cur_legend_color = "#000000"

        for row_item in rows:
            if not isinstance(row_item, list):
                continue
            nx = ny = 0.0
            nw = nh = 1.0
            nw2 = nh2 = nx2 = ny2 = 0.0

            for item in row_item:
                if isinstance(item, dict):
                    if "r"  in item: cur_r  = item["r"]
                    if "rx" in item: cur_rx = item["rx"]; cur_x = cur_rx
                    if "ry" in item: cur_ry = item["ry"]; cur_y = cur_ry
                    if "c"  in item: cur_color = item["c"]
                    if "t"  in item: cur_legend_color = item["t"].split("\n")[0]
                    if "x"  in item: nx  = item["x"]
                    if "y"  in item: ny  = item["y"]
                    if "w"  in item: nw  = item["w"]
                    if "h"  in item: nh  = item["h"]
                    if "w2" in item: nw2 = item["w2"]
                    if "h2" in item: nh2 = item["h2"]
                    if "x2" in item: nx2 = item["x2"]
                    if "y2" in item: ny2 = item["y2"]
                elif isinstance(item, str):
                    labels = item.split("\n")
                    label = labels[0].strip()
                    # 自动推断键值
                    keycode = self._infer_keycode(label)
                    k = KeyModel(
                        x=cur_x + nx, y=cur_y + ny,
                        w=nw, h=nh, r=cur_r, rx=cur_rx, ry=cur_ry,
                        x2=nx2, y2=ny2, w2=nw2, h2=nh2,
                        label=label,
                        color=cur_color,
                        legend_color=cur_legend_color,
                        uid=uid_counter,
                        keycodes=[keycode],
                    )
                    uid_counter += 1
                    keys.append(k)
                    cur_x = k.x + nw
                    nx = ny = 0.0; nw = nh = 1.0; nw2 = nh2 = nx2 = ny2 = 0.0

            cur_y += 1.0
            cur_x = cur_rx

        return keys

    def _infer_keycode(self, label: str) -> str:
        """从 KLE 标签推断 QMK 键码"""
        if not label:
            return "KC_NO"

        label_clean = label.strip()
        # 直接匹配
        if label_clean in LABEL_TO_KEYCODE:
            return LABEL_TO_KEYCODE[label_clean]

        # 大小写不敏感匹配
        label_upper = label_clean.upper()
        for key, code in LABEL_TO_KEYCODE.items():
            if key.upper() == label_upper:
                return code

        # 单字母/数字
        if len(label_clean) == 1:
            if label_clean.isalpha():
                return f"KC_{label_clean.upper()}"
            if label_clean.isdigit():
                return f"KC_{label_clean}"

        # 检测层切换标签（如 "MO(1)", "Layer 1"）
        mo_match = re.match(r"MO\((\d+)\)", label_clean, re.IGNORECASE)
        if mo_match:
            return f"MO({mo_match.group(1)})"

        layer_match = re.match(r"Layer\s*(\d+)", label_clean, re.IGNORECASE)
        if layer_match:
            return f"MO({layer_match.group(1)})"

        # 默认透明
        return "KC_TRNS"
