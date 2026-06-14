"""
Keymap 可视化编辑器
参考 Vial/VIA 设计：点击键帽 → 从键码选择器赋值
支持多层切换、层间复制、透明键显示
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QPushButton, QComboBox, QLineEdit, QSplitter, QListWidget,
    QListWidgetItem, QTabBar, QScrollArea, QFrame, QMessageBox,
    QGridLayout, QSizePolicy, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor

from ..core.key_model import KeyModel, KeyboardModel
from .keyboard_canvas import KeyboardCanvas, KeyboardView
from PyQt6.QtWidgets import QGraphicsScene


# ─── QMK 键码分类表（参考 Vial 布局）────────────────────────────────────────
KEYCODE_GROUPS = {
    "Basic": [
        "KC_A","KC_B","KC_C","KC_D","KC_E","KC_F","KC_G","KC_H",
        "KC_I","KC_J","KC_K","KC_L","KC_M","KC_N","KC_O","KC_P",
        "KC_Q","KC_R","KC_S","KC_T","KC_U","KC_V","KC_W","KC_X",
        "KC_Y","KC_Z",
        "KC_1","KC_2","KC_3","KC_4","KC_5","KC_6","KC_7","KC_8","KC_9","KC_0",
        "KC_ENT","KC_ESC","KC_BSPC","KC_TAB","KC_SPC",
        "KC_MINS","KC_EQL","KC_LBRC","KC_RBRC","KC_BSLS",
        "KC_SCLN","KC_QUOT","KC_GRV","KC_COMM","KC_DOT","KC_SLSH",
        "KC_CAPS","KC_PSCR","KC_SCRL","KC_PAUS","KC_INS","KC_HOME",
        "KC_PGUP","KC_DEL","KC_END","KC_PGDN","KC_RGHT","KC_LEFT",
        "KC_DOWN","KC_UP",
    ],
    "ISO/JIS": [
        "KC_NONUS_HASH","KC_NONUS_BSLASH","KC_INT1","KC_INT2","KC_INT3",
        "KC_INT4","KC_INT5","KC_LANG1","KC_LANG2",
    ],
    "Modifiers": [
        "KC_LCTL","KC_LSFT","KC_LALT","KC_LGUI",
        "KC_RCTL","KC_RSFT","KC_RALT","KC_RGUI",
        "OSM(MOD_LSFT)","OSM(MOD_LCTL)","OSM(MOD_LALT)","OSM(MOD_LGUI)",
        "KC_MEH","KC_HYPR",
    ],
    "Quantum": [
        "QK_BOOT","QK_RBT","QK_CLEAR_EEPROM","QK_MAKE",
        "QK_DEBUG_TOGGLE","QK_REBOOT",
        "KC_TRNS","KC_NO",
    ],
    "Layer": [
        "MO(1)","MO(2)","MO(3)","MO(4)","MO(5)","MO(6)","MO(7)",
        "TG(1)","TG(2)","TG(3)","TG(4)",
        "TO(0)","TO(1)","TO(2)","TO(3)",
        "TT(1)","TT(2)","TT(3)",
        "DF(0)","DF(1)","DF(2)",
        "OSL(1)","OSL(2)","OSL(3)",
        "LT(1,KC_SPC)","LT(2,KC_ENT)","LT(1,KC_TAB)",
    ],
    "Mod-Tap": [
        "MT(MOD_LCTL,KC_ESC)","MT(MOD_LSFT,KC_SPC)","MT(MOD_LALT,KC_TAB)",
        "LCTL_T(KC_ESC)","LSFT_T(KC_SPC)","LALT_T(KC_TAB)",
        "LGUI_T(KC_ENT)","RCTL_T(KC_BSPC)","RSFT_T(KC_DEL)",
    ],
    "Media": [
        "KC_MUTE","KC_VOLU","KC_VOLD",
        "KC_MPLY","KC_MSTP","KC_MPRV","KC_MNXT",
        "KC_MRWD","KC_MFFD","KC_EJCT",
        "KC_BRIU","KC_BRID",
        "KC_MSEL","KC_MAIL","KC_CALC","KC_MYCM",
        "KC_WSCH","KC_WHOM","KC_WBAK","KC_WFWD",
        "KC_WSTP","KC_WREF","KC_WFAV",
    ],
    "Numpad": [
        "KC_NUM",
        "KC_P1","KC_P2","KC_P3","KC_P4","KC_P5",
        "KC_P6","KC_P7","KC_P8","KC_P9","KC_P0",
        "KC_PDOT","KC_PCMM","KC_PSLS","KC_PAST",
        "KC_PMNS","KC_PPLS","KC_PENT","KC_PEQL",
    ],
    "Functions": [
        "KC_F1","KC_F2","KC_F3","KC_F4","KC_F5","KC_F6",
        "KC_F7","KC_F8","KC_F9","KC_F10","KC_F11","KC_F12",
        "KC_F13","KC_F14","KC_F15","KC_F16","KC_F17","KC_F18",
        "KC_F19","KC_F20","KC_F21","KC_F22","KC_F23","KC_F24",
    ],
    "Lighting": [
        "RGB_TOG","RGB_MOD","RGB_RMOD",
        "RGB_HUI","RGB_HUD","RGB_SAI","RGB_SAD",
        "RGB_VAI","RGB_VAD","RGB_SPI","RGB_SPD",
        "RGB_M_P","RGB_M_B","RGB_M_R","RGB_M_SW",
        "BL_TOGG","BL_STEP","BL_ON","BL_OFF",
        "BL_INC","BL_DEC","BL_BRTG",
    ],
    "Mouse": [
        "KC_MS_UP","KC_MS_DOWN","KC_MS_LEFT","KC_MS_RIGHT",
        "KC_MS_BTN1","KC_MS_BTN2","KC_MS_BTN3","KC_MS_BTN4","KC_MS_BTN5",
        "KC_MS_WH_UP","KC_MS_WH_DOWN","KC_MS_WH_LEFT","KC_MS_WH_RIGHT",
        "KC_MS_ACCEL0","KC_MS_ACCEL1","KC_MS_ACCEL2",
    ],
}


class KeycodeButton(QPushButton):
    """键码选择器中的单个键码按钮"""
    keycode_selected = pyqtSignal(str)

    def __init__(self, code: str, parent=None):
        super().__init__(parent)
        self.code = code
        display = code.replace("KC_", "").replace("_", " ")
        self.setText(display[:10])
        self.setToolTip(code)
        self.setFixedSize(72, 32)
        self.setFont(QFont("Consolas", 8))
        self.clicked.connect(lambda: self.keycode_selected.emit(self.code))


class KeycodePanel(QWidget):
    """键码选择面板（参考 Vial 键码选择器）"""
    keycode_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 搜索框
        search_row = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("搜索键码（如 SPC、F1、MO）...")
        self.txt_search.textChanged.connect(self._on_search)
        search_row.addWidget(self.txt_search)
        layout.addLayout(search_row)

        # 自定义键码输入
        custom_row = QHBoxLayout()
        custom_row.addWidget(QLabel("自定义："))
        self.txt_custom = QLineEdit()
        self.txt_custom.setPlaceholderText("直接输入键码，如 LT(1,KC_SPC)")
        self.txt_custom.setFont(QFont("Consolas", 9))
        btn_apply = QPushButton("应用")
        btn_apply.setFixedWidth(50)
        btn_apply.clicked.connect(self._apply_custom)
        self.txt_custom.returnPressed.connect(self._apply_custom)
        custom_row.addWidget(self.txt_custom)
        custom_row.addWidget(btn_apply)
        layout.addLayout(custom_row)

        # 分组标签页
        self.tabs = QTabBar()
        self.tabs.setShape(QTabBar.Shape.RoundedNorth)
        self.tabs.setExpanding(False)
        for group in KEYCODE_GROUPS:
            self.tabs.addTab(group)
        self.tabs.currentChanged.connect(self._show_group)
        layout.addWidget(self.tabs)

        # 键码按钮滚动区
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setMinimumHeight(100)
        self.scroll.setMaximumHeight(160)
        self.btn_container = QWidget()
        self.btn_grid = QGridLayout(self.btn_container)
        self.btn_grid.setSpacing(3)
        self.scroll.setWidget(self.btn_container)
        layout.addWidget(self.scroll)

        self._show_group(0)

    def _show_group(self, idx: int):
        # 清空
        while self.btn_grid.count():
            item = self.btn_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        group_name = list(KEYCODE_GROUPS.keys())[idx]
        self._fill_buttons(KEYCODE_GROUPS[group_name])

    def _fill_buttons(self, codes: list):
        cols = 8
        for i, code in enumerate(codes):
            btn = KeycodeButton(code)
            btn.keycode_selected.connect(self.keycode_selected)
            self.btn_grid.addWidget(btn, i // cols, i % cols)

    def _on_search(self, text: str):
        text = text.strip().upper()
        if not text:
            self._show_group(self.tabs.currentIndex())
            return
        allcodes = [c for codes in KEYCODE_GROUPS.values() for c in codes]
        matched = [c for c in allcodes if text in c.upper()]
        # 清空并填充
        while self.btn_grid.count():
            item = self.btn_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._fill_buttons(matched[:64])

    def _apply_custom(self):
        code = self.txt_custom.text().strip()
        if code:
            self.keycode_selected.emit(code)


class KeymapEditor(QWidget):
    """
    Keymap 可视化编辑器
    上：层选择 + 操作按钮
    中：键盘画布（点击键帽选中，再点键码面板赋值）
    下：键码选择面板
    """

    def __init__(self, kb_model: KeyboardModel, parent=None):
        super().__init__(parent)
        self.kb = kb_model
        self.current_layer = 0
        self.selected_key: KeyModel = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶栏：层控制 ───────────────────────────────────────
        top = QHBoxLayout()
        top.setContentsMargins(8, 6, 8, 6)

        top.addWidget(QLabel("当前层："))
        self.layer_tabs = QTabBar()
        self.layer_tabs.setExpanding(False)
        self.layer_tabs.currentChanged.connect(self._switch_layer)
        top.addWidget(self.layer_tabs)

        btn_add_layer = QToolButton(); btn_add_layer.setText("+")
        btn_add_layer.setToolTip("添加层")
        btn_add_layer.clicked.connect(self._add_layer)
        btn_del_layer = QToolButton(); btn_del_layer.setText("−")
        btn_del_layer.setToolTip("删除当前层")
        btn_del_layer.clicked.connect(self._del_layer)
        btn_copy = QToolButton(); btn_copy.setText("复制↓")
        btn_copy.setToolTip("复制当前层到下一层")
        btn_copy.clicked.connect(self._copy_layer)
        btn_fill = QToolButton(); btn_fill.setText("全填TRNS")
        btn_fill.clicked.connect(self._fill_trns)
        top.addWidget(btn_add_layer)
        top.addWidget(btn_del_layer)
        top.addWidget(btn_copy)
        top.addWidget(btn_fill)

        top.addStretch()
        self.lbl_selected = QLabel("点击键帽，再选键码")
        self.lbl_selected.setStyleSheet("color:#888; font-style:italic;")
        top.addWidget(self.lbl_selected)
        layout.addLayout(top)

        # ── 主体：画布 + 键码面板 ──────────────────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 键盘画布
        self.scene = QGraphicsScene()
        self.canvas = KeyboardCanvas(self.scene)
        self.view = KeyboardView()
        self.view.setScene(self.scene)
        self.canvas.key_clicked.connect(self._on_key_clicked)
        splitter.addWidget(self.view)

        # 键码面板
        self.keycode_panel = KeycodePanel()
        self.keycode_panel.keycode_selected.connect(self._assign_keycode)
        splitter.addWidget(self.keycode_panel)
        splitter.setSizes([400, 220])

        layout.addWidget(splitter, 1)

    # ── 层管理 ──────────────────────────────────────────────────

    def _refresh_layer_tabs(self):
        self.layer_tabs.blockSignals(True)
        while self.layer_tabs.count():
            self.layer_tabs.removeTab(0)
        n = self.kb.layer_count()
        for i in range(n):
            self.layer_tabs.addTab(f"Layer {i}")
        self.layer_tabs.setCurrentIndex(min(self.current_layer, n - 1))
        self.layer_tabs.blockSignals(False)

    def _switch_layer(self, idx: int):
        self.current_layer = idx
        self.canvas.set_layer(idx)

    def _add_layer(self):
        n = self.kb.layer_count()
        self.kb.ensure_layers(n + 1)
        self._refresh_layer_tabs()
        self.layer_tabs.setCurrentIndex(n)

    def _del_layer(self):
        n = self.kb.layer_count()
        if n <= 1:
            return
        for k in self.kb.keys:
            if len(k.keycodes) >= n:
                k.keycodes.pop()
        self.current_layer = min(self.current_layer, n - 2)
        self._refresh_layer_tabs()
        self.canvas.set_layer(self.current_layer)

    def _copy_layer(self):
        n = self.kb.layer_count()
        self.kb.ensure_layers(n + 1)
        for k in self.kb.keys:
            k.keycodes[n] = k.keycodes[self.current_layer]
        self._refresh_layer_tabs()

    def _fill_trns(self):
        layer = self.current_layer
        for k in self.kb.keys:
            k.set_keycode(layer, "KC_TRNS")
        self.canvas.refresh()

    # ── 键帽交互 ────────────────────────────────────────────────

    def _on_key_clicked(self, key: KeyModel):
        self.selected_key = key
        kc = key.get_keycode(self.current_layer)
        self.lbl_selected.setText(
            f"选中：[{key.row},{key.col}]  {key.label or ''}  →  当前键值：{kc}"
        )
        self.lbl_selected.setStyleSheet("color:#4e9ef5;")

    def _assign_keycode(self, code: str):
        if self.selected_key is None:
            return
        self.selected_key.set_keycode(self.current_layer, code)
        self.canvas.refresh_key(self.selected_key.uid)
        self.lbl_selected.setText(
            f"已设置：[{self.selected_key.row},{self.selected_key.col}]  →  {code}"
        )

    # ── 外部调用 ────────────────────────────────────────────────

    def reload(self):
        """当 kb_model 更新后重新加载"""
        self.kb.ensure_layers(max(1, self.kb.layer_count()))
        self.canvas.load_keys(self.kb.keys)
        self._refresh_layer_tabs()
        self.view.fit_view()

    def validate(self) -> bool:
        return True
