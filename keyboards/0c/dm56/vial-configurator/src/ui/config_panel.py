"""
配置面板：主控 + 分体 + 模块 + Vial
整合 Step 3-7 的所有配置项到一个页面
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QComboBox, QSpinBox, QFormLayout, QScrollArea, QFrame,
    QPushButton, QLineEdit, QCheckBox, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..core.key_model import KeyboardModel
from ..core.firmware_generator import ProjectConfig
from ..core.mcu_db import MCU_DATABASE, SPLIT_SERIAL_PRESETS, FEATURE_MODULES


class ConfigPanel(QWidget):
    """配置面板：主控/引脚/分体/模块/Vial 一站式配置"""

    def __init__(self, kb: KeyboardModel, cfg: ProjectConfig, parent=None):
        super().__init__(parent)
        self.kb = kb
        self.cfg = cfg
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_basic_tab(), "基本信息")
        self.tabs.addTab(self._build_mcu_tab(), "主控 & 引脚")
        self.tabs.addTab(self._build_split_tab(), "分体通信")
        self.tabs.addTab(self._build_modules_tab(), "功能模块")
        self.tabs.addTab(self._build_vial_tab(), "Vial 配置")
        layout.addWidget(self.tabs)

    # ── Tab 1: 基本信息 ────────────────────────────────────────
    def _build_basic_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        grp = QGroupBox("键盘基本信息")
        form = QFormLayout(grp)

        self.txt_name = QLineEdit(self.cfg.keyboard_name)
        form.addRow("键盘名称：", self.txt_name)

        self.txt_mfr = QLineEdit(self.cfg.manufacturer)
        form.addRow("制造商：", self.txt_mfr)

        self.txt_vid = QLineEdit(self.cfg.vid)
        form.addRow("USB VID：", self.txt_vid)

        self.txt_pid = QLineEdit(self.cfg.pid)
        form.addRow("USB PID：", self.txt_pid)

        layout.addWidget(grp)
        layout.addStretch()
        return w

    # ── Tab 2: 主控 & 引脚 ──────────────────────────────────────
    def _build_mcu_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

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
        self.lbl_mcu_note.setStyleSheet("color:#666;")
        mcu_lay.addRow("说明：", self.lbl_mcu_note)

        # 自动分配按钮
        btn_auto_assign = QPushButton("⚡ 自动分配引脚")
        btn_auto_assign.clicked.connect(self._auto_assign_pins)
        mcu_lay.addRow("", btn_auto_assign)

        layout.addWidget(grp_mcu)

        # 引脚分配（滚动区）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pin_container = QWidget()
        self.pin_layout = QVBoxLayout(self.pin_container)
        scroll.setWidget(self.pin_container)
        layout.addWidget(scroll, 1)

        self._on_mcu_changed()
        return w

    def _on_mcu_changed(self):
        key = self.cmb_mcu.currentData()
        mcu = MCU_DATABASE.get(key)
        if not mcu:
            return
        self.cfg.mcu_key = key
        self.cfg.processor = mcu.processor
        self.cfg.bootloader = mcu.bootloader
        self.lbl_mcu_note.setText(mcu.notes)
        self._rebuild_pin_selectors(mcu.pin_names())

    def _rebuild_pin_selectors(self, pins: list):
        while self.pin_layout.count():
            item = self.pin_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rows, cols = self.kb.matrix_size()
        is_asymmetric = self.cfg.is_split and hasattr(self, 'chk_asymmetric') and self.chk_asymmetric.isChecked()

        if self.cfg.is_split and not is_asymmetric:
            rows = rows // 2

        # 获取保留引脚（通信引脚）
        reserved_pins = self._get_reserved_pins()

        # 行引脚
        grp_row = QGroupBox(f"行引脚（ROWS × {rows}）")
        row_lay = QVBoxLayout(grp_row)
        self.row_combos = []
        for i in range(rows):
            cmb = QComboBox()
            cmb.addItem("— 未分配 —")
            cmb.addItems(pins)
            if i < len(self.cfg.row_pins):
                idx = cmb.findText(self.cfg.row_pins[i])
                if idx >= 0:
                    cmb.setCurrentIndex(idx)
            # 添加引脚冲突检测
            cmb.currentIndexChanged.connect(lambda idx, c=cmb: self._check_pin_conflict(c))
            row_lay.addWidget(QLabel(f"ROW {i}："))
            row_lay.addWidget(cmb)
            self.row_combos.append(cmb)
        self.pin_layout.addWidget(grp_row)

        # 列引脚
        grp_col = QGroupBox(f"列引脚（COLS × {cols}）")
        col_lay = QVBoxLayout(grp_col)
        self.col_combos = []
        for i in range(cols):
            cmb = QComboBox()
            cmb.addItem("— 未分配 —")
            cmb.addItems(pins)
            if i < len(self.cfg.col_pins):
                idx = cmb.findText(self.cfg.col_pins[i])
                if idx >= 0:
                    cmb.setCurrentIndex(idx)
            # 添加引脚冲突检测
            cmb.currentIndexChanged.connect(lambda idx, c=cmb: self._check_pin_conflict(c))
            col_lay.addWidget(QLabel(f"COL {i}："))
            col_lay.addWidget(cmb)
            self.col_combos.append(cmb)
        self.pin_layout.addWidget(grp_col)

        # 如果是不对称分体，添加右手引脚配置
        if is_asymmetric:
            grp_row_r = QGroupBox(f"右手行引脚（ROWS × {rows}）")
            row_r_lay = QVBoxLayout(grp_row_r)
            self.row_combos_right = []
            for i in range(rows):
                cmb = QComboBox()
                cmb.addItem("— 未分配 —")
                cmb.addItems(pins)
                if hasattr(self.cfg, 'row_pins_right') and i < len(self.cfg.row_pins_right):
                    idx = cmb.findText(self.cfg.row_pins_right[i])
                    if idx >= 0:
                        cmb.setCurrentIndex(idx)
                cmb.currentIndexChanged.connect(lambda idx, c=cmb: self._check_pin_conflict(c))
                row_r_lay.addWidget(QLabel(f"ROW {i}："))
                row_r_lay.addWidget(cmb)
                self.row_combos_right.append(cmb)
            self.pin_layout.addWidget(grp_row_r)

            grp_col_r = QGroupBox(f"右手列引脚（COLS × {cols}）")
            col_r_lay = QVBoxLayout(grp_col_r)
            self.col_combos_right = []
            for i in range(cols):
                cmb = QComboBox()
                cmb.addItem("— 未分配 —")
                cmb.addItems(pins)
                if hasattr(self.cfg, 'col_pins_right') and i < len(self.cfg.col_pins_right):
                    idx = cmb.findText(self.cfg.col_pins_right[i])
                    if idx >= 0:
                        cmb.setCurrentIndex(idx)
                cmb.currentIndexChanged.connect(lambda idx, c=cmb: self._check_pin_conflict(c))
                col_r_lay.addWidget(QLabel(f"COL {i}："))
                col_r_lay.addWidget(cmb)
                self.col_combos_right.append(cmb)
            self.pin_layout.addWidget(grp_col_r)

        self.pin_layout.addStretch()

    def _auto_assign_pins(self):
        """自动按顺序分配引脚，避开通信引脚"""
        mcu = MCU_DATABASE.get(self.cfg.mcu_key)
        if not mcu:
            return

        all_pins = mcu.pin_names()
        rows, cols = self.kb.matrix_size()
        is_asymmetric = self.cfg.is_split and hasattr(self, 'chk_asymmetric') and self.chk_asymmetric.isChecked()

        if self.cfg.is_split and not is_asymmetric:
            rows = rows // 2

        # 获取已占用的引脚（通信引脚）
        reserved_pins = self._get_reserved_pins()

        # 过滤掉保留引脚
        available_pins = [p for p in all_pins if p not in reserved_pins]

        # 检查引脚是否足够
        needed = rows + cols
        if is_asymmetric:
            needed = needed * 2  # 左右手各需要一套引脚

        if len(available_pins) < needed:
            QMessageBox.warning(
                self, "引脚不足",
                f"当前主控可用引脚：{len(all_pins)} 个\n"
                f"保留引脚（通信）：{len(reserved_pins)} 个\n"
                f"可用引脚：{len(available_pins)} 个\n"
                f"需要引脚：{needed} 个（{rows}行 + {cols}列" +
                (" × 2侧" if is_asymmetric else "") + "）\n\n"
                "请减少矩阵尺寸或更换主控。"
            )
            return

        # 自动分配：前 N 个给左手行，后 M 个给左手列
        for i, cmb in enumerate(self.row_combos):
            if i < len(available_pins):
                idx = cmb.findText(available_pins[i])
                if idx >= 0:
                    cmb.setCurrentIndex(idx)

        for i, cmb in enumerate(self.col_combos):
            pin_idx = rows + i
            if pin_idx < len(available_pins):
                idx = cmb.findText(available_pins[pin_idx])
                if idx >= 0:
                    cmb.setCurrentIndex(idx)

        msg = f"已自动分配左手引脚：\n行引脚：{available_pins[:rows]}\n列引脚：{available_pins[rows:rows+cols]}"

        # 如果是不对称分体，分配右手引脚
        if is_asymmetric and hasattr(self, 'row_combos_right'):
            offset = rows + cols
            for i, cmb in enumerate(self.row_combos_right):
                pin_idx = offset + i
                if pin_idx < len(available_pins):
                    idx = cmb.findText(available_pins[pin_idx])
                    if idx >= 0:
                        cmb.setCurrentIndex(idx)

            for i, cmb in enumerate(self.col_combos_right):
                pin_idx = offset + rows + i
                if pin_idx < len(available_pins):
                    idx = cmb.findText(available_pins[pin_idx])
                    if idx >= 0:
                        cmb.setCurrentIndex(idx)

            msg += f"\n\n已自动分配右手引脚：\n行引脚：{available_pins[offset:offset+rows]}\n列引脚：{available_pins[offset+rows:offset+rows+cols]}"

        if reserved_pins:
            msg += f"\n\n已避开通信引脚：{list(reserved_pins)}"

        QMessageBox.information(self, "自动分配完成", msg)

    def _get_reserved_pins(self) -> set:
        """获取保留引脚（通信引脚 + 模块引脚）"""
        reserved_pins = set()
        if self.cfg.is_split:
            # 从分体通信预设获取默认通信引脚
            from ..core.mcu_db import SPLIT_SERIAL_PRESETS
            presets = SPLIT_SERIAL_PRESETS.get(self.cfg.mcu_key, [])
            if presets:
                preset = presets[0]  # 使用第一个推荐预设
                tx = preset.get("tx", "")
                rx = preset.get("rx", "")
                if tx:
                    reserved_pins.add(tx)
                if rx:
                    reserved_pins.add(rx)
        return reserved_pins

    def _check_pin_conflict(self, combo: QComboBox):
        """检查引脚冲突"""
        pin = combo.currentText()
        if pin.startswith("—"):
            combo.setStyleSheet("")
            return

        # 收集所有已分配的引脚
        all_assigned = []
        for cmb in self.row_combos:
            p = cmb.currentText()
            if not p.startswith("—"):
                all_assigned.append(p)
        for cmb in self.col_combos:
            p = cmb.currentText()
            if not p.startswith("—"):
                all_assigned.append(p)

        # 如果是不对称分体，也检查右手引脚
        if hasattr(self, 'row_combos_right'):
            for cmb in self.row_combos_right:
                p = cmb.currentText()
                if not p.startswith("—"):
                    all_assigned.append(p)
            for cmb in self.col_combos_right:
                p = cmb.currentText()
                if not p.startswith("—"):
                    all_assigned.append(p)

        # 检查通信引脚冲突
        reserved_pins = self._get_reserved_pins()
        if pin in reserved_pins:
            combo.setStyleSheet("border: 2px solid red;")
            QMessageBox.warning(
                self, "引脚冲突",
                f"引脚 {pin} 已被分体通信占用！\n\n"
                f"保留引脚：{list(reserved_pins)}\n\n"
                "请选择其他引脚。"
            )
            return

        # 检查重复分配
        if all_assigned.count(pin) > 1:
            combo.setStyleSheet("border: 2px solid orange;")
            QMessageBox.warning(
                self, "引脚重复",
                f"引脚 {pin} 已被多次分配！\n\n"
                "请检查矩阵引脚配置。"
            )
            return

        combo.setStyleSheet("")

    # ── Tab 3: 分体通信 ────────────────────────────────────────
    def _build_split_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        self.lbl_split_skip = QLabel("（当前为整体键盘，本页跳过）")
        layout.addWidget(self.lbl_split_skip)

        grp_master = QGroupBox("USB 主从设置")
        m_lay = QFormLayout(grp_master)
        self.cmb_master = QComboBox()
        self.cmb_master.addItems(["left（左侧接 USB）", "right（右侧接 USB）"])
        m_lay.addRow("主控侧：", self.cmb_master)

        self.chk_asymmetric = QCheckBox("左右手不对称（需分别配置引脚）")
        self.chk_asymmetric.toggled.connect(self._on_asymmetric_changed)
        m_lay.addRow("", self.chk_asymmetric)
        layout.addWidget(grp_master)

        grp_serial = QGroupBox("分体通信协议")
        s_lay = QFormLayout(grp_serial)
        self.cmb_serial_preset = QComboBox()
        self.cmb_serial_preset.currentIndexChanged.connect(self._on_serial_preset)
        s_lay.addRow("推荐预设：", self.cmb_serial_preset)
        self.cmb_serial_driver = QComboBox()
        self.cmb_serial_driver.addItems(["vendor", "usart", "bitbang"])
        s_lay.addRow("串口驱动：", self.cmb_serial_driver)
        self.cmb_serial_tx = QComboBox()
        s_lay.addRow("TX 引脚：", self.cmb_serial_tx)
        self.cmb_serial_rx = QComboBox()
        s_lay.addRow("RX 引脚：", self.cmb_serial_rx)

        self.lbl_serial_note = QLabel("")
        self.lbl_serial_note.setWordWrap(True)
        self.lbl_serial_note.setStyleSheet("color:#666; font-size:9px;")
        s_lay.addRow("说明：", self.lbl_serial_note)

        layout.addWidget(grp_serial)

        layout.addStretch()
        self.grp_split_master = grp_master
        self.grp_split_serial = grp_serial
        return w

    def _on_asymmetric_changed(self, checked):
        """处理对称/不对称切换"""
        if checked:
            QMessageBox.information(
                self, "不对称分体键盘",
                "不对称分体键盘需要在「主控 & 引脚」标签页中分别配置左右手引脚。\n\n"
                "导出时将生成两个独立的固件文件夹：\n"
                "- keyboard_name_left/\n"
                "- keyboard_name_right/"
            )
        # 触发引脚页面重新加载
        self._on_mcu_changed()

    def _on_serial_preset(self, idx):
        preset = self.cmb_serial_preset.currentData()
        if not preset:
            return
        self.cmb_serial_driver.setCurrentText(preset.get("driver", "vendor"))
        tx_idx = self.cmb_serial_tx.findText(preset.get("tx", ""))
        rx_idx = self.cmb_serial_rx.findText(preset.get("rx", ""))
        if tx_idx >= 0:
            self.cmb_serial_tx.setCurrentIndex(tx_idx)
        if rx_idx >= 0:
            self.cmb_serial_rx.setCurrentIndex(rx_idx)

        # 显示说明
        note = preset.get("note", "")
        if note:
            self.lbl_serial_note.setText(note)
        else:
            self.lbl_serial_note.setText("")

    # ── Tab 4: 功能模块 ────────────────────────────────────────
    def _build_modules_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self.mod_layout = QVBoxLayout(container)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.module_widgets = {}
        return w

    def _rebuild_modules(self):
        while self.mod_layout.count():
            item = self.mod_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.module_widgets.clear()

        mcu = MCU_DATABASE.get(self.cfg.mcu_key)
        pins = mcu.pin_names() if mcu else []

        for mod in FEATURE_MODULES:
            key = mod["key"]
            grp = QGroupBox()
            grp_lay = QVBoxLayout(grp)
            chk = QCheckBox(f"  {mod['name']}")
            chk.setChecked(self.cfg.features.get(key, mod["default_enabled"]))
            grp_lay.addWidget(chk)

            sub = QWidget()
            sub_lay = QFormLayout(sub)
            pin_combos = {}
            if mod["pins_needed"]:
                for pk in mod["pins_needed"]:
                    lbl = mod.get("pin_labels", {}).get(pk, pk)
                    cmb = QComboBox()
                    cmb.addItem("— 未分配 —")
                    cmb.addItems(pins)
                    sub_lay.addRow(f"  {lbl}：", cmb)
                    pin_combos[pk] = cmb
            spin_led = None
            if key in ("RGBLIGHT_ENABLE", "RGB_MATRIX_ENABLE"):
                spin_led = QSpinBox()
                spin_led.setRange(1, 512)
                spin_led.setValue(self.cfg.rgb_led_count or 1)
                sub_lay.addRow("  LED 数量：", spin_led)
            grp_lay.addWidget(sub)
            chk.toggled.connect(lambda checked, sw=sub: sw.setVisible(checked))
            sub.setVisible(chk.isChecked())

            self.mod_layout.addWidget(grp)
            self.module_widgets[key] = {"chk": chk, "pin_combos": pin_combos, "spin_led": spin_led}
        self.mod_layout.addStretch()

    # ── Tab 5: Vial 配置 ───────────────────────────────────────
    def _build_vial_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)

        grp_uid = QGroupBox("Vial UID（唯一标识）")
        uid_lay = QHBoxLayout(grp_uid)
        self.txt_uid = QLineEdit()
        self.txt_uid.setReadOnly(True)
        self.txt_uid.setFont(QFont("Consolas", 9))
        uid_lay.addWidget(self.txt_uid)
        btn_gen = QPushButton("🔀 重新生成")
        btn_gen.clicked.connect(self._gen_uid)
        uid_lay.addWidget(btn_gen)
        layout.addWidget(grp_uid)

        grp_vial = QGroupBox("Vial 参数")
        vial_lay = QFormLayout(grp_vial)
        self.spin_layers = QSpinBox()
        self.spin_layers.setRange(2, 32)
        self.spin_layers.setValue(self.cfg.layer_count)
        vial_lay.addRow("层数：", self.spin_layers)
        self.spin_debounce = QSpinBox()
        self.spin_debounce.setRange(1, 30)
        self.spin_debounce.setValue(self.cfg.debounce)
        self.spin_debounce.setSuffix(" ms")
        vial_lay.addRow("防抖时间：", self.spin_debounce)
        self.txt_unlock_rows = QLineEdit("0, 0")
        vial_lay.addRow("解锁组合行：", self.txt_unlock_rows)
        self.txt_unlock_cols = QLineEdit("0, 1")
        vial_lay.addRow("解锁组合列：", self.txt_unlock_cols)
        layout.addWidget(grp_vial)

        layout.addStretch()
        self._gen_uid()
        return w

    def _gen_uid(self):
        import random
        self.cfg.vial_uid = [random.randint(0, 255) for _ in range(8)]
        self.txt_uid.setText(self.cfg.uid_str())

    # ── 外部调用 ────────────────────────────────────────────────

    def reload(self):
        """当 kb_model 更新后重新加载"""
        self._on_mcu_changed()
        self._rebuild_modules()
        is_split = self.cfg.is_split
        self.lbl_split_skip.setVisible(not is_split)
        self.grp_split_master.setVisible(is_split)
        self.grp_split_serial.setVisible(is_split)

        if is_split:
            mcu = MCU_DATABASE.get(self.cfg.mcu_key)
            pins = mcu.pin_names() if mcu else []
            self.cmb_serial_tx.clear()
            self.cmb_serial_rx.clear()
            self.cmb_serial_tx.addItems(pins)
            self.cmb_serial_rx.addItems(pins)
            self.cmb_serial_preset.clear()
            presets = SPLIT_SERIAL_PRESETS.get(self.cfg.mcu_key, [])
            for p in presets:
                self.cmb_serial_preset.addItem(p["desc"], p)
            if presets:
                self._on_serial_preset(0)

    def validate(self) -> bool:
        """保存配置到 cfg"""
        self.cfg.keyboard_name = self.txt_name.text().strip() or "my_keyboard"
        self.cfg.manufacturer = self.txt_mfr.text().strip() or "Custom"
        self.cfg.vid = self.txt_vid.text().strip() or "0x6464"
        self.cfg.pid = self.txt_pid.text().strip() or "0x0001"

        # 引脚（保存所有引脚，包括未分配的）
        self.cfg.row_pins = []
        for cmb in self.row_combos:
            pin = cmb.currentText()
            if not pin.startswith("—"):
                self.cfg.row_pins.append(pin)

        self.cfg.col_pins = []
        for cmb in self.col_combos:
            pin = cmb.currentText()
            if not pin.startswith("—"):
                self.cfg.col_pins.append(pin)

        # 分体
        if self.cfg.is_split:
            self.cfg.master_side = "right" if "right" in self.cmb_master.currentText() else "left"
            self.cfg.serial_driver = self.cmb_serial_driver.currentText()
            self.cfg.serial_tx = self.cmb_serial_tx.currentText()
            self.cfg.serial_rx = self.cmb_serial_rx.currentText()

            # 不对称分体：保存右手引脚
            if hasattr(self, 'chk_asymmetric') and self.chk_asymmetric.isChecked():
                self.cfg.is_asymmetric = True
                self.cfg.row_pins_right = []
                self.cfg.col_pins_right = []
                if hasattr(self, 'row_combos_right'):
                    for cmb in self.row_combos_right:
                        pin = cmb.currentText()
                        if not pin.startswith("—"):
                            self.cfg.row_pins_right.append(pin)
                if hasattr(self, 'col_combos_right'):
                    for cmb in self.col_combos_right:
                        pin = cmb.currentText()
                        if not pin.startswith("—"):
                            self.cfg.col_pins_right.append(pin)
            else:
                self.cfg.is_asymmetric = False

        # 模块
        for key, w in self.module_widgets.items():
            self.cfg.features[key] = w["chk"].isChecked()
            if w["chk"].isChecked() and w["pin_combos"]:
                pins = {}
                for pk, cmb in w["pin_combos"].items():
                    val = cmb.currentText()
                    if not val.startswith("—"):
                        pins[pk] = val
                self.cfg.module_pins[key] = pins
            if w["chk"].isChecked() and w["spin_led"]:
                self.cfg.rgb_led_count = w["spin_led"].value()

        # Vial
        self.cfg.layer_count = self.spin_layers.value()
        self.cfg.debounce = self.spin_debounce.value()
        try:
            self.cfg.unlock_rows = [int(x.strip()) for x in self.txt_unlock_rows.text().split(",")]
            self.cfg.unlock_cols = [int(x.strip()) for x in self.txt_unlock_cols.text().split(",")]
        except:
            self.cfg.unlock_rows = [0, 0]
            self.cfg.unlock_cols = [0, 1]

        return True
