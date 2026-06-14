"""
键盘画布渲染器
基于 PyQt6 QGraphicsScene/View，实现可视化键帽渲染
支持：点击选中、拖拽移动、矩阵坐标显示、层键值显示
"""
import math
from typing import Optional, List, Callable
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem,
    QGraphicsPolygonItem, QWidget
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QPolygonF, QTransform
)
from ..core.key_model import KeyModel

UNIT = 54  # 1U = 54px


class KeyItem(QGraphicsItem):
    """单个键帽的图形元素"""

    def __init__(self, key: KeyModel, layer: int = 0):
        super().__init__()
        self.key = key
        self.layer = layer
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self._apply_transform()

    def _apply_transform(self):
        k = self.key
        if k.is_rotated():
            t = QTransform()
            t.translate(k.rx * UNIT, k.ry * UNIT)
            t.rotate(k.r)
            t.translate(-k.rx * UNIT, -k.ry * UNIT)
            self.setTransform(t)

    def boundingRect(self) -> QRectF:
        k = self.key
        return QRectF(k.x * UNIT, k.y * UNIT,
                      k.w * UNIT, k.h * UNIT)

    def paint(self, painter: QPainter, option, widget=None):
        k = self.key
        rect = QRectF(k.x * UNIT + 2, k.y * UNIT + 2,
                      k.w * UNIT - 4, k.h * UNIT - 4)

        # 底色
        selected = self.isSelected()
        if selected:
            bg = QColor("#4e9ef5")
            border = QColor("#1a6fc4")
        elif self._hovered:
            bg = QColor("#e8f0fe")
            border = QColor("#4e9ef5")
        elif k.row >= 0 and k.col >= 0:
            bg = QColor(k.color)
            border = bg.darker(140)
        else:
            bg = QColor("#ffeecc")   # 未分配矩阵 — 橙色提示
            border = QColor("#cc8800")

        # 键帽主体（圆角矩形）
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(border, 1.5))
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(rect, 5, 5)

        # 内层阴影效果
        inner = rect.adjusted(3, 3, -3, -6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg.lighter(110)))
        painter.drawRoundedRect(inner, 4, 4)

        # 文字
        painter.setPen(QPen(QColor("#222222") if not selected else QColor("#ffffff")))

        # 键值（大字，居中）
        kc = k.get_keycode(self.layer)
        kc_display = self._format_keycode(kc)
        f_kc = QFont("Consolas", max(7, int(UNIT * 0.16)))
        f_kc.setBold(True)
        painter.setFont(f_kc)
        painter.drawText(inner, Qt.AlignmentFlag.AlignCenter, kc_display)

        # 矩阵坐标（右下角小字）
        if k.row >= 0 and k.col >= 0:
            f_mat = QFont("Consolas", max(6, int(UNIT * 0.11)))
            painter.setFont(f_mat)
            painter.setPen(QPen(QColor("#555555") if not selected else QColor("#ccddff")))
            painter.drawText(
                QRectF(rect.x(), rect.y() + rect.height() - 14,
                       rect.width() - 2, 14),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                f"{k.row},{k.col}"
            )

        # 标签（左上角小字）
        if k.label:
            f_lbl = QFont("", max(6, int(UNIT * 0.11)))
            painter.setFont(f_lbl)
            painter.setPen(QPen(QColor("#666666") if not selected else QColor("#ddeeff")))
            painter.drawText(
                QRectF(rect.x() + 2, rect.y(), rect.width() - 4, 14),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                k.label[:8]
            )

    @staticmethod
    def _format_keycode(kc: str) -> str:
        """缩短键码显示"""
        kc = kc.replace("KC_", "").replace("_", " ")
        return kc[:10] if len(kc) > 10 else kc

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()


class KeyboardCanvas(QObject):
    """
    键盘画布控制器
    管理 QGraphicsScene + KeyItem，对外暴露信号和操作接口
    """
    key_clicked = pyqtSignal(object)    # 发射 KeyModel
    selection_changed = pyqtSignal(list)  # 发射 [KeyModel, ...]

    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.scene = scene
        self.items_map: dict[int, KeyItem] = {}  # uid -> KeyItem
        self.current_layer = 0
        scene.selectionChanged.connect(self._on_selection_changed)

    def load_keys(self, keys: List[KeyModel]):
        self.scene.clear()
        self.items_map.clear()
        for key in keys:
            item = KeyItem(key, self.current_layer)
            self.scene.addItem(item)
            self.items_map[key.uid] = item

        # 自适应场景范围
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))

    def refresh(self):
        """刷新所有键帽显示（层切换或键值更新后调用）"""
        for item in self.items_map.values():
            item.layer = self.current_layer
            item.update()

    def set_layer(self, layer: int):
        self.current_layer = layer
        self.refresh()

    def refresh_key(self, uid: int):
        item = self.items_map.get(uid)
        if item:
            item.update()

    def selected_keys(self) -> List[KeyModel]:
        return [item.key for item in self.scene.selectedItems()
                if isinstance(item, KeyItem)]

    def select_key(self, uid: int, exclusive: bool = True):
        if exclusive:
            self.scene.clearSelection()
        item = self.items_map.get(uid)
        if item:
            item.setSelected(True)

    def _on_selection_changed(self):
        selected = self.selected_keys()
        self.selection_changed.emit(selected)
        if len(selected) == 1:
            self.key_clicked.emit(selected[0])


class KeyboardView(QGraphicsView):
    """可滚动/缩放的键盘视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#1e1e2e")))
        self._zoom = 1.0

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._zoom *= factor
        self._zoom = max(0.2, min(self._zoom, 4.0))
        self.setTransform(QTransform().scale(self._zoom, self._zoom))

    def fit_view(self):
        self.fitInView(self.scene().sceneRect(),
                       Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self.transform().m11()
