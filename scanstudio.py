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
    QLineEdit, QFormLayout, QGroupBox, QMessageBox, QScrollArea, QComboBox,
    QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QTransform, QPolygonF


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


class BatchRenameDialog(QDialog):
    """Diálogo para configurar a renomeação automática em lote."""
    def __init__(self, parent=None, current_page_idx=0, total_pages=1):
        super().__init__(parent)
        self.setWindowTitle("Andrew ScanStudio - Renomear em Lote")
        self.resize(380, 260)

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
        self.lbl_preview.setStyleSheet("font-weight: bold; color: #1565C0; margin: 8px 0;")
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


class ImageCanvas(QWidget):
    region_selected = pyqtSignal(int)
    region_added = pyqtSignal()
    region_updated = pyqtSignal()
    zoom_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = None
        self.image_np = None
        self.regions = []  # List: {'cx', 'cy', 'w', 'h', 'angle', 'name', 'page'}
        self.selected_index = -1
        self.current_page = 0

        self.zoom_level = 1.0
        self.scale_factor = 1.0

        self.is_drawing = False
        self.drag_mode = None  # 'MOVE', 'ROTATE', 'RESIZE_TL', 'RESIZE_TR', 'RESIZE_BR', 'RESIZE_BL'
        self.drag_start_mouse = QPointF()
        self.drag_start_region = {}

        self.setMouseTracking(True)

    def set_image(self, img_np, page_num):
        self.image_np = img_np
        self.current_page = page_num
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

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

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
        if event.button() != Qt.LeftButton or not self.pixmap:
            return

        mouse_disp = event.pos()
        mouse_img = mouse_disp / self.scale_factor

        handle_type = self.hit_test_handle(mouse_disp)
        if handle_type:
            self.drag_mode = handle_type
            self.drag_start_mouse = mouse_img
            self.drag_start_region = dict(self.regions[self.selected_index])
            return

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
            self.setCursor(Qt.ArrowCursor)
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

        for idx, r in enumerate(self.regions):
            if r['page'] != self.current_page:
                continue

            is_selected = (idx == self.selected_index)
            pen_color = QColor(0, 255, 0) if not is_selected else QColor(255, 50, 50)
            pen = QPen(pen_color, 2 if not is_selected else 3)
            painter.setPen(pen)

            transform = QTransform()
            transform.translate(r['cx'] * self.scale_factor, r['cy'] * self.scale_factor)
            transform.rotate(r['angle'])

            w_s = r['w'] * self.scale_factor
            h_s = r['h'] * self.scale_factor
            rect = QRectF(-w_s / 2, -h_s / 2, w_s, h_s)

            polygon = transform.map(QPolygonF(rect))
            painter.drawPolygon(polygon)

            painter.drawText(int(transform.map(QPointF(-w_s / 2, -h_s / 2 - 5)).x()),
                             int(transform.map(QPointF(-w_s / 2, -h_s / 2 - 5)).y()),
                             r['name'])

            if is_selected:
                handles = self.get_handle_positions(r)
                
                top_mid = QPointF(
                    (transform.map(QPointF(0, -h_s / 2))).x(),
                    (transform.map(QPointF(0, -h_s / 2))).y()
                )
                painter.setPen(QPen(QColor(0, 150, 255), 1, Qt.DashLine))
                painter.drawLine(top_mid, handles['ROT'])

                painter.setPen(QPen(QColor(0, 200, 0), 2))
                painter.setBrush(QColor(100, 255, 100))
                painter.drawEllipse(handles['ROT'], 5, 5)

                painter.setPen(QPen(QColor(0, 100, 255), 2))
                painter.setBrush(QColor(255, 255, 255))
                for key in ['TL', 'TR', 'BR', 'BL']:
                    pt = handles[key]
                    painter.drawRect(QRectF(pt.x() - 4, pt.y() - 4, 8, 8))

        if self.is_drawing:
            pen = QPen(QColor(0, 150, 255), 2, Qt.DashLine)
            painter.setPen(pen)
            curr_pos = self.mapFromGlobal(self.cursor().pos())
            x1 = self.drag_start_region['x'] * self.scale_factor
            y1 = self.drag_start_region['y'] * self.scale_factor
            painter.drawRect(QRectF(QPointF(x1, y1), curr_pos))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Andrew ScanStudio")
        self.resize(1280, 768)

        self.pages_images = []
        self.page_rotations = []
        self.current_page_idx = 0
        self.loaded_filepath = None

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- ÁREA DA ESQUERDA: CANVAS E FERRAMENTAS ---
        left_layout = QVBoxLayout()
        
        # Barra 1: Arquivos e Projetos
        top_bar_1 = QHBoxLayout()
        self.btn_open = QPushButton("📁 Abrir Arquivo")
        self.btn_open.clicked.connect(self.open_file)
        top_bar_1.addWidget(self.btn_open)

        self.btn_save_proj = QPushButton("💾 Salvar Projeto")
        self.btn_save_proj.clicked.connect(self.save_project)
        top_bar_1.addWidget(self.btn_save_proj)

        self.btn_load_proj = QPushButton("📂 Carregar Projeto")
        self.btn_load_proj.clicked.connect(self.load_project)
        top_bar_1.addWidget(self.btn_load_proj)

        self.btn_batch_rename = QPushButton("🏷️ Renomear em Lote")
        self.btn_batch_rename.setStyleSheet("font-weight: bold; color: #0D47A1;")
        self.btn_batch_rename.clicked.connect(self.open_batch_rename)
        top_bar_1.addWidget(self.btn_batch_rename)

        self.lbl_page = QLabel("Página: -")
        self.combo_pages = QComboBox()
        self.combo_pages.currentIndexChanged.connect(self.change_page)
        top_bar_1.addWidget(self.lbl_page)
        top_bar_1.addWidget(self.combo_pages)

        left_layout.addLayout(top_bar_1)

        # Barra 2: Rotações de Página e Zoom
        top_bar_2 = QHBoxLayout()
        self.btn_rot_ccw = QPushButton("↺ 90° Anti-horário")
        self.btn_rot_ccw.clicked.connect(lambda: self.rotate_current_page('ccw'))
        top_bar_2.addWidget(self.btn_rot_ccw)

        self.btn_rot_cw = QPushButton("↻ 90° Horário")
        self.btn_rot_cw.clicked.connect(lambda: self.rotate_current_page('cw'))
        top_bar_2.addWidget(self.btn_rot_cw)

        top_bar_2.addWidget(QLabel(" Zoom:"))

        self.btn_zoom_in = QPushButton("🔍 +")
        self.btn_zoom_in.clicked.connect(lambda: self.canvas.zoom_in())
        top_bar_2.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton("🔍 -")
        self.btn_zoom_out.clicked.connect(lambda: self.canvas.zoom_out())
        top_bar_2.addWidget(self.btn_zoom_out)

        self.btn_zoom_reset = QPushButton("100%")
        self.btn_zoom_reset.clicked.connect(lambda: self.canvas.reset_zoom())
        top_bar_2.addWidget(self.btn_zoom_reset)

        self.lbl_zoom = QLabel("100%")
        top_bar_2.addWidget(self.lbl_zoom)
        top_bar_2.addStretch()

        left_layout.addLayout(top_bar_2)

        self.canvas = ImageCanvas()
        self.canvas.region_selected.connect(self.on_region_selected)
        self.canvas.region_added.connect(self.sync_region_list)
        self.canvas.region_updated.connect(self.populate_controls)
        self.canvas.zoom_changed.connect(self.update_zoom_label)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas)
        scroll_area.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(scroll_area)

        main_layout.addLayout(left_layout, stretch=3)

        # --- ÁREA DA DIREITA: CONTROLES ---
        right_layout = QVBoxLayout()

        group_list = QGroupBox("Regiões Selecionadas")
        layout_list = QVBoxLayout(group_list)
        self.list_regions = QListWidget()
        self.list_regions.currentRowChanged.connect(self.on_list_item_changed)
        layout_list.addWidget(self.list_regions)
        
        self.btn_delete = QPushButton("Excluir Região Selecionada")
        self.btn_delete.clicked.connect(self.delete_region)
        layout_list.addWidget(self.btn_delete)
        
        right_layout.addWidget(group_list)

        group_controls = QGroupBox("Ajuste Fino / Numérico")
        form_layout = QFormLayout(group_controls)

        self.txt_name = QLineEdit()
        self.txt_name.textChanged.connect(self.update_region_properties)
        form_layout.addRow("Nome do Arquivo:", self.txt_name)

        self.spin_angle = QDoubleSpinBox()
        self.spin_angle.setRange(-180.0, 180.0)
        self.spin_angle.setSingleStep(0.5)
        self.spin_angle.setSuffix(" °")
        self.spin_angle.valueChanged.connect(self.update_region_properties)
        form_layout.addRow("Inclinação:", self.spin_angle)

        self.spin_w = QSpinBox()
        self.spin_w.setRange(1, 10000)
        self.spin_w.valueChanged.connect(self.update_region_properties)
        form_layout.addRow("Largura (px):", self.spin_w)

        self.spin_h = QSpinBox()
        self.spin_h.setRange(1, 10000)
        self.spin_h.valueChanged.connect(self.update_region_properties)
        form_layout.addRow("Altura (px):", self.spin_h)

        right_layout.addWidget(group_controls)

        # Seletor de Formato de Exportação
        group_export = QGroupBox("Exportação")
        layout_export = QVBoxLayout(group_export)
        
        form_fmt = QFormLayout()
        self.combo_format = QComboBox()
        self.combo_format.addItems(["JPG (.jpg)", "PNG (.png)", "WEBP (.webp)"])
        form_fmt.addRow("Formato do Arquivo:", self.combo_format)
        layout_export.addLayout(form_fmt)

        self.btn_export = QPushButton("🚀 Exportar Todos os Recortes")
        self.btn_export.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 10px;")
        self.btn_export.clicked.connect(self.export_crops)
        layout_export.addWidget(self.btn_export)

        right_layout.addWidget(group_export)

        main_layout.addLayout(right_layout, stretch=1)

    def update_zoom_label(self, val):
        self.lbl_zoom.setText(f"{int(val * 100)}%")

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
        self.lbl_page.setText(f"Total Páginas: {len(self.pages_images)}")
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
            self.canvas.set_image(img_np, self.current_page_idx)
            self.sync_region_list()

    def change_page(self, index):
        if index >= 0:
            self.current_page_idx = index
            self.load_current_page()

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
            self.list_regions.addItem(f"[{r['name']}] (Pág. {r['page'] + 1})")
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
                item.setText(f"[{r['name']}] (Pág. {r['page'] + 1})")

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

        # Obter extensão selecionada pelo usuário (.jpg, .png, .webp)
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

            # Parâmetros de qualidade de salvamento
            params = []
            if ext in ['.jpg', '.jpeg']:
                params = [int(cv2.IMWRITE_JPEG_QUALITY), 95]  # Alta qualidade JPG

            cv2.imwrite(save_path, cropped_bgr, params)
            saved_count += 1

        QMessageBox.information(
            self, "Sucesso", f"{saved_count} imagens foram exportadas em formato {ext.upper()} com sucesso para:\n{export_dir}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
