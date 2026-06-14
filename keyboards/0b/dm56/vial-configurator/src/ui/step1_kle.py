"""
Step 1: KLE 布局导入页
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ..core.kle_parser import KLEParser
from ..core.project_state import ProjectState


class Step1Widget(QWidget):
    def __init__(self, state: ProjectState, parent=None):
        super().__init__(parent)
        self.state = state
        self.parser = KLEParser()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Step 1 — 导入 KLE 布局文件")
        title.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(
            "请将 Keyboard Layout Editor (keyboard-layout-editor.com) 导出的 JSON 粘贴到下方，\n"
            "或点击「打开文件」选择 .json 文件。"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 文件导入按钮
        btn_row = QHBoxLayout()
        self.btn_open = QPushButton("📂 打开 KLE JSON 文件")
        self.btn_open.clicked.connect(self._open_file)
        btn_row.addWidget(self.btn_open)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # JSON 文本框
        grp = QGroupBox("KLE JSON 内容")
        grp_layout = QVBoxLayout(grp)
        self.txt_json = QTextEdit()
        self.txt_json.setPlaceholderText('粘贴 KLE JSON 内容，例如：\n[["Q","W","E","R","T"],...]')
        self.txt_json.setFont(QFont("Consolas", 9))
        self.txt_json.setMinimumHeight(200)
        grp_layout.addWidget(self.txt_json)
        layout.addWidget(grp)

        # 解析结果
        self.lbl_result = QLabel("")
        self.lbl_result.setWordWrap(True)
        layout.addWidget(self.lbl_result)

        layout.addStretch()

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 KLE JSON 文件", "", "JSON 文件 (*.json);;所有文件 (*)"
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.txt_json.setPlainText(content)

    def validate(self) -> bool:
        """向导切换到下一步前调用，验证并解析"""
        text = self.txt_json.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先粘贴或导入 KLE JSON 内容。")
            return False
        try:
            import json
            data = json.loads(text)
            keys = self.parser.parse(data)
            if not keys:
                raise ValueError("未解析到任何按键，请检查 JSON 格式。")
            self.state.keys = keys
            self.state.kle_raw = text
            self.lbl_result.setText(
                f"✅ 解析成功，共识别 <b>{len(keys)}</b> 个按键。"
            )
            return True
        except Exception as e:
            QMessageBox.critical(self, "解析失败", f"KLE JSON 解析错误：\n{e}")
            return False
