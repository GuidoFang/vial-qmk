"""
核心数据模型 — 按键三位一体
位置坐标(KLE) + 电气矩阵(row,col) + 各层键值 三者统一在一个对象中
"""
import math
import json
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class KeyModel:
    # ── 位置坐标（来自 KLE，单位：键宽） ─────────────────────────
    x: float = 0.0
    y: float = 0.0
    w: float = 1.0
    h: float = 1.0
    r: float = 0.0       # 旋转角度（度）
    rx: float = 0.0      # 旋转原点 x
    ry: float = 0.0      # 旋转原点 y
    x2: float = 0.0      # 第二形状偏移（KLE stepped key）
    y2: float = 0.0
    w2: float = 0.0
    h2: float = 0.0

    # ── 外观 ────────────────────────────────────────────────────
    label: str = ""       # KLE 顶层文字
    color: str = "#cccccc"
    legend_color: str = "#000000"

    # ── 电气矩阵 ────────────────────────────────────────────────
    row: int = -1
    col: int = -1

    # ── 各层键值 ────────────────────────────────────────────────
    # keycodes[0] = Layer0 键值, keycodes[1] = Layer1 ...
    keycodes: List[str] = field(default_factory=list)

    # ── UI 状态（运行时，不序列化） ──────────────────────────────
    selected: bool = False

    # ── ID（在项目中唯一） ──────────────────────────────────────
    uid: int = -1

    # ─────────────────────────────────────────────────────────── #

    def is_rotated(self) -> bool:
        return abs(self.r) > 0.001

    def physical_center(self) -> Tuple[float, float]:
        """返回按键物理中心坐标（已考虑旋转）"""
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2
        if not self.is_rotated():
            return cx, cy
        # 绕 (rx, ry) 旋转
        lx = cx - self.rx
        ly = cy - self.ry
        rad = math.radians(self.r)
        rx2 = lx * math.cos(rad) - ly * math.sin(rad)
        ry2 = lx * math.sin(rad) + ly * math.cos(rad)
        return rx2 + self.rx, ry2 + self.ry

    def corners_world(self) -> List[Tuple[float, float]]:
        """返回按键四个角的世界坐标（考虑旋转），用于碰撞检测"""
        corners_local = [
            (self.x, self.y),
            (self.x + self.w, self.y),
            (self.x + self.w, self.y + self.h),
            (self.x, self.y + self.h),
        ]
        if not self.is_rotated():
            return corners_local
        rad = math.radians(self.r)
        result = []
        for lx, ly in corners_local:
            dx, dy = lx - self.rx, ly - self.ry
            wx = dx * math.cos(rad) - dy * math.sin(rad) + self.rx
            wy = dx * math.sin(rad) + dy * math.cos(rad) + self.ry
            result.append((wx, wy))
        return result

    def get_keycode(self, layer: int) -> str:
        if layer < len(self.keycodes):
            return self.keycodes[layer]
        return "KC_TRNS"

    def set_keycode(self, layer: int, code: str):
        while len(self.keycodes) <= layer:
            self.keycodes.append("KC_TRNS")
        self.keycodes[layer] = code

    def matrix_str(self) -> str:
        if self.row >= 0 and self.col >= 0:
            return f"{self.row},{self.col}"
        return "—"

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "x": self.x, "y": self.y, "w": self.w, "h": self.h,
            "r": self.r, "rx": self.rx, "ry": self.ry,
            "row": self.row, "col": self.col,
            "label": self.label, "color": self.color,
            "keycodes": self.keycodes,
        }

    @staticmethod
    def from_dict(d: dict) -> "KeyModel":
        k = KeyModel()
        for f in ("uid","x","y","w","h","r","rx","ry","row","col","label","color","keycodes"):
            if f in d:
                setattr(k, f, d[f])
        return k


class KeyboardModel:
    """整个键盘的数据模型"""

    def __init__(self):
        self.keys: List[KeyModel] = []
        self._next_uid = 0

    def add_key(self, key: KeyModel) -> KeyModel:
        key.uid = self._next_uid
        self._next_uid += 1
        self.keys.append(key)
        return key

    def remove_key(self, uid: int):
        self.keys = [k for k in self.keys if k.uid != uid]

    def get_key(self, uid: int) -> Optional[KeyModel]:
        for k in self.keys:
            if k.uid == uid:
                return k
        return None

    def matrix_size(self) -> Tuple[int, int]:
        if not self.keys:
            return 0, 0
        rows = max((k.row for k in self.keys if k.row >= 0), default=-1) + 1
        cols = max((k.col for k in self.keys if k.col >= 0), default=-1) + 1
        return rows, cols

    def layer_count(self) -> int:
        if not self.keys:
            return 1
        return max((len(k.keycodes) for k in self.keys), default=1)

    def ensure_layers(self, n: int):
        for k in self.keys:
            while len(k.keycodes) < n:
                k.keycodes.append("KC_TRNS")

    def auto_assign_matrix(self, is_split: bool = False,
                            split_x: Optional[float] = None):
        """自动为所有键分配 row/col"""
        Y_TOL = 0.4

        if is_split and split_x is None:
            xs = sorted(k.physical_center()[0] for k in self.keys)
            split_x = (xs[0] + xs[-1]) / 2
            for i in range(1, len(xs)):
                if xs[i] - xs[i-1] > (split_x - xs[0]):
                    split_x = (xs[i] + xs[i-1]) / 2

        def group_rows(key_list):
            groups = []
            for k in sorted(key_list, key=lambda k: k.physical_center()[1]):
                placed = False
                for g in groups:
                    if abs(k.physical_center()[1] - g[0].physical_center()[1]) < Y_TOL:
                        g.append(k)
                        placed = True
                        break
                if not placed:
                    groups.append([k])
            return groups

        if is_split:
            left  = [k for k in self.keys if k.physical_center()[0] <  (split_x or 0)]
            right = [k for k in self.keys if k.physical_center()[0] >= (split_x or 0)]
            left_rows  = group_rows(left)
            right_rows = group_rows(right)
            for ri, grp in enumerate(left_rows):
                for ci, k in enumerate(sorted(grp, key=lambda k: k.physical_center()[0])):
                    k.row, k.col = ri, ci
            offset = len(left_rows)
            for ri, grp in enumerate(right_rows):
                for ci, k in enumerate(sorted(grp, key=lambda k: k.physical_center()[0])):
                    k.row, k.col = offset + ri, ci
        else:
            for ri, grp in enumerate(group_rows(self.keys)):
                for ci, k in enumerate(sorted(grp, key=lambda k: k.physical_center()[0])):
                    k.row, k.col = ri, ci

    def to_project_dict(self) -> dict:
        return {"keys": [k.to_dict() for k in self.keys],
                "next_uid": self._next_uid}

    def load_project_dict(self, d: dict):
        self.keys = [KeyModel.from_dict(kd) for kd in d.get("keys", [])]
        self._next_uid = d.get("next_uid", len(self.keys))
