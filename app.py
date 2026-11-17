import sys
import os
import math
import json
import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QListWidget, QLabel, QSpinBox, QDoubleSpinBox,
    QLineEdit, QFormLayout, QMessageBox, QScrollArea, QComboBox,
    QDialog, QDialogButtonBox, QFrame, QAction, QStatusBar, QShortcut
)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor, QTransform, QPolygonF,
    QKeySequence
)


# ==============================================================================
# ESTILO DARK UI INSPIRADO NO ADOBE PHOTOSHOP
# ==============================================================================
PHOTOSHOP_QSS = """
QMainWindow, QDialog {
    background-color: #262626;
    color: #E0E0E0;
    font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
    font-size: 12px;
}

QWidget {
    color: #E0E0E0;
}

/* Barra de Menus Superior */
QMenuBar {
    background-color: #262626;
    color: #CCCCCC;
    border-bottom: 1px solid #181818;
    padding: 2px 4px;
}
QMenuBar::item {
    background: transparent;
    padding: 4px 10px;
    border-radius: 3px;
}
QMenuBar::item:selected {
    background-color: #3E3E3E;
    color: #FFFFFF;
}
QMenu {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #181818;
    padding: 4px 0px;
}
QMenu::item {
    padding: 6px 26px 6px 16px;
}
QMenu::item:selected {
    background-color: #1473E6;
    color: #FFFFFF;
}
QMenu::separator {
    height: 1px;
    background: #3E3E3E;
    margin: 4px 8px;
}

/* Barra de Opções Contextual (Logo abaixo do menu) */
QFrame#OptionsBar {
    background-color: #323232;
    border-bottom: 1px solid #181818;
}

/* Barra de Ferramentas Vertical Esquerda */
QFrame#ToolDock {
    background-color: #323232;
    border-right: 1px solid #181818;
}
QPushButton#ToolBtn {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #D0D0D0;
    font-size: 15px;
    padding: 4px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
}
QPushButton#ToolBtn:hover {
    background-color: #424242;
    border: 1px solid #525252;
}
QPushButton#ToolBtn:checked {
    background-color: #1F1F1F;
    border: 1px solid #1473E6;
    color: #4FC3F7;
}

/* Barra de Aba do Documento */
QFrame#DocTabBar {
    background-color: #1E1E1E;
    border-bottom: 1px solid #141414;
}
QLabel#DocTabActive {
    background-color: #2B2B2B;
    color: #E6E6E6;
    border-top: 2px solid #1473E6;
    border-right: 1px solid #141414;
    padding: 5px 14px;
    font-weight: 600;
    font-size: 11px;
}

/* Área Central Escura (Workspace Canvas) */
QScrollArea#CanvasScrollArea {
    background-color: #181818;
    border: none;
}

/* Painéis Laterais Direitos */
QFrame#RightPanels {
    background-color: #2B2B2B;
    border-left: 1px solid #181818;
}
QFrame#StudioPanel {
    background-color: #323232;
    border: 1px solid #1E1E1E;
    border-radius: 3px;
}
QLabel#PanelHeader {
    background-color: #262626;
    color: #BDBDBD;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.6px;
    padding: 6px 10px;
    border-bottom: 1px solid #1C1C1C;
}
QFrame#PanelFooter {
    background-color: #2A2A2A;
    border-top: 1px solid #1E1E1E;
}

/* Inputs, SpinBoxes e Combos */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1F1F1F;
    color: #ECECEC;
    border: 1px solid #454545;
    border-radius: 3px;
    padding: 4px 6px;
    selection-background-color: #1473E6;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #1473E6;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #262626;
    color: #E0E0E0;
    selection-background-color: #1473E6;
    border: 1px solid #454545;
}

/* Lista de Regiões (Estilo Camadas Photoshop) */
QListWidget {
    background-color: #242424;
    color: #E0E0E0;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 7px 10px;
    border-bottom: 1px solid #2E2E2E;
}
QListWidget::item:hover {
    background-color: #363636;
}
QListWidget::item:selected {
    background-color: #3D526B;
    color: #FFFFFF;
    border-left: 3px solid #2680EB;
}

/* Botões Gerais */
QPushButton {
    background-color: #3E3E3E;
    color: #E0E0E0;
    border: 1px solid #505050;
    border-radius: 3px;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #4A4A4A;
    border-color: #666666;
}
QPushButton:pressed {
    background-color: #2A2A2A;
}

/* Botão Primário Adobe Blue */
QPushButton#PrimaryBtn {
    background-color: #1473E6;
    color: #FFFFFF;
    border: 1px solid #1473E6;
    border-radius: 4px;
    font-weight: bold;
    padding: 9px 12px;
}
QPushButton#PrimaryBtn:hover {
    background-color: #0D66D0;
}
QPushButton#PrimaryBtn:pressed {
    background-color: #095ABA;
}

/* Botão Destrutivo Sutil */
QPushButton#DangerBtn:hover {
    background-color: #8E2424;
    border-color: #B71C1C;
    color: #FFFFFF;
}

/* Scrollbars Finas Estilo Adobe */
QScrollBar:vertical {
    background: #1E1E1E;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #4A4A4A;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #666666;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #1E1E1E;
    height: 10px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #4A4A4A;
    min-width: 24px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #666666;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Barra de Status Inferior */
QStatusBar {
    background-color: #1F1F1F;
    color: #A8A8A8;
    border-top: 1px solid #141414;
    font-size: 11px;
}
QStatusBar::item {
    border: none;
}
"""


def crop_oriented_rect(img_np, center, size, angle):
    """Realiza o corte da imagem considerando centro, tamanho e ângulo de rotação."""
    cx, cy = center
    w, h = size
    angle_rad = math.radians(angle)

    pts = np.array([
        [-w / 2, -h / 2],
        [ w / 2, -h / 2],
        [ w / 2,  h / 2],
        [-w / 2,  h / 2]
    ], dtype=np.float32)

    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    R = np.array([
        [cos_a, -sin_a],
        [sin_a,  cos_a]
    ], dtype=np.float32)

    rotated_pts = np.dot(pts, R.T) + np.array([cx, cy], dtype=np.float32)

    dst_pts = np.array([
        [0, 0],
        [w - 1, 0],
        [w - 1, h - 1],
        [0, h - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(rotated_pts, dst_pts)
    cropped = cv2.warpPerspective(img_np, M, (max(1, int(w)), max(1, int(h))), flags=cv2.INTER_CUBIC)
    return cropped


def rect_from_four_points(points):
    """Converte 4 pontos (x, y) clicados nos cantos em (cx, cy, w, h, angle)."""
    pts = np.array(points, dtype=np.float32)
    s = pts.sum(axis=1)
    tl_idx = int(np.argmin(s))
    br_idx = int(np.argmax(s))
    if tl_idx == br_idx:
        br_idx = (tl_idx + 1) % 4

    rem = [i for i in range(4) if i not in (tl_idx, br_idx)]
    diffs = [pts[i][1] - pts[i][0] for i in rem]
    if diffs[0] <= diffs[1]:
        tr_idx, bl_idx = rem[0], rem[1]
    else:
        tr_idx, bl_idx = rem[1], rem[0]

    tl, tr, br, bl = pts[tl_idx], pts[tr_idx], pts[br_idx], pts[bl_idx]

    cx = float(pts[:, 0].mean())
    cy = float(pts[:, 1].mean())

    vx = ((tr[0] - tl[0]) + (br[0] - bl[0])) / 2.0
    vy = ((tr[1] - tl[1]) + (br[1] - bl[1])) / 2.0
    angle = round(math.degrees(math.atan2(vy, vx)), 1)

    w_top = math.hypot(tr[0] - tl[0], tr[1] - tl[1])
    w_bot = math.hypot(br[0] - bl[0], br[1] - bl[1])
    h_left = math.hypot(bl[0] - tl[0], bl[1] - tl[1])
    h_right = math.hypot(br[0] - tr[0], br[1] - tr[1])

    w = max(10.0, float((w_top + w_bot) / 2.0))
    h = max(10.0, float((h_left + h_right) / 2.0))

    return cx, cy, w, h, angle


class BatchRenameDialog(QDialog):
    """Diálogo para configurar a renomeação automática em lote."""
    def __init__(self, parent=None, current_page_idx=0, total_pages=1):
        super().__init__(parent)
        self.setWindowTitle("Andrew ScanStudio - Renomear em Lote")
        self.resize(390, 265)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.txt_prefix = QLineEdit()
        self.txt_prefix.setPlaceholderText("Ex: DOC_")
        self.txt_prefix.textChanged.connect(self.update_preview)
        form_layout.addRow("Prefixo (Opcional):", self.txt_prefix)

        self.spin_start = QSpinBox()
        self.spin_start.setRange(0, 999999)
        self.spin_start.setValue(1)
        self.spin_start.valueChanged.connect(self.update_preview)
        form_layout.addRow("Número Inicial:", self.spin_start)

        self.spin_digits = QSpinBox()
        self.spin_digits.setRange(1, 8)
        self.spin_digits.setValue(4)
        self.spin_digits.valueChanged.connect(self.update_preview)
        form_layout.addRow("Dígitos (Ex: 0001):", self.spin_digits)

        self.txt_suffix = QLineEdit()
        self.txt_suffix.setPlaceholderText("Ex: _frente")
        self.txt_suffix.textChanged.connect(self.update_preview)
        form_layout.addRow("Sufixo (Opcional):", self.txt_suffix)

        self.combo_scope = QComboBox()
        self.combo_scope.addItem("Todas as Páginas")
        self.combo_scope.addItem(f"Apenas Página Atual ({current_page_idx + 1})")
        form_layout.addRow("Aplicar em:", self.combo_scope)

        layout.addLayout(form_layout)

        self.lbl_preview = QLabel("Exemplo: ")
        self.lbl_preview.setStyleSheet("font-weight: bold; color: #4FC3F7; margin: 8px 0;")
        layout.addWidget(self.lbl_preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.update_preview()

    def update_preview(self):
        prefix = self.txt_prefix.text()
        num_str = str(self.spin_start.value()).zfill(self.spin_digits.value())
        suffix = self.txt_suffix.text()
        self.lbl_preview.setText(f"Pré-visualização: {prefix}{num_str}{suffix}")

    def get_settings(self):
        return {
            "prefix": self.txt_prefix.text(),
            "start": self.spin_start.value(),
            "digits": self.spin_digits.value(),
            "suffix": self.txt_suffix.text(),
            "all_pages": self.combo_scope.currentIndex() == 0
        }


class PhotoshopScrollArea(QScrollArea):
    """Área de visualização com Zoom direto na roda do mouse e Pan (Botão do Meio ou Espaço)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CanvasScrollArea")
        self.setAlignment(Qt.AlignCenter)
        self.space_pressed = False
        self.is_panning = False
        self.pan_start = QPointF()

    def wheelEvent(self, event):
        canvas = self.widget()
        delta = event.angleDelta().y()
        if canvas is not None and getattr(canvas, "pixmap", None) is not None and delta != 0:
            vp_pos = self.viewport().mapFrom(self, event.pos())
            canvas_pos = canvas.mapFrom(self.viewport(), vp_pos)
            old_w = max(1, canvas.width())
            old_h = max(1, canvas.height())
            rel_x = canvas_pos.x() / old_w
            rel_y = canvas_pos.y() / old_h

            if delta > 0:
                canvas.zoom_in()
            else:
                canvas.zoom_out()

            new_w = canvas.width()
            new_h = canvas.height()
            vp_w = self.viewport().width()
            vp_h = self.viewport().height()

            self.horizontalScrollBar().setRange(0, max(0, new_w - vp_w))
            self.verticalScrollBar().setRange(0, max(0, new_h - vp_h))

            if new_w > vp_w:
                self.horizontalScrollBar().setValue(int(rel_x * new_w - vp_pos.x()))
            if new_h > vp_h:
                self.verticalScrollBar().setValue(int(rel_y * new_h - vp_pos.y()))

            event.accept()
            return

        super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.space_pressed = True
            self.viewport().setCursor(Qt.OpenHandCursor)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.space_pressed = False
            self.is_panning = False
            self.viewport().unsetCursor()
            event.accept()
            return
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and self.space_pressed):
            self.is_panning = True
            self.pan_start = event.pos()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning:
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_panning and event.button() in (Qt.MiddleButton, Qt.LeftButton):
            self.is_panning = False
            if self.space_pressed:
                self.viewport().setCursor(Qt.OpenHandCursor)
            else:
                self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ImageCanvas(QWidget):
    region_selected = pyqtSignal(int)
    region_added = pyqtSignal()
    region_updated = pyqtSignal()
    zoom_changed = pyqtSignal(float)
    points_changed = pyqtSignal(int)
    cursor_moved = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.image_np = None
        self.regions = []  # List: {'cx', 'cy', 'w', 'h', 'angle', 'name', 'page'}
        self.selected_index = -1
        self.current_page = 0

        self.zoom_level = 1.0
        self.scale_factor = 1.0

        self.selection_mode = 'RECT'  # 'RECT' ou '4POINTS'
        self.four_points = []
        self.hover_img_pos = None

        self.is_drawing = False
        self.drag_mode = None
        self.drag_start_mouse = QPointF()
        self.drag_start_region = {}

        self.setMouseTracking(True)

    def set_selection_mode(self, mode):
        self.selection_mode = mode
        self.four_points.clear()
        self.is_drawing = False
        self.drag_mode = None
        self.points_changed.emit(0)
        self.setCursor(Qt.CrossCursor)
        self.update()

    def clear_pending_points(self):
        self.four_points.clear()
        self.points_changed.emit(0)
        self.update()

    def set_image(self, img_np, page_num):
        self.image_np = img_np
        self.current_page = page_num
        self.clear_pending_points()
        h, w, ch = img_np.shape
        bytes_per_line = ch * w
        q_img = QImage(img_np.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.pixmap = QPixmap.fromImage(q_img)
        self.update_geometry()
        self.update()

    def update_geometry(self):
        if self.pixmap:
            max_w = 900
            base_scale = min(1.0, max_w / self.pixmap.width())
            self.scale_factor = base_scale * self.zoom_level
            disp_w = int(self.pixmap.width() * self.scale_factor)
            disp_h = int(self.pixmap.height() * self.scale_factor)
            self.setFixedSize(disp_w, disp_h)

    def set_zoom(self, level):
        self.zoom_level = max(0.2, min(5.0, level))
        self.update_geometry()
        self.zoom_changed.emit(self.zoom_level)
        self.update()

    def zoom_in(self):
        self.set_zoom(self.zoom_level * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom_level / 1.25)

    def reset_zoom(self):
        self.set_zoom(1.0)

    def fit_to_viewport(self, vp_w, vp_h):
        if not self.pixmap:
            return
        max_w = 900
        base_scale = min(1.0, max_w / self.pixmap.width())
        base_w = self.pixmap.width() * base_scale
        base_h = self.pixmap.height() * base_scale
        target_zoom = min((vp_w - 40) / max(1, base_w), (vp_h - 40) / max(1, base_h))
        self.set_zoom(target_zoom)

    def wheelEvent(self, event):
        # Propaga o evento para o PhotoshopScrollArea aplicar o zoom centralizado no cursor
        event.ignore()

    def get_handle_positions(self, r):
        cx, cy = r['cx'], r['cy']
        w, h = r['w'], r['h']
        rad = math.radians(r['angle'])

        local_pts = {
            'TL': (-w / 2, -h / 2),
            'TR': ( w / 2, -h / 2),
            'BR': ( w / 2,  h / 2),
            'BL': (-w / 2,  h / 2),
            'ROT': (0, -h / 2 - (25 / self.scale_factor))
        }

        screen_pts = {}
        for key, (lx, ly) in local_pts.items():
            rx = lx * math.cos(rad) - ly * math.sin(rad)
            ry = lx * math.sin(rad) + ly * math.cos(rad)
            screen_pts[key] = QPointF((cx + rx) * self.scale_factor, (cy + ry) * self.scale_factor)

        return screen_pts

    def hit_test_handle(self, mouse_pos_disp):
        if not (0 <= self.selected_index < len(self.regions)):
            return None

        r = self.regions[self.selected_index]
        if r['page'] != self.current_page:
            return None

        handles = self.get_handle_positions(r)
        threshold = 10.0

        for key, pt in handles.items():
            dist = math.hypot(mouse_pos_disp.x() - pt.x(), mouse_pos_disp.y() - pt.y())
            if dist <= threshold:
                return f"RESIZE_{key}" if key != 'ROT' else "ROTATE"

        return None

    def mousePressEvent(self, event):
        if not self.pixmap:
            return

        # Deixa o ScrollArea cuidar do Pan com Botão do Meio ou Espaço
        if event.button() == Qt.MiddleButton:
            event.ignore()
            return
        parent_sa = self.parentWidget()
        while parent_sa and not isinstance(parent_sa, PhotoshopScrollArea):
            parent_sa = parent_sa.parentWidget()
        if parent_sa and parent_sa.space_pressed:
            event.ignore()
            return

        # Botão direito desfaz o último ponto no modo 4 cantos
        if event.button() == Qt.RightButton and self.selection_mode == '4POINTS':
            if self.four_points:
                self.four_points.pop()
                self.points_changed.emit(len(self.four_points))
                self.update()
            return

        if event.button() != Qt.LeftButton:
            return

        mouse_disp = event.pos()
        mouse_img = mouse_disp / self.scale_factor

        # 1. Alças da seleção atual
        if not self.four_points:
            handle_type = self.hit_test_handle(mouse_disp)
            if handle_type:
                self.drag_mode = handle_type
                self.drag_start_mouse = mouse_img
                self.drag_start_region = dict(self.regions[self.selected_index])
                return

        # 2. Modo 4 Cantos
        if self.selection_mode == '4POINTS':
            self.four_points.append((mouse_img.x(), mouse_img.y()))
            self.points_changed.emit(len(self.four_points))

            if len(self.four_points) == 4:
                cx, cy, w, h, angle = rect_from_four_points(self.four_points)
                region_num = len(self.regions) + 1
                new_region = {
                    'cx': cx, 'cy': cy,
                    'w': w, 'h': h,
                    'angle': angle,
                    'name': f'recorte_p{self.current_page + 1}_{region_num}',
                    'page': self.current_page
                }
                self.regions.append(new_region)
                self.selected_index = len(self.regions) - 1
                self.four_points.clear()
                self.points_changed.emit(0)
                self.region_added.emit()

            self.update()
            return

        # 3. Modo Retângulo Padrão
        clicked_idx = self.get_region_at(mouse_img.x(), mouse_img.y())
        if clicked_idx != -1:
            self.selected_index = clicked_idx
            self.region_selected.emit(self.selected_index)
            self.drag_mode = 'MOVE'
            self.drag_start_mouse = mouse_img
            self.drag_start_region = dict(self.regions[self.selected_index])
            self.update()
            return

        self.is_drawing = True
        self.drag_start_mouse = mouse_img
        self.drag_start_region = {'x': mouse_img.x(), 'y': mouse_img.y()}

    def mouseMoveEvent(self, event):
        mouse_disp = event.pos()
        mouse_img = mouse_disp / self.scale_factor
        self.hover_img_pos = mouse_img

        if self.pixmap:
            self.cursor_moved.emit(int(mouse_img.x()), int(mouse_img.y()))

        if self.selection_mode == '4POINTS':
            if not self.four_points and self.hit_test_handle(mouse_disp):
                handle = self.hit_test_handle(mouse_disp)
                self.setCursor(Qt.PointingHandCursor if handle == 'ROTATE' else Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.CrossCursor)
            if self.four_points:
                self.update()
            if not self.drag_mode:
                return

        if not self.drag_mode and not self.is_drawing:
            handle = self.hit_test_handle(mouse_disp)
            if handle == 'ROTATE':
                self.setCursor(Qt.PointingHandCursor)
            elif handle and handle.startswith('RESIZE'):
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.CrossCursor)

        if self.is_drawing:
            self.update()
            return

        if not self.drag_mode or not (0 <= self.selected_index < len(self.regions)):
            return

        r = self.regions[self.selected_index]

        if self.drag_mode == 'MOVE':
            dx = mouse_img.x() - self.drag_start_mouse.x()
            dy = mouse_img.y() - self.drag_start_mouse.y()
            r['cx'] = self.drag_start_region['cx'] + dx
            r['cy'] = self.drag_start_region['cy'] + dy

        elif self.drag_mode == 'ROTATE':
            cx, cy = r['cx'], r['cy']
            dx = mouse_img.x() - cx
            dy = mouse_img.y() - cy
            angle_rad = math.atan2(dy, dx)
            new_angle = math.degrees(angle_rad) + 90
            r['angle'] = round((new_angle + 180) % 360 - 180, 1)

        elif self.drag_mode.startswith('RESIZE_'):
            handle_type = self.drag_mode.replace('RESIZE_', '')
            self.handle_resize_drag(handle_type, mouse_img)

        self.region_updated.emit()
        self.update()

    def handle_resize_drag(self, handle_type, mouse_img):
        r = self.regions[self.selected_index]
        cx, cy = r['cx'], r['cy']
        w, h = r['w'], r['h']
        angle = r['angle']
        rad = math.radians(angle)

        local_corners = {
            'TL': (-w / 2, -h / 2),
            'TR': ( w / 2, -h / 2),
            'BR': ( w / 2,  h / 2),
            'BL': (-w / 2,  h / 2)
        }
        anchors = {'TL': 'BR', 'TR': 'BL', 'BR': 'TL', 'BL': 'TR'}

        anchor_name = anchors[handle_type]
        ax_loc, ay_loc = local_corners[anchor_name]

        ax_img = cx + (ax_loc * math.cos(rad) - ay_loc * math.sin(rad))
        ay_img = cy + (ax_loc * math.sin(rad) + ay_loc * math.cos(rad))

        dx_img = mouse_img.x() - ax_img
        dy_img = mouse_img.y() - ay_img

        unrot_rad = -rad
        rel_x = dx_img * math.cos(unrot_rad) - dy_img * math.sin(unrot_rad)
        rel_y = dx_img * math.sin(unrot_rad) + dy_img * math.cos(unrot_rad)

        if handle_type == 'TL':
            new_w, new_h = -rel_x, -rel_y
            c_loc_x, c_loc_y = -new_w / 2, -new_h / 2
        elif handle_type == 'TR':
            new_w, new_h = rel_x, -rel_y
            c_loc_x, c_loc_y = new_w / 2, -new_h / 2
        elif handle_type == 'BR':
            new_w, new_h = rel_x, rel_y
            c_loc_x, c_loc_y = new_w / 2, new_h / 2
        elif handle_type == 'BL':
            new_w, new_h = -rel_x, rel_y
            c_loc_x, c_loc_y = -new_w / 2, new_h / 2

        new_w = max(10.0, new_w)
        new_h = max(10.0, new_h)

        new_cx = ax_img + (c_loc_x * math.cos(rad) - c_loc_y * math.sin(rad))
        new_cy = ay_img + (c_loc_x * math.sin(rad) + c_loc_y * math.cos(rad))

        r['w'] = new_w
        r['h'] = new_h
        r['cx'] = new_cx
        r['cy'] = new_cy

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_drawing:
                self.is_drawing = False
                end_point = event.pos() / self.scale_factor
                start_x, start_y = self.drag_start_region['x'], self.drag_start_region['y']

                w = abs(end_point.x() - start_x)
                h = abs(end_point.y() - start_y)

                if w > 10 and h > 10:
                    cx = (start_x + end_point.x()) / 2.0
                    cy = (start_y + end_point.y()) / 2.0
                    region_num = len(self.regions) + 1
                    new_region = {
                        'cx': cx, 'cy': cy,
                        'w': w, 'h': h,
                        'angle': 0.0,
                        'name': f'recorte_p{self.current_page + 1}_{region_num}',
                        'page': self.current_page
                    }
                    self.regions.append(new_region)
                    self.selected_index = len(self.regions) - 1
                    self.region_added.emit()

            self.drag_mode = None
            self.setCursor(Qt.CrossCursor)
            self.update()

    def get_region_at(self, x, y):
        for idx, r in enumerate(self.regions):
            if r['page'] != self.current_page:
                continue
            dx = x - r['cx']
            dy = y - r['cy']
            rad = math.radians(-r['angle'])
            rx = dx * math.cos(rad) - dy * math.sin(rad)
            ry = dx * math.sin(rad) + dy * math.cos(rad)
            if abs(rx) <= r['w'] / 2 and abs(ry) <= r['h'] / 2:
                return idx
        return -1

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            scaled_pix = self.pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled_pix)

            # Borda sutil estilo prancheta do Photoshop
            painter.setPen(QPen(QColor(15, 15, 15), 1))
            painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        for idx, r in enumerate(self.regions):
            if r['page'] != self.current_page:
                continue

            is_selected = (idx == self.selected_index)
            pen_color = QColor(38, 128, 235) if is_selected else QColor(0, 230, 118)
            pen = QPen(pen_color, 2 if is_selected else 1.5)
            painter.setPen(pen)

            if is_selected:
                painter.setBrush(QColor(38, 128, 235, 35))
            else:
                painter.setBrush(QColor(0, 230, 118, 15))

            transform = QTransform()
            transform.translate(r['cx'] * self.scale_factor, r['cy'] * self.scale_factor)
            transform.rotate(r['angle'])

            w_s = r['w'] * self.scale_factor
            h_s = r['h'] * self.scale_factor
            rect = QRectF(-w_s / 2, -h_s / 2, w_s, h_s)

            polygon = transform.map(QPolygonF(rect))
            painter.drawPolygon(polygon)

            label_pos = transform.map(QPointF(-w_s / 2, -h_s / 2 - 6))
            painter.setPen(QPen(QColor(255, 255, 255) if is_selected else QColor(185, 246, 202)))
            painter.drawText(int(label_pos.x()), int(label_pos.y()), r['name'])

            if is_selected:
                handles = self.get_handle_positions(r)

                top_mid = transform.map(QPointF(0, -h_s / 2))
                painter.setPen(QPen(QColor(79, 195, 247), 1, Qt.DashLine))
                painter.drawLine(top_mid, handles['ROT'])

                painter.setPen(QPen(QColor(38, 128, 235), 2))
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(handles['ROT'], 5, 5)

                painter.setPen(QPen(QColor(38, 128, 235), 1.5))
                painter.setBrush(QColor(255, 255, 255))
                for key in ['TL', 'TR', 'BR', 'BL']:
                    pt = handles[key]
                    painter.drawRect(QRectF(pt.x() - 4, pt.y() - 4, 8, 8))

        # Marcações parciais no Modo 4 Cantos
        if self.selection_mode == '4POINTS' and self.four_points:
            disp_pts = [QPointF(px * self.scale_factor, py * self.scale_factor) for px, py in self.four_points]

            painter.setPen(QPen(QColor(255, 167, 38), 2, Qt.SolidLine))
            for i in range(len(disp_pts) - 1):
                painter.drawLine(disp_pts[i], disp_pts[i + 1])

            if self.hover_img_pos is not None:
                cursor_disp = QPointF(self.hover_img_pos.x() * self.scale_factor,
                                      self.hover_img_pos.y() * self.scale_factor)
                painter.setPen(QPen(QColor(255, 167, 38), 1, Qt.DashLine))
                painter.drawLine(disp_pts[-1], cursor_disp)
                if len(disp_pts) == 3:
                    painter.drawLine(cursor_disp, disp_pts[0])

            for i, pt in enumerate(disp_pts):
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.setBrush(QColor(255, 111, 0))
                painter.drawEllipse(pt, 5, 5)
                painter.setPen(QPen(QColor(255, 235, 59), 2))
                painter.drawText(int(pt.x() + 9), int(pt.y() - 6), f"P{i + 1}")

        # Desenho temporário no Modo Retângulo
        if self.is_drawing:
            pen = QPen(QColor(79, 195, 247), 1.5, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(QColor(38, 128, 235, 30))
            curr_pos = self.mapFromGlobal(self.cursor().pos())
            x1 = self.drag_start_region['x'] * self.scale_factor
            y1 = self.drag_start_region['y'] * self.scale_factor
            painter.drawRect(QRectF(QPointF(x1, y1), curr_pos))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Andrew ScanStudio")
        self.resize(1380, 820)

        self.pages_images = []
        self.page_rotations = []
        self.current_page_idx = 0
        self.loaded_filepath = None

        self.init_ui()
        self.init_menus_and_shortcuts()

    def init_ui(self):
        central_container = QWidget()
        self.setCentralWidget(central_container)
        root_layout = QVBoxLayout(central_container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ======================================================================
        # 1. BARRA DE OPÇÕES CONTEXTUAL (TOP OPTIONS BAR ESTILO PHOTOSHOP)
        # ======================================================================
        options_bar = QFrame()
        options_bar.setObjectName("OptionsBar")
        options_bar.setFixedHeight(38)
        opt_layout = QHBoxLayout(options_bar)
        opt_layout.setContentsMargins(10, 3, 10, 3)
        opt_layout.setSpacing(8)

        self.lbl_active_tool = QLabel("▭ Seleção Retangular")
        self.lbl_active_tool.setStyleSheet("font-weight: bold; color: #4FC3F7;")
        opt_layout.addWidget(self.lbl_active_tool)

        self.lbl_mode_hint = QLabel("")
        self.lbl_mode_hint.setStyleSheet("color: #FFB74D; font-weight: bold;")
        opt_layout.addWidget(self.lbl_mode_hint)

        self.btn_clear_pts = QPushButton("Limpar Pontos")
        self.btn_clear_pts.setVisible(False)
        self.btn_clear_pts.clicked.connect(lambda: self.canvas.clear_pending_points())
        opt_layout.addWidget(self.btn_clear_pts)

        opt_layout.addWidget(self._create_v_sep())

        # Controles de Página
        opt_layout.addWidget(QLabel("Página:"))
        self.btn_prev_page = QPushButton("◀")
        self.btn_prev_page.setFixedWidth(26)
        self.btn_prev_page.clicked.connect(self.prev_page)
        opt_layout.addWidget(self.btn_prev_page)

        self.combo_pages = QComboBox()
        self.combo_pages.setMinimumWidth(115)
        self.combo_pages.currentIndexChanged.connect(self.change_page)
        opt_layout.addWidget(self.combo_pages)

        self.btn_next_page = QPushButton("▶")
        self.btn_next_page.setFixedWidth(26)
        self.btn_next_page.clicked.connect(self.next_page)
        opt_layout.addWidget(self.btn_next_page)

        self.lbl_page = QLabel("Total: 0")
        self.lbl_page.setStyleSheet("color: #9E9E9E;")
        opt_layout.addWidget(self.lbl_page)

        opt_layout.addWidget(self._create_v_sep())

        # Controles Rápidos de Rotação
        self.btn_rot_ccw_opt = QPushButton("↺ 90°")
        self.btn_rot_ccw_opt.setToolTip("Girar Página 90° Anti-horário")
        self.btn_rot_ccw_opt.clicked.connect(lambda: self.rotate_current_page('ccw'))
        opt_layout.addWidget(self.btn_rot_ccw_opt)

        self.btn_rot_cw_opt = QPushButton("↻ 90°")
        self.btn_rot_cw_opt.setToolTip("Girar Página 90° Horário")
        self.btn_rot_cw_opt.clicked.connect(lambda: self.rotate_current_page('cw'))
        opt_layout.addWidget(self.btn_rot_cw_opt)

        opt_layout.addStretch()

        # Controles de Zoom na Barra de Opções
        self.btn_zoom_out_opt = QPushButton("−")
        self.btn_zoom_out_opt.setFixedWidth(26)
        self.btn_zoom_out_opt.clicked.connect(lambda: self.canvas.zoom_out())
        opt_layout.addWidget(self.btn_zoom_out_opt)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setMinimumWidth(42)
        self.lbl_zoom.setAlignment(Qt.AlignCenter)
        opt_layout.addWidget(self.lbl_zoom)

        self.btn_zoom_in_opt = QPushButton("+")
        self.btn_zoom_in_opt.setFixedWidth(26)
        self.btn_zoom_in_opt.clicked.connect(lambda: self.canvas.zoom_in())
        opt_layout.addWidget(self.btn_zoom_in_opt)

        self.btn_zoom_reset = QPushButton("100%")
        self.btn_zoom_reset.clicked.connect(lambda: self.canvas.reset_zoom())
        opt_layout.addWidget(self.btn_zoom_reset)

        self.btn_zoom_fit = QPushButton("Ajustar")
        self.btn_zoom_fit.clicked.connect(self.fit_canvas_to_view)
        opt_layout.addWidget(self.btn_zoom_fit)

        root_layout.addWidget(options_bar)

        # ======================================================================
        # 2. CORPO PRINCIPAL (DOCA ESQUERDA + CANVAS CENTRAL + PAINÉIS DIREITOS)
        # ======================================================================
        workspace_layout = QHBoxLayout()
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        # --- 2A. BARRA DE FERRAMENTAS LATERAL ESQUERDA (PHOTOSHOP TOOL DOCK) ---
        tool_dock = QFrame()
        tool_dock.setObjectName("ToolDock")
        tool_dock.setFixedWidth(46)
        tool_layout = QVBoxLayout(tool_dock)
        tool_layout.setContentsMargins(6, 10, 6, 10)
        tool_layout.setSpacing(6)

        self.btn_mode_rect = QPushButton("▭")
        self.btn_mode_rect.setObjectName("ToolBtn")
        self.btn_mode_rect.setCheckable(True)
        self.btn_mode_rect.setChecked(True)
        self.btn_mode_rect.setToolTip("Ferramenta Seleção Retangular (M)\nClique e arraste para criar um recorte")
        self.btn_mode_rect.clicked.connect(lambda: self.switch_selection_mode('RECT'))
        tool_layout.addWidget(self.btn_mode_rect)

        self.btn_mode_4pts = QPushButton("📍")
        self.btn_mode_4pts.setObjectName("ToolBtn")
        self.btn_mode_4pts.setCheckable(True)
        self.btn_mode_4pts.setToolTip("Ferramenta Marcar 4 Cantos (P)\nClique nos 4 vértices do documento inclinado")
        self.btn_mode_4pts.clicked.connect(lambda: self.switch_selection_mode('4POINTS'))
        tool_layout.addWidget(self.btn_mode_4pts)

        tool_layout.addWidget(self._create_h_sep())

        self.btn_rot_ccw = QPushButton("↺")
        self.btn_rot_ccw.setObjectName("ToolBtn")
        self.btn_rot_ccw.setToolTip("Girar Página 90° Anti-horário")
        self.btn_rot_ccw.clicked.connect(lambda: self.rotate_current_page('ccw'))
        tool_layout.addWidget(self.btn_rot_ccw)

        self.btn_rot_cw = QPushButton("↻")
        self.btn_rot_cw.setObjectName("ToolBtn")
        self.btn_rot_cw.setToolTip("Girar Página 90° Horário")
        self.btn_rot_cw.clicked.connect(lambda: self.rotate_current_page('cw'))
        tool_layout.addWidget(self.btn_rot_cw)

        tool_layout.addWidget(self._create_h_sep())

        self.btn_zoom_in = QPushButton("🔍+")
        self.btn_zoom_in.setObjectName("ToolBtn")
        self.btn_zoom_in.setToolTip("Ampliar Zoom (Roda do Mouse / Ctrl +)")
        self.btn_zoom_in.clicked.connect(lambda: self.canvas.zoom_in())
        tool_layout.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton("🔍-")
        self.btn_zoom_out.setObjectName("ToolBtn")
        self.btn_zoom_out.setToolTip("Reduzir Zoom (Roda do Mouse / Ctrl -)")
        self.btn_zoom_out.clicked.connect(lambda: self.canvas.zoom_out())
        tool_layout.addWidget(self.btn_zoom_out)

        self.btn_fit_dock = QPushButton("⤢")
        self.btn_fit_dock.setObjectName("ToolBtn")
        self.btn_fit_dock.setToolTip("Ajustar Página à Tela (Ctrl + 0)")
        self.btn_fit_dock.clicked.connect(self.fit_canvas_to_view)
        tool_layout.addWidget(self.btn_fit_dock)

        tool_layout.addStretch()
        workspace_layout.addWidget(tool_dock)

        # --- 2B. ÁREA CENTRAL DE DOCUMENTO (ABA + VIEWPORT) ---
        center_area = QVBoxLayout()
        center_area.setContentsMargins(0, 0, 0, 0)
        center_area.setSpacing(0)

        doc_tab_bar = QFrame()
        doc_tab_bar.setObjectName("DocTabBar")
        doc_tab_bar.setFixedHeight(30)
        tab_layout = QHBoxLayout(doc_tab_bar)
        tab_layout.setContentsMargins(0, 0, 8, 0)
        tab_layout.setSpacing(0)

        self.lbl_doc_tab = QLabel("Nenhum documento aberto @ 100% (RGB/8)")
        self.lbl_doc_tab.setObjectName("DocTabActive")
        tab_layout.addWidget(self.lbl_doc_tab)
        tab_layout.addStretch()

        btn_quick_open = QPushButton("📁 Abrir Arquivo...")
        btn_quick_open.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        btn_quick_open.clicked.connect(self.open_file)
        tab_layout.addWidget(btn_quick_open)

        center_area.addWidget(doc_tab_bar)

        self.canvas = ImageCanvas()
        self.canvas.region_selected.connect(self.on_region_selected)
        self.canvas.region_added.connect(self.sync_region_list)
        self.canvas.region_updated.connect(self.populate_controls)
        self.canvas.zoom_changed.connect(self.update_zoom_label)
        self.canvas.points_changed.connect(self.update_points_hint)
        self.canvas.cursor_moved.connect(self.update_cursor_status)

        self.scroll_area = PhotoshopScrollArea()
        self.scroll_area.setWidget(self.canvas)
        center_area.addWidget(self.scroll_area)

        workspace_layout.addLayout(center_area, stretch=1)

        # --- 2C. PAINÉIS LATERAIS DIREITOS (STUDIO PANELS ESTILO PHOTOSHOP) ---
        right_panels = QFrame()
        right_panels.setObjectName("RightPanels")
        right_panels.setFixedWidth(315)
        right_layout = QVBoxLayout(right_panels)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)

        # PAINEL 1: PROPRIEDADES
        panel_props = self._create_studio_panel("PROPRIEDADES")
        props_body = QWidget()
        form_layout = QFormLayout(props_body)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(8)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Nome do arquivo de saída")
        self.txt_name.textChanged.connect(self.update_region_properties)
        form_layout.addRow("Nome:", self.txt_name)

        self.spin_angle = QDoubleSpinBox()
        self.spin_angle.setRange(-180.0, 180.0)
        self.spin_angle.setSingleStep(0.5)
        self.spin_angle.setSuffix(" °")
        self.spin_angle.valueChanged.connect(self.update_region_properties)
        form_layout.addRow("Inclinação:", self.spin_angle)

        dims_row = QHBoxLayout()
        dims_row.setSpacing(6)
        self.spin_w = QSpinBox()
        self.spin_w.setRange(1, 10000)
        self.spin_w.setPrefix("L: ")
        self.spin_w.setSuffix(" px")
        self.spin_w.valueChanged.connect(self.update_region_properties)

        self.spin_h = QSpinBox()
        self.spin_h.setRange(1, 10000)
        self.spin_h.setPrefix("A: ")
        self.spin_h.setSuffix(" px")
        self.spin_h.valueChanged.connect(self.update_region_properties)

        dims_row.addWidget(self.spin_w)
        dims_row.addWidget(self.spin_h)
        form_layout.addRow("Dimensões:", dims_row)

        panel_props.layout().addWidget(props_body)
        right_layout.addWidget(panel_props)

        # PAINEL 2: REGIÕES (ESTILO CAMADAS PHOTOSHOP)
        panel_layers = self._create_studio_panel("REGIÕES / CAMADAS")
        self.list_regions = QListWidget()
        self.list_regions.currentRowChanged.connect(self.on_list_item_changed)
        panel_layers.layout().addWidget(self.list_regions)

        layers_footer = QFrame()
        layers_footer.setObjectName("PanelFooter")
        footer_layout = QHBoxLayout(layers_footer)
        footer_layout.setContentsMargins(6, 5, 6, 5)
        footer_layout.setSpacing(6)

        self.btn_batch_rename = QPushButton("🏷️ Renomear Lote")
        self.btn_batch_rename.setToolTip("Renomear regiões sequencialmente em lote (Ctrl+B)")
        self.btn_batch_rename.clicked.connect(self.open_batch_rename)
        footer_layout.addWidget(self.btn_batch_rename)

        self.btn_delete = QPushButton("🗑️ Excluir")
        self.btn_delete.setObjectName("DangerBtn")
        self.btn_delete.setToolTip("Excluir região selecionada (Del)")
        self.btn_delete.clicked.connect(self.delete_region)
        footer_layout.addWidget(self.btn_delete)

        panel_layers.layout().addWidget(layers_footer)
        right_layout.addWidget(panel_layers, stretch=1)

        # PAINEL 3: EXPORTAÇÃO
        panel_export = self._create_studio_panel("EXPORTAÇÃO")
        export_body = QWidget()
        exp_layout = QVBoxLayout(export_body)
        exp_layout.setContentsMargins(10, 10, 10, 10)
        exp_layout.setSpacing(8)

        form_fmt = QFormLayout()
        self.combo_format = QComboBox()
        self.combo_format.addItems(["JPG (.jpg)", "PNG (.png)", "WEBP (.webp)"])
        form_fmt.addRow("Formato:", self.combo_format)
        exp_layout.addLayout(form_fmt)

        self.btn_export = QPushButton("🚀 Exportar Todos os Recortes")
        self.btn_export.setObjectName("PrimaryBtn")
        self.btn_export.clicked.connect(self.export_crops)
        exp_layout.addWidget(self.btn_export)

        panel_export.layout().addWidget(export_body)
        right_layout.addWidget(panel_export)

        workspace_layout.addWidget(right_panels)
        root_layout.addLayout(workspace_layout, stretch=1)

        # ======================================================================
        # 3. BARRA DE STATUS INFERIOR ESTILO PHOTOSHOP
        # ======================================================================
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.status_zoom = QLabel("  100%  ")
        self.status_zoom.setStyleSheet("color: #E0E0E0; font-weight: bold; border-right: 1px solid #383838;")
        status_bar.addWidget(self.status_zoom)

        self.status_doc_info = QLabel("  Doc: Nenhum arquivo carregado  ")
        self.status_doc_info.setStyleSheet("border-right: 1px solid #383838;")
        status_bar.addWidget(self.status_doc_info)

        self.status_cursor = QLabel("  X: -   Y: -  ")
        self.status_cursor.setStyleSheet("border-right: 1px solid #383838;")
        status_bar.addWidget(self.status_cursor)

        self.status_hint = QLabel("  Roda do Mouse: Zoom  |  Espaço + Arrastar ou Botão do Meio: Mover Tela")
        status_bar.addPermanentWidget(self.status_hint)

        self.switch_selection_mode('RECT')

    def _create_studio_panel(self, title):
        frame = QFrame()
        frame.setObjectName("StudioPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(title)
        header.setObjectName("PanelHeader")
        layout.addWidget(header)
        return frame

    def _create_v_sep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #484848;")
        return sep

    def _create_h_sep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #484848;")
        return sep

    def init_menus_and_shortcuts(self):
        menubar = self.menuBar()

        # Menu Arquivo
        menu_file = menubar.addMenu("Arquivo")
        act_open = QAction("Abrir Imagem ou PDF...", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.open_file)
        menu_file.addAction(act_open)

        menu_file.addSeparator()

        act_save_proj = QAction("Salvar Projeto (.json)...", self)
        act_save_proj.setShortcut("Ctrl+S")
        act_save_proj.triggered.connect(self.save_project)
        menu_file.addAction(act_save_proj)

        act_load_proj = QAction("Carregar Projeto (.json)...", self)
        act_load_proj.setShortcut("Ctrl+L")
        act_load_proj.triggered.connect(self.load_project)
        menu_file.addAction(act_load_proj)

        menu_file.addSeparator()

        act_export = QAction("Exportar Todos os Recortes...", self)
        act_export.setShortcut("Ctrl+E")
        act_export.triggered.connect(self.export_crops)
        menu_file.addAction(act_export)

        menu_file.addSeparator()

        act_exit = QAction("Sair", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        # Menu Editar
        menu_edit = menubar.addMenu("Editar")
        act_batch = QAction("Renomear Regiões em Lote...", self)
        act_batch.setShortcut("Ctrl+B")
        act_batch.triggered.connect(self.open_batch_rename)
        menu_edit.addAction(act_batch)

        act_del = QAction("Excluir Região Selecionada", self)
        act_del.triggered.connect(self.delete_region)
        menu_edit.addAction(act_del)

        act_clear_pts = QAction("Limpar Pontos Pendentes (4 Cantos)", self)
        act_clear_pts.setShortcut("Esc")
        act_clear_pts.triggered.connect(lambda: self.canvas.clear_pending_points())
        menu_edit.addAction(act_clear_pts)

        # Menu Imagem
        menu_image = menubar.addMenu("Imagem")
        act_cw = QAction("Girar Página 90° Horário", self)
        act_cw.triggered.connect(lambda: self.rotate_current_page('cw'))
        menu_image.addAction(act_cw)

        act_ccw = QAction("Girar Página 90° Anti-horário", self)
        act_ccw.triggered.connect(lambda: self.rotate_current_page('ccw'))
        menu_image.addAction(act_ccw)

        # Menu Visualizar
        menu_view = menubar.addMenu("Visualizar")
        act_zin = QAction("Ampliar Zoom", self)
        act_zin.setShortcut("Ctrl++")
        act_zin.triggered.connect(lambda: self.canvas.zoom_in())
        menu_view.addAction(act_zin)

        act_zout = QAction("Reduzir Zoom", self)
        act_zout.setShortcut("Ctrl+-")
        act_zout.triggered.connect(lambda: self.canvas.zoom_out())
        menu_view.addAction(act_zout)

        act_z100 = QAction("Tamanho Real (100%)", self)
        act_z100.setShortcut("Ctrl+1")
        act_z100.triggered.connect(lambda: self.canvas.reset_zoom())
        menu_view.addAction(act_z100)

        act_zfit = QAction("Ajustar à Tela", self)
        act_zfit.setShortcut("Ctrl+0")
        act_zfit.triggered.connect(self.fit_canvas_to_view)
        menu_view.addAction(act_zfit)

        # Atalhos de Teclado Rápidos
        QShortcut(QKeySequence("M"), self, activated=lambda: self.switch_selection_mode('RECT'))
        QShortcut(QKeySequence("P"), self, activated=lambda: self.switch_selection_mode('4POINTS'))
        QShortcut(QKeySequence(Qt.Key_Delete), self, activated=self.delete_region_if_not_typing)

    def delete_region_if_not_typing(self):
        if not isinstance(QApplication.focusWidget(), QLineEdit):
            self.delete_region()

    def switch_selection_mode(self, mode):
        is_4pts = (mode == '4POINTS')
        self.btn_mode_rect.setChecked(not is_4pts)
        self.btn_mode_4pts.setChecked(is_4pts)
        self.btn_clear_pts.setVisible(is_4pts)

        if is_4pts:
            self.lbl_active_tool.setText("📍 Marcar 4 Cantos (P)")
            self.lbl_active_tool.setStyleSheet("font-weight: bold; color: #FFB74D;")
        else:
            self.lbl_active_tool.setText("▭ Seleção Retangular (M)")
            self.lbl_active_tool.setStyleSheet("font-weight: bold; color: #4FC3F7;")

        self.canvas.set_selection_mode(mode)
        self.update_points_hint(0)

    def update_points_hint(self, count):
        if self.canvas.selection_mode == '4POINTS':
            self.lbl_mode_hint.setText(f"[{count}/4 cantos | Botão dir. desfaz]")
        else:
            self.lbl_mode_hint.setText("")

    def update_zoom_label(self, val):
        pct = f"{int(val * 100)}%"
        self.lbl_zoom.setText(pct)
        self.status_zoom.setText(f"  {pct}  ")
        self.update_doc_tab_title()

    def update_cursor_status(self, x, y):
        self.status_cursor.setText(f"  X: {x} px   Y: {y} px  ")

    def update_doc_tab_title(self):
        pct = int(self.canvas.zoom_level * 100)
        if self.loaded_filepath:
            fname = os.path.basename(self.loaded_filepath)
            self.lbl_doc_tab.setText(f"{fname} — Pág. {self.current_page_idx + 1} @ {pct}% (RGB/8)")
        else:
            self.lbl_doc_tab.setText(f"Nenhum documento aberto @ {pct}% (RGB/8)")

    def fit_canvas_to_view(self):
        vp = self.scroll_area.viewport()
        self.canvas.fit_to_viewport(vp.width(), vp.height())

    def load_file_data(self, filepath):
        self.pages_images.clear()
        self.page_rotations = []
        self.combo_pages.blockSignals(True)
        self.combo_pages.clear()

        if filepath.lower().endswith('.pdf'):
            doc = fitz.open(filepath)
            for page_idx in range(len(doc)):
                page = doc.load_page(page_idx)
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                self.pages_images.append(np.array(img))
                self.page_rotations.append(0)
                self.combo_pages.addItem(f"Página {page_idx + 1}")
        else:
            img = Image.open(filepath).convert("RGB")
            self.pages_images.append(np.array(img))
            self.page_rotations.append(0)
            self.combo_pages.addItem("Página 1")

        self.combo_pages.blockSignals(False)
        self.lbl_page.setText(f"de {len(self.pages_images)}")
        self.loaded_filepath = filepath

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Abrir Imagem ou PDF", "", "Arquivos Suportados (*.pdf *.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if not filepath:
            return

        self.canvas.regions.clear()
        self.load_file_data(filepath)
        self.current_page_idx = 0
        self.load_current_page()

    def load_current_page(self):
        if 0 <= self.current_page_idx < len(self.pages_images):
            img_np = self.pages_images[self.current_page_idx]
            h, w = img_np.shape[:2]
            self.canvas.set_image(img_np, self.current_page_idx)
            self.status_doc_info.setText(f"  Doc: {w} × {h} px  ")
            self.update_doc_tab_title()
            self.sync_region_list()

    def change_page(self, index):
        if index >= 0:
            self.current_page_idx = index
            self.load_current_page()

    def prev_page(self):
        if self.current_page_idx > 0:
            self.combo_pages.setCurrentIndex(self.current_page_idx - 1)

    def next_page(self):
        if self.current_page_idx < len(self.pages_images) - 1:
            self.combo_pages.setCurrentIndex(self.current_page_idx + 1)

    def rotate_current_page(self, direction):
        if not self.pages_images or not (0 <= self.current_page_idx < len(self.pages_images)):
            return

        img_np = self.pages_images[self.current_page_idx]
        h_orig, w_orig = img_np.shape[:2]

        if direction == 'cw':
            rotated_img = cv2.rotate(img_np, cv2.ROTATE_90_CLOCKWISE)
            self.page_rotations[self.current_page_idx] = (self.page_rotations[self.current_page_idx] + 90) % 360
            for r in self.canvas.regions:
                if r['page'] == self.current_page_idx:
                    old_cx, old_cy = r['cx'], r['cy']
                    r['cx'] = h_orig - old_cy
                    r['cy'] = old_cx
                    r['w'], r['h'] = r['h'], r['w']
                    r['angle'] = (r['angle'] + 90) % 360
        else:
            rotated_img = cv2.rotate(img_np, cv2.ROTATE_90_COUNTERCLOCKWISE)
            self.page_rotations[self.current_page_idx] = (self.page_rotations[self.current_page_idx] - 90) % 360
            for r in self.canvas.regions:
                if r['page'] == self.current_page_idx:
                    old_cx, old_cy = r['cx'], r['cy']
                    r['cx'] = old_cy
                    r['cy'] = w_orig - old_cx
                    r['w'], r['h'] = r['h'], r['w']
                    r['angle'] = (r['angle'] - 90) % 360

        self.pages_images[self.current_page_idx] = rotated_img
        self.load_current_page()

    def open_batch_rename(self):
        if not self.canvas.regions:
            QMessageBox.warning(self, "Aviso", "Nenhuma região foi criada para renomear.")
            return

        dialog = BatchRenameDialog(self, self.current_page_idx, len(self.pages_images))
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            prefix = settings['prefix']
            curr_num = settings['start']
            digits = settings['digits']
            suffix = settings['suffix']
            all_pages = settings['all_pages']

            for r in self.canvas.regions:
                if all_pages or r['page'] == self.current_page_idx:
                    num_str = str(curr_num).zfill(digits)
                    r['name'] = f"{prefix}{num_str}{suffix}"
                    curr_num += 1

            self.sync_region_list()
            self.canvas.update()

    def save_project(self):
        if not self.loaded_filepath:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo de imagem/PDF está aberto para salvar.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Projeto", "", "Projeto Andrew ScanStudio (*.json)"
        )
        if not save_path:
            return

        project_data = {
            "app": "Andrew ScanStudio",
            "filepath": self.loaded_filepath,
            "page_rotations": self.page_rotations,
            "current_page_idx": self.current_page_idx,
            "regions": self.canvas.regions
        }

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Sucesso", f"Projeto salvo com sucesso em:\n{save_path}")

    def load_project(self):
        json_path, _ = QFileDialog.getOpenFileName(
            self, "Carregar Projeto", "", "Projeto Andrew ScanStudio (*.json)"
        )
        if not json_path:
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao abrir arquivo JSON:\n{str(e)}")
            return

        filepath = project_data.get("filepath", "")
        if not os.path.exists(filepath):
            QMessageBox.warning(
                self, "Arquivo Não Encontrado",
                f"O arquivo original não foi localizado em:\n{filepath}\n\nSelecione a nova localização do arquivo."
            )
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Localizar Arquivo Original", "", "Arquivos Suportados (*.pdf *.png *.jpg *.jpeg *.bmp *.tiff)"
            )
            if not filepath:
                return

        self.load_file_data(filepath)

        saved_rotations = project_data.get("page_rotations", [])
        for page_idx, rot in enumerate(saved_rotations):
            if page_idx < len(self.pages_images):
                times = (rot % 360) // 90
                for _ in range(times):
                    self.pages_images[page_idx] = cv2.rotate(self.pages_images[page_idx], cv2.ROTATE_90_CLOCKWISE)
                self.page_rotations[page_idx] = rot % 360

        self.canvas.regions = project_data.get("regions", [])
        self.current_page_idx = project_data.get("current_page_idx", 0)

        if self.current_page_idx < self.combo_pages.count():
            self.combo_pages.setCurrentIndex(self.current_page_idx)

        self.load_current_page()
        QMessageBox.information(self, "Sucesso", "Projeto carregado com sucesso!")

    def sync_region_list(self):
        self.list_regions.blockSignals(True)
        self.list_regions.clear()
        for idx, r in enumerate(self.canvas.regions):
            self.list_regions.addItem(f"▣  {r['name']}   (Pág. {r['page'] + 1})")
        if 0 <= self.canvas.selected_index < len(self.canvas.regions):
            self.list_regions.setCurrentRow(self.canvas.selected_index)
        self.list_regions.blockSignals(False)
        self.populate_controls()

    def on_region_selected(self, index):
        self.sync_region_list()

    def on_list_item_changed(self, row):
        if 0 <= row < len(self.canvas.regions):
            self.canvas.selected_index = row
            region = self.canvas.regions[row]
            if region['page'] != self.current_page_idx:
                self.combo_pages.setCurrentIndex(region['page'])
            self.canvas.update()
            self.populate_controls()

    def populate_controls(self):
        idx = self.canvas.selected_index
        if 0 <= idx < len(self.canvas.regions):
            r = self.canvas.regions[idx]
            self.txt_name.blockSignals(True)
            self.spin_angle.blockSignals(True)
            self.spin_w.blockSignals(True)
            self.spin_h.blockSignals(True)

            self.txt_name.setText(r['name'])
            self.spin_angle.setValue(r['angle'])
            self.spin_w.setValue(int(r['w']))
            self.spin_h.setValue(int(r['h']))

            self.txt_name.blockSignals(False)
            self.spin_angle.blockSignals(False)
            self.spin_w.blockSignals(False)
            self.spin_h.blockSignals(False)

    def update_region_properties(self):
        idx = self.canvas.selected_index
        if 0 <= idx < len(self.canvas.regions):
            r = self.canvas.regions[idx]
            r['name'] = self.txt_name.text().strip() or f"crop_{idx+1}"
            r['angle'] = self.spin_angle.value()
            r['w'] = float(self.spin_w.value())
            r['h'] = float(self.spin_h.value())
            self.canvas.update()

            item = self.list_regions.item(idx)
            if item:
                item.setText(f"▣  {r['name']}   (Pág. {r['page'] + 1})")

    def delete_region(self):
        idx = self.canvas.selected_index
        if 0 <= idx < len(self.canvas.regions):
            del self.canvas.regions[idx]
            self.canvas.selected_index = -1
            self.sync_region_list()
            self.canvas.update()

    def export_crops(self):
        if not self.canvas.regions:
            QMessageBox.warning(self, "Aviso", "Nenhuma região foi marcada para exportação.")
            return

        export_dir = QFileDialog.getExistingDirectory(self, "Selecione a Pasta de Destino para Exportar")
        if not export_dir:
            return

        fmt_text = self.combo_format.currentText()
        ext = fmt_text.split("(")[1].replace(")", "").strip()

        saved_count = 0
        for r in self.canvas.regions:
            page_idx = r['page']
            img_np = self.pages_images[page_idx]

            cropped = crop_oriented_rect(
                img_np,
                center=(r['cx'], r['cy']),
                size=(r['w'], r['h']),
                angle=r['angle']
            )

            file_name = f"{r['name']}{ext}"
            save_path = os.path.join(export_dir, file_name)

            cropped_bgr = cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR)

            params = []
            if ext in ['.jpg', '.jpeg']:
                params = [int(cv2.IMWRITE_JPEG_QUALITY), 95]

            cv2.imwrite(save_path, cropped_bgr, params)
            saved_count += 1

        QMessageBox.information(
            self, "Sucesso", f"{saved_count} imagens foram exportadas em formato {ext.upper()} com sucesso para:\n{export_dir}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(PHOTOSHOP_QSS)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
