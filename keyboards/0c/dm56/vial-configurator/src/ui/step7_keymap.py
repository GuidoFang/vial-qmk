"""
Step 7: Keymap 编辑器（简化版：层 + 键值列表）
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QLineEdit, QFormLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ..core.project_state import ProjectState

# 常用预设键值
DEFAULT_LAYER0 = [
    "KC_ESC","KC_1","KC_2","KC_3","KC_4","KC_5",
    "KC_TAB","KC_Q","KC_W","KC_E","KC_R","KC_T",
    "KC_LSFT","KC_A","KC_S","KC_D","KC_F","KC_G",
    "KC_LCTL","KC_Z","KC_X","KC_C","KC_V","KC_B",
    "KC_LBRC","KC_RBRC","MO(1)","KC_SPC","KC_TAB","KC_HOME",
    "KC_BSPC","KC_GRV",
    "KC_6","KC_7","KC_8","KC_9","KC_0","KC_BSPC",
    "KC_Y","KC_U","KC_I","KC_O","KC_P","KC_MINS",
    "KC_H","KC_J","KC_K","KC_L","KC_SCLN","KC_QUOT",
    "KC_N","KC_M","KC_COMM","KC_DOT","KC_SLSH","KC_BSLS",
    "KC_PLUS","KC_EQL","KC_ENT","MO(2)","KC_END","KC_DEL",
    "KC_LGUI","KC_LALT",
]


class Step7Widget(QWidget):
    def __init__(self, state: ProjectState, parent=None):
        super().__init__(parent)
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Step 7 — Keymap 编辑")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(
            "为每一层的每个按键设置键值。键值使用 QMK 键码（如 KC_A、MO(1)、LT(1,KC_SPC)）。\n"
            "KC_TRNS 表示透明（穿透到下层），KC_NO 表示空键。"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 层标签页
        self.tab = QTabWidget()
        layout.addWidget(self.tab, 1)

        # 工具栏
        btn_row = QHBoxLayout()
        btn_add_layer = QPushButton("+ 添加层")
        btn_add_layer.clicked.connect(self._add_layer)
        btn_del_layer = QPushButton("- 删除末层")
        btn_del_layer.clicked.connect(self._del_layer)
        btn_fill = QPushButton("当前层填充 KC_TRNS")
        btn_fill.clicked.connect(self._fill_trns)
        btn_row.addWidget(btn_add_layer)
        btn_row.addWidget(btn_del_layer)
        btn_row.addWidget(btn_fill)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def showEvent(self, event):
        super().showEvent(event)
        self._rebuild_tabs()

    def _rebuild_tabs(self):
        self.tab.clear()
        key_count = len(self.state.keys)
        layer_count = self.state.layer_count

        # 确保 keymaps 有足够层数
        while len(self.state.keymaps) < layer_count:
            if len(self.state.keymaps) == 0:
                # Layer 0：尽量用预设填充
                layer = DEFAULT_LAYER0[:key_count]
                while len(layer) < key_count:
                    layer.append("KC_TRNS")
            else:
                layer = ["KC_TRNS"] * key_count
            self.state.keymaps.append(layer)

        for layer_idx in range(layer_count):
            table = self._make_table(layer_idx)
            self.tab.addTab(table, f"Layer {layer_idx}")

    def _make_table(self, layer_idx: int) -> QTableWidget:
        keys = self.state.keys
        layer = self.state.keymaps[layer_idx]

        table = QTableWidget(len(keys), 3)
        table.setHorizontalHeaderLabels(["#", "位置 (row,col)", "键值"])
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.setProperty("layer_idx", layer_idx)

        for i, key in enumerate(keys):
            table.setItem(i, 0, QTableWidgetItem(str(i)))
            table.setItem(i, 1, QTableWidgetItem(f"{key.row},{key.col}  {key.label}"))
            kc = layer[i] if i < len(layer) else "KC_TRNS"
            table.setItem(i, 2, QTableWidgetItem(kc))

        table.itemChanged.connect(lambda item: self._on_item_changed(item, layer_idx))
        return table

    def _on_item_changed(self, item: QTableWidgetItem, layer_idx: int):
        if item.column() != 2:
            return
        row = item.row()
        if layer_idx < len(self.state.keymaps) and row < len(self.state.keymaps[layer_idx]):
            self.state.keymaps[layer_idx][row] = item.text()

    def _add_layer(self):
        key_count = len(self.state.keys)
        self.state.keymaps.append(["KC_TRNS"] * key_count)
        self.state.layer_count = len(self.state.keymaps)
        self._rebuild_tabs()

    def _del_layer(self):
        if len(self.state.keymaps) > 1:
            self.state.keymaps.pop()
            self.state.layer_count = len(self.state.keymaps)
            self._rebuild_tabs()

    def _fill_trns(self):
        idx = self.tab.currentIndex()
        if 0 <= idx < len(self.state.keymaps):
            key_count = len(self.state.keys)
            self.state.keymaps[idx] = ["KC_TRNS"] * key_count
            self._rebuild_tabs()
            self.tab.setCurrentIndex(idx)

    def validate(self) -> bool:
        # 从 table 控件同步数据
        for i in range(self.tab.count()):
            table = self.tab.widget(i)
            layer_idx = i
            if layer_idx >= len(self.state.keymaps):
                continue
            for row in range(table.rowCount()):
                item = table.item(row, 2)
                if item and layer_idx < len(self.state.keymaps) and row < len(self.state.keymaps[layer_idx]):
                    self.state.keymaps[layer_idx][row] = item.text()
        return True
