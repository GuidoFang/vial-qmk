"""
Step 4: 分体通信配置
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QGroupBox,
    QComboBox, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtGui import QFont
from ..core.mcu_db import MCU_DATABASE, SPLIT_SERIAL_PRESETS
from ..core.project_state import ProjectState


class Step4Widget(QWidget):
    def __init__(self, state: ProjectState, parent=None):
        super().__init__(parent)
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Step 4 — 分体通信配置")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        self.lbl_skip = QLabel("（当前为整体键盘，本步骤跳过）")
        layout.addWidget(self.lbl_skip)

        # 主从设置
        grp_master = QGroupBox("USB 主从设置")
        m_lay = QFormLayout(grp_master)
        self.cmb_master = QComboBox()
        self.cmb_master.addItems(["left（左侧接 USB）", "right（右侧接 USB）", "自动检测（SPLIT_USB_DETECT）"])
        m_lay.addRow("主控侧：", self.cmb_master)
        layout.addWidget(grp_master)

        # 通信协议
        grp_serial = QGroupBox("分体通信协议")
        s_lay = QFormLayout(grp_serial)

        self.cmb_preset = QComboBox()
        self.cmb_preset.currentIndexChanged.connect(self._on_preset_changed)
        s_lay.addRow("推荐预设：", self.cmb_preset)

        self.cmb_driver = QComboBox()
        self.cmb_driver.addItems(["vendor", "usart", "bitbang"])
        s_lay.addRow("串口驱动：", self.cmb_driver)

        self.cmb_tx = QComboBox()
        s_lay.addRow("TX 引脚：", self.cmb_tx)

        self.cmb_rx = QComboBox()
        s_lay.addRow("RX 引脚：", self.cmb_rx)

        layout.addWidget(grp_serial)
        layout.addStretch()

        self.grp_master = grp_master
        self.grp_serial = grp_serial

    def showEvent(self, event):
        super().showEvent(event)
        is_split = self.state.is_split
        self.lbl_skip.setVisible(not is_split)
        self.grp_master.setVisible(is_split)
        self.grp_serial.setVisible(is_split)

        if is_split:
            mcu = MCU_DATABASE.get(self.state.mcu_key)
            pins = mcu.pin_names() if mcu else []

            self.cmb_tx.clear()
            self.cmb_rx.clear()
            self.cmb_tx.addItems(pins)
            self.cmb_rx.addItems(pins)

            # 加载预设
            self.cmb_preset.blockSignals(True)
            self.cmb_preset.clear()
            presets = SPLIT_SERIAL_PRESETS.get(self.state.mcu_key, [])
            for p in presets:
                self.cmb_preset.addItem(p["desc"], p)
            self.cmb_preset.blockSignals(False)
            if presets:
                self._on_preset_changed(0)

    def _on_preset_changed(self, idx):
        preset = self.cmb_preset.currentData()
        if not preset:
            return
        self.cmb_driver.setCurrentText(preset.get("driver", "vendor"))
        tx_idx = self.cmb_tx.findText(preset.get("tx", ""))
        rx_idx = self.cmb_rx.findText(preset.get("rx", ""))
        if tx_idx >= 0:
            self.cmb_tx.setCurrentIndex(tx_idx)
        if rx_idx >= 0:
            self.cmb_rx.setCurrentIndex(rx_idx)

    def validate(self) -> bool:
        if not self.state.is_split:
            return True
        master_text = self.cmb_master.currentText()
        if "right" in master_text:
            self.state.master_side = "right"
        else:
            self.state.master_side = "left"
        self.state.serial_driver = self.cmb_driver.currentText()
        self.state.serial_tx = self.cmb_tx.currentText()
        self.state.serial_rx = self.cmb_rx.currentText()

        if self.state.serial_tx == self.state.serial_rx:
            QMessageBox.warning(self, "引脚冲突", "TX 和 RX 引脚不能相同。")
            return False
        return True
