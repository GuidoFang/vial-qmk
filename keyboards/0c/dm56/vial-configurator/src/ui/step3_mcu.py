"""
Step 3: 主控选择 + 矩阵引脚分配
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QComboBox, QFormLayout, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ..core.mcu_db import MCU_DATABASE
from ..core.project_state import ProjectState


class PinSelector(QWidget):
    """单行引脚选择器：标签 + 下拉框"""
    def __init__(self, label: str, pins: list, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(QLabel(label))
        self.cmb = QComboBox()
        self.cmb.addItem("— 未分配 —")
        self.cmb.addItems(pins)
        lay.addWidget(self.cmb)

    def value(self) -> str:
        t = self.cmb.currentText()
        return "" if t.startswith("—") else t

    def set_value(self, v: str):
        idx = self.cmb.findText(v)
        if idx >= 0:
            self.cmb.setCurrentIndex(idx)


class Step3Widget(QWidget):
    def __init__(self, state: ProjectState, parent=None):
        super().__init__(parent)
        self.state = state
        self.row_selectors: list[PinSelector] = []
        self.col_selectors: list[PinSelector] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Step 3 — 主控选择 & 矩阵引脚分配")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # 主控选择
        grp_mcu = QGroupBox("主控（MCU）")
        mcu_lay = QFormLayout(grp_mcu)
        self.cmb_mcu = QComboBox()
        for key, mcu in MCU_DATABASE.items():
            self.cmb_mcu.addItem(mcu.name, key)
        self.cmb_mcu.currentIndexChanged.connect(self._on_mcu_changed)
        mcu_lay.addRow("主控型号：", self.cmb_mcu)
        self.lbl_mcu_note = QLabel("")
        self.lbl_mcu_note.setWordWrap(True)
        mcu_lay.addRow("说明：", self.lbl_mcu_note)
        layout.addWidget(grp_mcu)

        # 引脚分配区（可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pin_container = QWidget()
        self.pin_layout = QVBoxLayout(self.pin_container)
        scroll.setWidget(self.pin_container)
        layout.addWidget(scroll, 1)

        self._on_mcu_changed()

    def _on_mcu_changed(self):
        key = self.cmb_mcu.currentData()
        mcu = MCU_DATABASE.get(key)
        if not mcu:
            return
        self.state.mcu_key = key
        self.lbl_mcu_note.setText(mcu.notes)
        self._rebuild_pin_selectors(mcu.pin_names())

    def _rebuild_pin_selectors(self, pins: list):
        # 清空旧控件
        while self.pin_layout.count():
            item = self.pin_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.row_selectors.clear()
        self.col_selectors.clear()

        rows = self.state.matrix_rows
        cols = self.state.matrix_cols
        if self.state.is_split:
            rows = rows // 2  # 每半边物理行数

        # 行引脚
        grp_row = QGroupBox(f"行引脚（ROWS × {rows}）")
        row_lay = QVBoxLayout(grp_row)
        for i in range(rows):
            sel = PinSelector(f"ROW {i}：", pins)
            # 还原上次选择
            if i < len(self.state.row_pins):
                sel.set_value(self.state.row_pins[i])
            row_lay.addWidget(sel)
            self.row_selectors.append(sel)
        self.pin_layout.addWidget(grp_row)

        # 列引脚
        grp_col = QGroupBox(f"列引脚（COLS × {cols}）")
        col_lay = QVBoxLayout(grp_col)
        for i in range(cols):
            sel = PinSelector(f"COL {i}：", pins)
            if i < len(self.state.col_pins):
                sel.set_value(self.state.col_pins[i])
            col_lay.addWidget(sel)
            self.col_selectors.append(sel)
        self.pin_layout.addWidget(grp_col)
        self.pin_layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        self._on_mcu_changed()

    def validate(self) -> bool:
        row_pins = [s.value() for s in self.row_selectors]
        col_pins = [s.value() for s in self.col_selectors]

        missing_rows = [i for i, p in enumerate(row_pins) if not p]
        missing_cols = [i for i, p in enumerate(col_pins) if not p]
        if missing_rows or missing_cols:
            msg = ""
            if missing_rows:
                msg += f"以下行引脚未分配：ROW {missing_rows}\n"
            if missing_cols:
                msg += f"以下列引脚未分配：COL {missing_cols}\n"
            QMessageBox.warning(self, "引脚未分配", msg)
            return False

        # 检查重复
        all_pins = row_pins + col_pins
        if len(set(all_pins)) < len(all_pins):
            QMessageBox.warning(self, "引脚冲突", "存在重复分配的引脚，请检查。")
            return False

        self.state.row_pins = row_pins
        self.state.col_pins = col_pins
        return True
