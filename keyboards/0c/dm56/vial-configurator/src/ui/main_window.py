"""
主窗口 v2 — 3步向导式界面
Step 1: 布局 & 矩阵分配
Step 2: Keymap 编辑
Step 3: 配置 & 导出
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..core.key_model import KeyboardModel
from ..core.firmware_generator import ProjectConfig, FirmwareGenerator
from .editor_layout import LayoutMatrixEditor
from .editor_keymap import KeymapEditor
from .config_panel import ConfigPanel


class ExportPanel(QWidget):
    """Step 3 右侧：配置 + 导出按钮"""

    def __init__(self, kb: KeyboardModel, cfg: ProjectConfig, parent=None):
        super().__init__(parent)
        self.kb = kb
        self.cfg = cfg
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("固件导出")
        title.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        desc = QLabel(
            "配置完成后，点击下方按钮导出固件文件夹。\n"
            "导出后将文件夹复制到 vial-qmk/keyboards/ 目录下，\n"
            "使用 QMK MSYS 编译固件。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#666;")
        layout.addWidget(desc)

        layout.addStretch()

        self.btn_export = QPushButton("📦  导出固件文件夹")
        self.btn_export.setFont(QFont("", 11, QFont.Weight.Bold))
        self.btn_export.setMinimumHeight(48)
        self.btn_export.setStyleSheet(
            "background:#4e9ef5; color:white; border-radius:6px;"
        )
        self.btn_export.clicked.connect(self._do_export)
        layout.addWidget(self.btn_export)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

    def _do_export(self):
        # 强制保存当前配置
        if hasattr(self, 'config_panel'):
            self.config_panel.validate()

        unassigned = [k for k in self.kb.keys if k.row < 0 or k.col < 0]
        if unassigned:
            QMessageBox.warning(
                self, "矩阵未完全分配",
                f"有 {len(unassigned)} 个按键未分配矩阵位置。\n"
                "请返回 Step 1 完成矩阵分配。"
            )
            return

        # 检查引脚分配
        rows, cols = self.kb.matrix_size()
        if self.cfg.is_split and not self.cfg.is_asymmetric:
            rows = rows // 2

        # 检查左手引脚
        if len(self.cfg.row_pins) < rows or len(self.cfg.col_pins) < cols:
            QMessageBox.warning(
                self, "引脚未完全分配",
                f"左手矩阵需要：{rows} 行 + {cols} 列\n"
                f"当前已分配：{len(self.cfg.row_pins)} 行 + {len(self.cfg.col_pins)} 列\n\n"
                "请在左侧「主控 & 引脚」标签页完成引脚分配，\n"
                "或点击「⚡ 自动分配引脚」按钮。"
            )
            return

        # 如果是不对称分体，检查右手引脚
        if self.cfg.is_split and self.cfg.is_asymmetric:
            if len(self.cfg.row_pins_right) < rows or len(self.cfg.col_pins_right) < cols:
                QMessageBox.warning(
                    self, "右手引脚未完全分配",
                    f"右手矩阵需要：{rows} 行 + {cols} 列\n"
                    f"当前已分配：{len(self.cfg.row_pins_right)} 行 + {len(self.cfg.col_pins_right)} 列\n\n"
                    "请在左侧「主控 & 引脚」标签页完成右手引脚分配。"
                )
                return

        out_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not out_dir:
            return

        try:
            gen = FirmwareGenerator(self.kb, self.cfg)
            files = gen.generate_all(out_dir)

            msg = f"✅ 导出成功！共生成 {len(files)} 个文件。\n"
            if self.cfg.is_split and self.cfg.is_asymmetric:
                msg += "\n不对称分体键盘已生成两个独立固件文件夹：\n"
                msg += f"- {self.cfg.keyboard_name}_left/\n"
                msg += f"- {self.cfg.keyboard_name}_right/\n"
                msg += "\n请分别编译并刷写到左右手主控。"

            self.lbl_status.setText(msg)

            # 显示导出成功对话框
            export_msg = f"固件文件已生成到：\n{out_dir}/\n\n共 {len(files)} 个文件。\n\n"
            if self.cfg.is_split and self.cfg.is_asymmetric:
                export_msg += "下一步：\n"
                export_msg += "1. 将两个文件夹分别复制到 vial-qmk/keyboards/ 目录下\n"
                export_msg += "2. 使用 QMK MSYS 分别编译：\n"
                export_msg += f"   qmk compile -kb {self.cfg.keyboard_name}_left -km vial_left\n"
                export_msg += f"   qmk compile -kb {self.cfg.keyboard_name}_right -km vial_right"
            else:
                export_msg += "下一步：\n"
                export_msg += "1. 将整个文件夹复制到 vial-qmk/keyboards/ 目录下\n"
                export_msg += "2. 使用 QMK MSYS 执行编译命令：\n"
                if self.cfg.is_split:
                    export_msg += f"   qmk compile -kb {self.cfg.keyboard_name} -km vial_left\n"
                    export_msg += f"   qmk compile -kb {self.cfg.keyboard_name} -km vial_right"
                else:
                    export_msg += f"   qmk compile -kb {self.cfg.keyboard_name} -km vial"

            QMessageBox.information(self, "导出成功", export_msg
            )
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"错误：{e}")


class MainWindow(QMainWindow):
    """主窗口：3步向导"""

    def __init__(self):
        super().__init__()
        self.kb = KeyboardModel()
        self.cfg = ProjectConfig()
        self.current_step = 0
        self.setWindowTitle("Vial 固件配置器 v2.0  —  可视化三位一体编辑")
        self.setMinimumSize(1100, 720)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 顶栏：步骤指示器
        top = QFrame()
        top.setStyleSheet("background:#2b2b2b; color:#fff;")
        top.setFixedHeight(60)
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(20, 10, 20, 10)

        self.step_labels = []
        steps = [
            ("1", "布局 & 矩阵", "导入 KLE，分配矩阵坐标"),
            ("2", "Keymap 编辑", "为每层每键设置键值"),
            ("3", "配置 & 导出", "主控/分体/模块/Vial 配置"),
        ]
        for i, (num, title, desc) in enumerate(steps):
            if i > 0:
                arrow = QLabel("  →  ")
                arrow.setStyleSheet("color:#666; font-size:18px;")
                top_lay.addWidget(arrow)

            step_w = QWidget()
            step_lay = QVBoxLayout(step_w)
            step_lay.setContentsMargins(0, 0, 0, 0)
            step_lay.setSpacing(2)

            lbl_num = QLabel(num)
            lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_num.setFixedSize(28, 28)
            lbl_num.setStyleSheet(
                "background:#444; color:#aaa; border-radius:14px; font-weight:bold;"
            )
            lbl_title = QLabel(title)
            lbl_title.setFont(QFont("", 10, QFont.Weight.Bold))
            lbl_title.setStyleSheet("color:#aaa;")
            lbl_desc = QLabel(desc)
            lbl_desc.setFont(QFont("", 8))
            lbl_desc.setStyleSheet("color:#666;")

            step_lay.addWidget(lbl_num, alignment=Qt.AlignmentFlag.AlignCenter)
            step_lay.addWidget(lbl_title)
            step_lay.addWidget(lbl_desc)
            top_lay.addWidget(step_w)
            self.step_labels.append((lbl_num, lbl_title, lbl_desc))

        top_lay.addStretch()
        root.addWidget(top)

        # 主体：页面堆栈
        self.stack = QStackedWidget()

        self.editor_layout = LayoutMatrixEditor(self.kb)
        self.editor_layout.layout_changed.connect(self._on_layout_changed)
        self.stack.addWidget(self.editor_layout)

        self.editor_keymap = KeymapEditor(self.kb)
        self.stack.addWidget(self.editor_keymap)

        step3 = QSplitter(Qt.Orientation.Horizontal)
        self.config_panel = ConfigPanel(self.kb, self.cfg)
        step3.addWidget(self.config_panel)
        self.export_panel = ExportPanel(self.kb, self.cfg)
        step3.addWidget(self.export_panel)
        step3.setSizes([700, 300])
        self.stack.addWidget(step3)

        root.addWidget(self.stack, 1)

        # 底栏：导航按钮
        bottom = QFrame()
        bottom.setStyleSheet("background:#f5f5f5; border-top:1px solid #ddd;")
        bottom.setFixedHeight(56)
        bottom_lay = QHBoxLayout(bottom)
        bottom_lay.setContentsMargins(20, 8, 20, 8)

        self.btn_prev = QPushButton("◀  上一步")
        self.btn_prev.setFixedHeight(36)
        self.btn_prev.setFixedWidth(100)
        self.btn_prev.clicked.connect(self._prev_step)

        self.btn_next = QPushButton("下一步  ▶")
        self.btn_next.setFixedHeight(36)
        self.btn_next.setFixedWidth(100)
        self.btn_next.setFont(QFont("", 10, QFont.Weight.Bold))
        self.btn_next.setStyleSheet(
            "background:#4e9ef5; color:white; border-radius:4px;"
        )
        self.btn_next.clicked.connect(self._next_step)

        self.lbl_progress = QLabel()
        self.lbl_progress.setStyleSheet("color:#888;")

        bottom_lay.addWidget(self.btn_prev)
        bottom_lay.addStretch()
        bottom_lay.addWidget(self.lbl_progress)
        bottom_lay.addStretch()
        bottom_lay.addWidget(self.btn_next)
        root.addWidget(bottom)

        self._refresh_nav()

    def _refresh_nav(self):
        n = 3
        for i, (lbl_num, lbl_title, lbl_desc) in enumerate(self.step_labels):
            if i == self.current_step:
                lbl_num.setStyleSheet(
                    "background:#4e9ef5; color:#fff; border-radius:14px; font-weight:bold;"
                )
                lbl_title.setStyleSheet("color:#fff;")
                lbl_desc.setStyleSheet("color:#ccc;")
            elif i < self.current_step:
                lbl_num.setStyleSheet(
                    "background:#2d7a3e; color:#fff; border-radius:14px; font-weight:bold;"
                )
                lbl_title.setStyleSheet("color:#aaa;")
                lbl_desc.setStyleSheet("color:#666;")
            else:
                lbl_num.setStyleSheet(
                    "background:#444; color:#aaa; border-radius:14px; font-weight:bold;"
                )
                lbl_title.setStyleSheet("color:#aaa;")
                lbl_desc.setStyleSheet("color:#666;")

        self.btn_prev.setEnabled(self.current_step > 0)
        is_last = self.current_step == n - 1
        self.btn_next.setText("完成" if is_last else "下一步  ▶")
        self.lbl_progress.setText(f"第 {self.current_step + 1} / {n} 步")
        self.stack.setCurrentIndex(self.current_step)

    def _next_step(self):
        if self.current_step == 0:
            if not self.editor_layout.validate():
                return
            self.cfg.is_split = self.editor_layout.chk_split.isChecked()
            self.editor_keymap.reload()
        elif self.current_step == 1:
            if not self.editor_keymap.validate():
                return
            self.config_panel.reload()
        elif self.current_step == 2:
            if not self.config_panel.validate():
                return
            QMessageBox.information(
                self, "配置完成",
                "所有配置已完成！\n点击右侧「导出固件文件夹」按钮生成固件文件。"
            )
            return

        if self.current_step < 2:
            self.current_step += 1
            self._refresh_nav()

    def _prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._refresh_nav()

    def _on_layout_changed(self):
        pass
