"""
Step 2: Matrix 矩阵设计页
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QRadioButton, QButtonGroup, QSpinBox, QComboBox,
    QCheckBox, QMessageBox, QDoubleSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ..core.kle_parser import KLEParser
from ..core.project_state import ProjectState


class Step2Widget(QWidget):
    def __init__(self, state: ProjectState, parent=None):
        super().__init__(parent)
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Step 2 — Matrix 矩阵设计")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # 分体键盘选项
        grp_split = QGroupBox("键盘类型")
        split_layout = QVBoxLayout(grp_split)
        self.rb_single = QRadioButton("整体键盘（单 PCB）")
        self.rb_split  = QRadioButton("分体键盘（左右两片 PCB）")
        self.rb_single.setChecked(True)
        split_layout.addWidget(self.rb_single)
        split_layout.addWidget(self.rb_split)
        self.rb_split.toggled.connect(self._on_split_toggled)
        layout.addWidget(grp_split)

        # 分割线配置（分体时显示）
        self.grp_split_cfg = QGroupBox("分体分割线")
        sc_layout = QFormLayout(self.grp_split_cfg)
        self.spin_split_x = QDoubleSpinBox()
        self.spin_split_x.setRange(0, 100)
        self.spin_split_x.setDecimals(1)
        self.spin_split_x.setValue(8.5)
        self.spin_split_x.setSuffix("  （键单位，自动推断可留默认）")
        sc_layout.addRow("左右分割 X 坐标：", self.spin_split_x)
        self.grp_split_cfg.setVisible(False)
        layout.addWidget(self.grp_split_cfg)

        # 矩阵参数
        grp_matrix = QGroupBox("矩阵参数（自动推断，可手动调整）")
        m_layout = QFormLayout(grp_matrix)

        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 32)
        m_layout.addRow("总行数（MATRIX_ROWS）：", self.spin_rows)

        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 32)
        m_layout.addRow("总列数（MATRIX_COLS）：", self.spin_cols)

        self.cmb_diode = QComboBox()
        self.cmb_diode.addItems(["COL2ROW", "ROW2COL"])
        m_layout.addRow("二极管方向：", self.cmb_diode)

        layout.addWidget(grp_matrix)

        self.lbl_info = QLabel("")
        self.lbl_info.setWordWrap(True)
        layout.addWidget(self.lbl_info)
        layout.addStretch()

    def _on_split_toggled(self, checked):
        self.grp_split_cfg.setVisible(checked)

    def showEvent(self, event):
        super().showEvent(event)
        self._auto_detect()

    def _auto_detect(self):
        """进入本页时自动推断矩阵尺寸"""
        if not self.state.keys:
            return
        parser = KLEParser()
        is_split = self.rb_split.isChecked()
        split_x = self.spin_split_x.value() if is_split else None
        keys = parser.auto_assign_matrix(self.state.keys, is_split, split_x)
        rows, cols = parser.get_matrix_size(keys)
        self.spin_rows.setValue(rows)
        self.spin_cols.setValue(cols)
        info = f"自动推断：{rows} 行 × {cols} 列，共 {len(keys)} 个有效按键位。"
        if is_split:
            left = sum(1 for k in keys if k.center_x() < (split_x or 0))
            info += f"\n  左半：{left} 键，右半：{len(keys)-left} 键。"
        self.lbl_info.setText(info)

    def validate(self) -> bool:
        is_split = self.rb_split.isChecked()
        split_x  = self.spin_split_x.value() if is_split else None

        parser = KLEParser()
        self.state.keys = parser.auto_assign_matrix(
            self.state.keys, is_split, split_x
        )
        self.state.is_split = is_split
        self.state.split_x_threshold = split_x or 0.0
        self.state.matrix_rows = self.spin_rows.value()
        self.state.matrix_cols = self.spin_cols.value()
        self.state.diode_direction = self.cmb_diode.currentText()
        return True
