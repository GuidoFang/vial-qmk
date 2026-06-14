"""
Step 6: Vial 专属配置
"""
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QGroupBox,
    QLineEdit, QSpinBox, QPushButton, QHBoxLayout
)
from PyQt6.QtGui import QFont
from ..core.project_state import ProjectState


class Step6Widget(QWidget):
    def __init__(self, state: ProjectState, parent=None):
        super().__init__(parent)
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Step 6 — Vial 专属配置")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # 基本信息
        grp_info = QGroupBox("键盘基本信息")
        info_lay = QFormLayout(grp_info)

        self.txt_name = QLineEdit("my_keyboard")
        info_lay.addRow("键盘名称（英文/数字/下划线）：", self.txt_name)

        self.txt_mfr = QLineEdit("Custom")
        info_lay.addRow("制造商：", self.txt_mfr)

        self.txt_vid = QLineEdit("0x6464")
        info_lay.addRow("USB VID（厂商 ID）：", self.txt_vid)

        self.txt_pid = QLineEdit("0x0001")
        info_lay.addRow("USB PID（产品 ID）：", self.txt_pid)

        layout.addWidget(grp_info)

        # Vial UID
        grp_uid = QGroupBox("Vial UID（唯一标识，勿与他人重复）")
        uid_lay = QHBoxLayout(grp_uid)
        self.txt_uid = QLineEdit()
        self.txt_uid.setReadOnly(True)
        self.txt_uid.setFont(QFont("Consolas", 10))
        uid_lay.addWidget(self.txt_uid)
        btn_gen = QPushButton("🔀 重新生成")
        btn_gen.clicked.connect(self._gen_uid)
        uid_lay.addWidget(btn_gen)
        layout.addWidget(grp_uid)

        # Vial 参数
        grp_vial = QGroupBox("Vial 参数")
        vial_lay = QFormLayout(grp_vial)

        self.spin_layers = QSpinBox()
        self.spin_layers.setRange(2, 32)
        self.spin_layers.setValue(5)
        vial_lay.addRow("层数（DYNAMIC_KEYMAP_LAYER_COUNT）：", self.spin_layers)

        self.spin_debounce = QSpinBox()
        self.spin_debounce.setRange(1, 30)
        self.spin_debounce.setValue(5)
        self.spin_debounce.setSuffix(" ms")
        vial_lay.addRow("防抖时间（DEBOUNCE）：", self.spin_debounce)

        self.txt_unlock_rows = QLineEdit("0, 0")
        vial_lay.addRow("解锁组合行（UNLOCK_COMBO_ROWS）：", self.txt_unlock_rows)

        self.txt_unlock_cols = QLineEdit("0, 1")
        vial_lay.addRow("解锁组合列（UNLOCK_COMBO_COLS）：", self.txt_unlock_cols)

        layout.addWidget(grp_vial)
        layout.addStretch()

        self._gen_uid()

    def _gen_uid(self):
        uid = [random.randint(0, 255) for _ in range(8)]
        self.state.vial_uid = uid
        self.txt_uid.setText("{" + ", ".join(f"0x{b:02X}" for b in uid) + "}")

    def validate(self) -> bool:
        name = self.txt_name.text().strip()
        if not name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "键盘名称不能为空。")
            return False
        self.state.keyboard_name = name
        self.state.manufacturer = self.txt_mfr.text().strip() or "Custom"
        self.state.vid = self.txt_vid.text().strip() or "0x6464"
        self.state.pid = self.txt_pid.text().strip() or "0x0001"
        self.state.layer_count = self.spin_layers.value()
        self.state.debounce = self.spin_debounce.value()
        try:
            self.state.unlock_rows = [int(x.strip()) for x in self.txt_unlock_rows.text().split(",")]
            self.state.unlock_cols = [int(x.strip()) for x in self.txt_unlock_cols.text().split(",")]
        except Exception:
            self.state.unlock_rows = [0, 0]
            self.state.unlock_cols = [0, 1]
        return True
