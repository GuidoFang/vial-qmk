"""
Step 1+2 合并：可视化布局编辑器 + 矩阵分配
参考 KLE 的布局画布 + kbfirmware 的矩阵分配界面
"""
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QTextEdit, QSplitter, QFileDialog, QMessageBox,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QRadioButton, QButtonGroup, QFormLayout, QHeaderView,
    QDoubleSpinBox, QFrame, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ..core.key_model import KeyModel, KeyboardModel
from ..core.kle_parser import KLEParser
from .keyboard_canvas import KeyboardCanvas, KeyboardView
from PyQt6.QtWidgets import QGraphicsScene


class LayoutMatrixEditor(QWidget):
    """
    Step 1+2：布局导入 & 矩阵分配
    左：KLE 画布（可视化预览，显示位置+矩阵坐标+键值）
    右：属性面板（选中键的坐标/矩阵/键值编辑）
    底：矩阵总览表
    """
    layout_changed = pyqtSignal()

    def __init__(self, kb_model: KeyboardModel, parent=None):
        super().__init__(parent)
        self.kb = kb_model
        self.parser = KLEParser()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # ── 顶部工具栏 ─────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 6, 8, 6)

        btn_open = QPushButton("📂 导入 KLE JSON")
        btn_open.clicked.connect(self._import_kle)
        btn_paste = QPushButton("📋 粘贴 KLE JSON")
        btn_paste.clicked.connect(self._paste_kle)
        btn_auto_matrix = QPushButton("⚡ 自动分配矩阵")
        btn_auto_matrix.clicked.connect(self._auto_assign)
        btn_fit = QPushButton("🔍 适合视图")
        btn_fit.clicked.connect(lambda: self.view.fit_view())

        self.chk_split = QRadioButton("分体键盘")
        self.chk_single = QRadioButton("整体键盘")
        self.chk_single.setChecked(True)
        bg = QButtonGroup(self)
        bg.addButton(self.chk_single)
        bg.addButton(self.chk_split)

        self.lbl_count = QLabel("0 个按键")
        self.lbl_count.setStyleSheet("color:#888;")

        for w in [btn_open, btn_paste, btn_auto_matrix, btn_fit,
                  QFrame(), self.chk_single, self.chk_split,
                  QFrame(), self.lbl_count]:
            if isinstance(w, QFrame):
                w.setFrameShape(QFrame.Shape.VLine)
                w.setFixedWidth(1)
            toolbar.addWidget(w)
        toolbar.addStretch()
        root.addLayout(toolbar)

        # ── 主体：左画布 + 右属性面板 ──────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左：画布
        self.scene = QGraphicsScene()
        self.canvas = KeyboardCanvas(self.scene)
        self.view = KeyboardView()
        self.view.setScene(self.scene)
        self.canvas.key_clicked.connect(self._on_key_clicked)
        self.canvas.selection_changed.connect(self._on_selection_changed)
        splitter.addWidget(self.view)

        # 右：属性面板
        right_panel = self._build_right_panel()
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 280])

        root.addWidget(splitter, 1)

        # ── 底部：矩阵总览 ─────────────────────────────────────
        self.tab_bottom = QTabWidget()
        self.tab_bottom.setMaximumHeight(160)
        self._matrix_table = self._build_matrix_table()
        self.tab_bottom.addTab(self._matrix_table, "矩阵总览")
        root.addWidget(self.tab_bottom)

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(260)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 4, 8, 4)

        lbl = QLabel("选中按键属性")
        lbl.setFont(QFont("", 10, QFont.Weight.Bold))
        layout.addWidget(lbl)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 位置（只读）
        self.prop_pos = QLabel("—")
        form.addRow("位置 (x, y)：", self.prop_pos)
        self.prop_size = QLabel("—")
        form.addRow("尺寸 (w × h)：", self.prop_size)
        self.prop_rot = QLabel("—")
        form.addRow("旋转：", self.prop_rot)

        # 矩阵（可编辑）
        row_col = QHBoxLayout()
        self.spin_row = QSpinBox(); self.spin_row.setRange(-1, 64)
        self.spin_col = QSpinBox(); self.spin_col.setRange(-1, 64)
        self.spin_row.setPrefix("R:")
        self.spin_col.setPrefix("C:")
        row_col.addWidget(self.spin_row)
        row_col.addWidget(self.spin_col)
        form.addRow("矩阵位置：", row_col)

        self.btn_apply_matrix = QPushButton("应用矩阵")
        self.btn_apply_matrix.clicked.connect(self._apply_matrix)
        form.addRow("", self.btn_apply_matrix)

        layout.addLayout(form)

        # 键帽标签
        lbl2 = QLabel("标签：")
        layout.addWidget(lbl2)
        from PyQt6.QtWidgets import QLineEdit
        self.txt_label = QLineEdit()
        self.txt_label.setPlaceholderText("KLE 标签（可选）")
        self.txt_label.editingFinished.connect(self._apply_label)
        layout.addWidget(self.txt_label)

        layout.addStretch()

        # 多选操作
        grp_multi = QGroupBox("批量操作（多选）")
        multi_lay = QVBoxLayout(grp_multi)
        btn_row_sel = QHBoxLayout()
        self.spin_batch_row = QSpinBox(); self.spin_batch_row.setRange(0, 64)
        self.spin_batch_col_start = QSpinBox(); self.spin_batch_col_start.setRange(0, 64)
        btn_row_sel.addWidget(QLabel("从 Row:"))
        btn_row_sel.addWidget(self.spin_batch_row)
        btn_row_sel.addWidget(QLabel("Col起始:"))
        btn_row_sel.addWidget(self.spin_batch_col_start)
        multi_lay.addLayout(btn_row_sel)
        btn_batch = QPushButton("批量分配（按 X 排序）")
        btn_batch.clicked.connect(self._batch_assign)
        multi_lay.addWidget(btn_batch)
        layout.addWidget(grp_multi)

        return panel

    def _build_matrix_table(self) -> QTableWidget:
        t = QTableWidget(0, 5)
        t.setHorizontalHeaderLabels(["UID", "标签", "位置(x,y)", "矩阵(r,c)", "Layer0键值"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.itemSelectionChanged.connect(self._on_table_select)
        return t

    # ── 数据操作 ────────────────────────────────────────────────

    def _import_kle(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 KLE JSON", "", "JSON (*.json);;所有文件(*)")
        if path:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            self._load_kle_text(text)

    def _paste_kle(self):
        dlg = _PasteDialog(self)
        if dlg.exec():
            self._load_kle_text(dlg.text())

    def _load_kle_text(self, text: str):
        try:
            keys = self.parser.parse_string(text)
            self.kb.keys.clear()
            self.kb._next_uid = 0
            for k in keys:
                self.kb.add_key(k)
            self.kb.ensure_layers(1)
            self._refresh_canvas()
            self._refresh_table()
            self.lbl_count.setText(f"{len(self.kb.keys)} 个按键")
            self.layout_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "解析失败", str(e))

    def _auto_assign(self):
        if not self.kb.keys:
            QMessageBox.information(self, "提示", "请先导入 KLE 布局。")
            return
        is_split = self.chk_split.isChecked()
        self.kb.auto_assign_matrix(is_split)
        self._refresh_canvas()
        self._refresh_table()
        rows, cols = self.kb.matrix_size()
        QMessageBox.information(self, "自动分配完成",
            f"矩阵：{rows} 行 × {cols} 列\n"
            + ("（分体：左右各 " + str(rows//2) + " 行）" if is_split else ""))

    def _refresh_canvas(self):
        self.canvas.load_keys(self.kb.keys)
        self.view.fit_view()

    def _refresh_table(self):
        t = self._matrix_table
        t.setRowCount(0)
        for k in self.kb.keys:
            r = t.rowCount(); t.insertRow(r)
            t.setItem(r, 0, QTableWidgetItem(str(k.uid)))
            t.setItem(r, 1, QTableWidgetItem(k.label))
            t.setItem(r, 2, QTableWidgetItem(f"{k.x:.1f}, {k.y:.1f}"))
            mat = f"{k.row}, {k.col}" if k.row >= 0 else "未分配"
            item = QTableWidgetItem(mat)
            if k.row < 0:
                item.setForeground(QColor("#cc4400"))
            t.setItem(r, 3, item)
            t.setItem(r, 4, QTableWidgetItem(k.get_keycode(0)))

    # ── 属性面板操作 ────────────────────────────────────────────

    def _on_key_clicked(self, key: KeyModel):
        self.prop_pos.setText(f"{key.x:.2f}, {key.y:.2f}")
        self.prop_size.setText(f"{key.w:.2f} × {key.h:.2f}")
        self.prop_rot.setText(f"{key.r}°  (rx={key.rx}, ry={key.ry})" if key.is_rotated() else "无")
        self.spin_row.setValue(key.row)
        self.spin_col.setValue(key.col)
        self.txt_label.setText(key.label)

        # 同步表格选中
        for r in range(self._matrix_table.rowCount()):
            if self._matrix_table.item(r, 0).text() == str(key.uid):
                self._matrix_table.selectRow(r)
                break

    def _on_selection_changed(self, keys):
        pass

    def _on_table_select(self):
        rows = self._matrix_table.selectedItems()
        if rows:
            uid = int(self._matrix_table.item(rows[0].row(), 0).text())
            self.canvas.select_key(uid)

    def _apply_matrix(self):
        selected = self.canvas.selected_keys()
        if not selected:
            return
        for k in selected:
            k.row = self.spin_row.value()
            k.col = self.spin_col.value()
        self.canvas.refresh()
        self._refresh_table()

    def _apply_label(self):
        selected = self.canvas.selected_keys()
        if selected:
            selected[0].label = self.txt_label.text()
            self.canvas.refresh()
            self._refresh_table()

    def _batch_assign(self):
        selected = sorted(self.canvas.selected_keys(), key=lambda k: k.physical_center()[0])
        if not selected:
            QMessageBox.information(self, "提示", "请先框选多个按键。")
            return
        base_row = self.spin_batch_row.value()
        base_col = self.spin_batch_col_start.value()
        for i, k in enumerate(selected):
            k.row = base_row
            k.col = base_col + i
        self.canvas.refresh()
        self._refresh_table()

    def validate(self) -> bool:
        if not self.kb.keys:
            QMessageBox.warning(self, "提示", "请先导入布局。")
            return False
        unassigned = [k for k in self.kb.keys if k.row < 0 or k.col < 0]
        if unassigned:
            ret = QMessageBox.question(self, "矩阵未完全分配",
                f"有 {len(unassigned)} 个按键未分配矩阵位置。\n"
                "可点击「自动分配矩阵」完成分配。\n\n是否仍然继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            return ret == QMessageBox.StandardButton.Yes
        return True


class _PasteDialog(QWidget):
    """粘贴 KLE JSON 的弹窗"""
    from PyQt6.QtWidgets import QDialog
    def __new__(cls, parent=None):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        dlg = QDialog(parent)
        dlg.setWindowTitle("粘贴 KLE JSON")
        dlg.resize(600, 400)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel("请将 KLE 导出的 JSON 粘贴到此处："))
        txt = QTextEdit()
        txt.setFont(QFont("Consolas", 9))
        lay.addWidget(txt)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        dlg._txt = txt
        dlg.text = lambda: txt.toPlainText().strip()
        return dlg
