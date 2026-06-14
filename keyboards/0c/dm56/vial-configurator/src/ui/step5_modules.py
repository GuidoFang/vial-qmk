"""
Step 5: 功能模块选择 + 引脚分配
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QCheckBox, QComboBox, QSpinBox, QFormLayout, QScrollArea,
    QFrame, QPushButton, QMessageBox
)
from PyQt6.QtGui import QFont
from ..core.mcu_db import MCU_DATABASE, FEATURE_MODULES
from ..core.project_state import ProjectState


class Step5Widget(QWidget):
    def __init__(self, state: ProjectState, parent=None):
        super().__init__(parent)
        self.state = state
        self.module_widgets: dict = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("Step 5 — 功能模块选择")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self.mod_layout = QVBoxLayout(container)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self._build_modules()

    def _build_modules(self):
        while self.mod_layout.count():
            item = self.mod_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.module_widgets.clear()

        mcu = MCU_DATABASE.get(self.state.mcu_key)
        pins = mcu.pin_names() if mcu else []

        for mod in FEATURE_MODULES:
            key = mod["key"]
            grp = QGroupBox()
            grp_lay = QVBoxLayout(grp)

            # 标题行：复选框
            chk = QCheckBox(f"  {mod['name']}")
            chk.setChecked(self.state.features.get(key, mod["default_enabled"]))
            chk.setFont(QFont("", 10))
            grp_lay.addWidget(chk)

            # 引脚选择子区
            sub_widget = QWidget()
            sub_lay = QFormLayout(sub_widget)
            pin_combos = {}

            if mod["pins_needed"]:
                for pin_key in mod["pins_needed"]:
                    label = mod.get("pin_labels", {}).get(pin_key, pin_key)
                    cmb = QComboBox()
                    cmb.addItem("— 未分配 —")
                    cmb.addItems(pins)
                    saved = self.state.module_pins.get(key, {}).get(pin_key, "")
                    if saved:
                        idx = cmb.findText(saved)
                        if idx >= 0:
                            cmb.setCurrentIndex(idx)
                    sub_lay.addRow(f"  {label}：", cmb)
                    pin_combos[pin_key] = cmb

            # RGB LED 数量
            spin_led = None
            if key in ("RGBLIGHT_ENABLE", "RGB_MATRIX_ENABLE"):
                spin_led = QSpinBox()
                spin_led.setRange(1, 512)
                spin_led.setValue(self.state.rgb_led_count or 1)
                sub_lay.addRow("  LED 数量：", spin_led)

            grp_lay.addWidget(sub_widget)

            # 切换可见
            def make_toggle(sw, ck):
                ck.toggled.connect(lambda checked: sw.setVisible(checked))
            make_toggle(sub_widget, chk)
            sub_widget.setVisible(chk.isChecked())

            self.mod_layout.addWidget(grp)
            self.module_widgets[key] = {
                "chk": chk, "pin_combos": pin_combos, "spin_led": spin_led
            }

        self.mod_layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        self._build_modules()

    def validate(self) -> bool:
        features = {}
        module_pins = {}
        rgb_count = 0

        for key, w in self.module_widgets.items():
            enabled = w["chk"].isChecked()
            features[key] = enabled
            if enabled and w["pin_combos"]:
                pins = {}
                for pin_key, cmb in w["pin_combos"].items():
                    val = cmb.currentText()
                    if val.startswith("—"):
                        val = ""
                    pins[pin_key] = val
                module_pins[key] = pins
            if enabled and w["spin_led"]:
                rgb_count = w["spin_led"].value()

        self.state.features = features
        self.state.module_pins = module_pins
        self.state.rgb_led_count = rgb_count
        return True
