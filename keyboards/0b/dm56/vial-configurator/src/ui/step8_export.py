"""
Step 8: 引脚汇总 + 冲突检测 + 文件导出
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QPushButton, QFileDialog,
    QMessageBox, QTextEdit, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from ..core.project_state import ProjectState
from ..core.firmware_generator import FirmwareGenerator


class Step8Widget(QWidget):
    def __init__(self, state: ProjectState, parent=None):
        super().__init__(parent)
        self.state = state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Step 8 — 引脚汇总 & 导出固件文件")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # 引脚汇总表
        grp_pins = QGroupBox("引脚分配汇总（红色=冲突）")
        pin_lay = QVBoxLayout(grp_pins)
        self.pin_table = QTableWidget(0, 3)
        self.pin_table.setHorizontalHeaderLabels(["引脚", "功能", "状态"])
        self.pin_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pin_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        pin_lay.addWidget(self.pin_table)
        layout.addWidget(grp_pins)

        # 文件预览
        grp_preview = QGroupBox("生成文件列表")
        prev_lay = QVBoxLayout(grp_preview)
        self.txt_files = QTextEdit()
        self.txt_files.setReadOnly(True)
        self.txt_files.setFont(QFont("Consolas", 9))
        self.txt_files.setMaximumHeight(120)
        prev_lay.addWidget(self.txt_files)
        layout.addWidget(grp_preview)

        # 导出按钮
        btn_row = QHBoxLayout()
        self.btn_export = QPushButton("📦  导出固件文件夹")
        self.btn_export.setFont(QFont("", 11, QFont.Weight.Bold))
        self.btn_export.setMinimumHeight(44)
        self.btn_export.clicked.connect(self._do_export)
        btn_row.addWidget(self.btn_export)
        layout.addLayout(btn_row)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)
        layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_summary()

    def _collect_pin_usage(self) -> dict:
        """收集所有引脚分配，返回 {pin: [功能列表]}"""
        usage: dict = {}

        def add(pin, func):
            if pin:
                usage.setdefault(pin, []).append(func)

        for i, p in enumerate(self.state.row_pins):
            add(p, f"ROW {i}")
        for i, p in enumerate(self.state.col_pins):
            add(p, f"COL {i}")

        if self.state.is_split:
            add(self.state.serial_tx, "Serial TX")
            add(self.state.serial_rx, "Serial RX")

        for feat_key, pins in self.state.module_pins.items():
            if self.state.features.get(feat_key):
                for role, pin in pins.items():
                    add(pin, f"{feat_key}:{role}")

        return usage

    def _refresh_summary(self):
        usage = self._collect_pin_usage()
        self.pin_table.setRowCount(0)

        for pin, funcs in sorted(usage.items()):
            row = self.pin_table.rowCount()
            self.pin_table.insertRow(row)
            conflict = len(funcs) > 1
            color = QColor("#ffcccc") if conflict else QColor("#ccffcc")

            for col, text in enumerate([pin, " | ".join(funcs), "⚠ 冲突!" if conflict else "✓ 正常"]):
                item = QTableWidgetItem(text)
                item.setBackground(color)
                self.pin_table.setItem(row, col, item)

        # 预览文件列表
        sides = ["vial_left", "vial_right"] if self.state.is_split else ["vial"]
        name = self.state.keyboard_name or "my_keyboard"
        lines = [f"keyboards/{name}/keyboard.json",
                 f"keyboards/{name}/config.h",
                 f"keyboards/{name}/rules.mk"]
        for side in sides:
            for f in ["config.h", "rules.mk", "keymap.c", "vial.json"]:
                lines.append(f"keyboards/{name}/keymaps/{side}/{f}")
        self.txt_files.setPlainText("\n".join(lines))

    def _do_export(self):
        usage = self._collect_pin_usage()
        conflicts = [p for p, funcs in usage.items() if len(funcs) > 1]
        if conflicts:
            ret = QMessageBox.question(
                self, "存在引脚冲突",
                f"以下引脚存在冲突：{', '.join(conflicts)}\n是否仍然继续导出？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if ret != QMessageBox.StandardButton.Yes:
                return

        out_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not out_dir:
            return

        try:
            cfg = self.state.to_firmware_config()
            gen = FirmwareGenerator(cfg)
            files = gen.generate_all(out_dir)
            self.lbl_status.setText(
                f"✅ 导出成功！共生成 {len(files)} 个文件。\n路径：{out_dir}/{cfg.keyboard_name}/"
            )
            QMessageBox.information(
                self, "导出成功",
                f"固件文件已生成到：\n{out_dir}/{cfg.keyboard_name}/\n\n"
                f"共 {len(files)} 个文件。\n\n"
                "下一步：将整个文件夹复制到 vial-qmk/keyboards/ 目录下，\n"
                "然后使用 QMK MSYS 执行编译命令。"
            )
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误：{e}")

    def validate(self) -> bool:
        return True
