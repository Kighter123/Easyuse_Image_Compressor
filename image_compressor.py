import sys
import os
import json
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QMessageBox, QSpinBox,
                             QListWidget,  QGroupBox, QFormLayout, QCheckBox,
                             QFrame, QSplitter, QProgressDialog,  QInputDialog,
                             QMenu, QAction)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (QFont, QIcon, QColor, QPainter, QPen, QBrush,
                         QLinearGradient,)
from PIL import Image

class SciFiBackground(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.parent = parent
        self.points = []
        self.generate_random_points()
        
    def generate_random_points(self):
        self.points = []
        for _ in range(50):
            x = random.randint(0, self.width())
            y = random.randint(0, self.height())
            size = random.randint(1, 3)
            self.points.append((x, y, size))
            
    def resizeEvent(self, event):
        self.generate_random_points()
        super().resizeEvent(event)
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(240, 247, 255))
        gradient.setColorAt(1, QColor(227, 242, 253))
        painter.fillRect(self.rect(), QBrush(gradient))
        
        painter.setPen(QPen(QColor(187, 222, 251, 100), 1))
        step = 30
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)
            
        for x, y, size in self.points:
            painter.setPen(QPen(QColor(66, 165, 245, 150), size))
            painter.drawPoint(x, y)

class ImageCompressor(QMainWindow):
    def __init__(self):
        super().__init__()
        # 存储多组比例设置 (width, height, quality, crop)
        self.ratio_presets = []  
        # 存储保存的尺寸预设
        self.size_presets = {}
        # 预设文件路径
        self.presets_file = os.path.join(os.path.expanduser("~"), ".image_compressor_presets.json")
        # 处理队列 - 存储预设配置
        self.process_queue = []
        
        self.init_ui()
        self.folder_path = ""
        # 加载保存的尺寸预设
        self.load_size_presets()
        
        # 科幻风格动画定时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(50)  # 每50ms更新一次动画
        self.animation_frame = 0

    def init_ui(self):
        # 窗口基础设置
        self.setWindowTitle("图片批量压缩工具")
        self.setGeometry(100, 100, 1600, 1150)
        
        
        # 全局字体和样式
        font = QFont("Microsoft YaHei UI", 18, QFont.Bold)
        self.setFont(font)
        
        # 创建装饰性背景组件 - 科幻风格
        self.decorative_bg = SciFiBackground(self)
        self.decorative_bg.setGeometry(0, 0, self.width(), self.height())
        self.decorative_bg.lower()  # 置于底层
        
        # 样式表
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #ffffff;
            }
            
            /* 基础GroupBox样式 */
            QGroupBox {
                border: 1px solid #b3d1ff;
                border-radius: 12px;
                padding: 15px;
                background-color: rgba(255, 255, 255, 0.9);
                margin: 0;
            }
            
            /* 区域特定样式 */
            #paramGroup {
                border-color: #90caf9;
            }
            
            #presetGroup {
                border-color: #64b5f6;
            }
            
            #queueGroup {
                border-color: #42a5f5;
            }
            
            /* 标题标签样式 */
            .section-title {
                color: #0a4da2;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI';
                font-size: 12pt;
                margin-bottom: 5px;
                padding-left: 5px;
            }
            
            QPushButton {
                background-color: #1e88e5;
                color: #ffffff;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 12pt;
                border: 1px solid #64b5f6;
                font-family: 'Microsoft YaHei UI';
            }
            
            QPushButton:hover { 
                background-color: #42a5f5;
                border-color: #90caf9;
            }
            
            QPushButton:pressed { 
                background-color: #1565c0;
            }
            
            QPushButton:disabled { 
                background-color: #e3f2fd;
                border-color: #bbdefb;
                color: #90caf9;
            }
            
            QSpinBox, QSlider {
                border: 1px solid #b3d1ff;
                border-radius: 6px;
                padding: 8px;
                background-color: #f0f7ff;
                color: #0d47a1;
                font-family: 'Microsoft YaHei UI';
            }
            
            QSpinBox:hover, QSlider:hover {
                border-color: #64b5f6;
            }
            
            QListWidget {
                border: 1px solid #b3d1ff;
                border-radius: 8px;
                padding: 10px;
                background-color: #f0f7ff;
                alternate-background-color: #e3f2fd;
                color: #0d47a1;
                font-family: 'Microsoft YaHei UI';
            }
            
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            
            QListWidget::item:selected {
                background-color: #1e88e5;
                color: #ffffff;
            }
            
            QLabel { 
                color: #0d47a1;
                font-family: 'Microsoft YaHei UI';
            }
            
            QCheckBox { 
                color: #0d47a1;
                spacing: 8px;
                font-family: 'Microsoft YaHei UI';
            }
            
            QMenuBar { 
                background-color: #f0f7ff;
                border-bottom: 1px solid #bbdefb;
            }
            
            QMenuBar::item { 
                background-color: transparent;
                padding: 6px 12px;
                font-family: 'Microsoft YaHei UI';
                color: #0d47a1;
            }
            
            QMenuBar::item:selected { 
                background-color: #e3f2fd;
                border-radius: 4px;
            }
            
            QMenu { 
                background-color: #f0f7ff;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                padding: 4px 0;
                font-family: 'Microsoft YaHei UI';
                color: #0d47a1;
            }
            
            QMenu::item { 
                padding: 8px 24px;
                color: #0d47a1;
            }
            
            QMenu::item:selected { 
                background-color: #42a5f5;
                color: white;
                border-radius: 4px;
            }
        """)

        # 中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 10, 20, 20)
        
        # 标题和分隔线
        title_label = QLabel("图片压缩工具")
        title_label.setFont(QFont("Microsoft YaHei UI", 36, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #0a4da2; 
            margin-bottom: 5px;
        """)
        main_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("@Kighter123")
        subtitle_label.setFont(QFont("Microsoft YaHei UI", 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #1565c0; margin-bottom: 10px;")
        main_layout.addWidget(subtitle_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #90caf9, stop:0.5 #42a5f5, stop:1 #90caf9); height: 2px;")
        main_layout.addWidget(line)

        # 1. 文件夹选择区域
        folder_frame = QFrame()
        folder_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient( x1:0 y1:0, x2:1 y2:1,
                                            stop:0 #bbdefb, stop:1 #90caf9);
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #64b5f6;
            }
        """)
        folder_layout = QHBoxLayout(folder_frame)
        folder_layout.setSpacing(15)
        
        self.folder_label = QLabel("目标文件夹: 未选择", self)
        self.folder_label.setMinimumHeight(45)
        self.folder_label.setStyleSheet("""
            padding: 8px;
            color: #0d47a1;
            font-weight: 600;
            font-size: 12pt;
            font-family: 'Microsoft YaHei UI';
            background-color: rgba(255, 255, 255, 0.5);
            border-radius: 8px;
            border: 1px solid rgba(66, 165, 245, 0.3);
        """)
        self.folder_label.setWordWrap(True)
        
        self.folder_btn = QPushButton("选择文件夹", self)
        self.folder_btn.setMinimumSize(160, 50)
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 136, 229, 0.8);
                color: #ffffff;
                border: 1px solid rgba(66, 165, 245, 0.7);
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei UI';
            }
            QPushButton:hover {
                background-color: rgba(66, 165, 245, 0.9);
                border-color: rgba(90, 170, 245, 0.9);
            }
            QPushButton:pressed {
                background-color: rgba(21, 101, 192, 0.9);
            }
        """)
        self.folder_btn.clicked.connect(self.select_folder)
        
        folder_layout.addWidget(self.folder_label, 1)
        folder_layout.addWidget(self.folder_btn, 0, Qt.AlignRight)
        main_layout.addWidget(folder_frame)

        # 2. 主要参数区域（分割器）
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #90caf9;
                width: 4px;
                margin: 0 2px;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #42a5f5;
            }
        """)
        
        # 左侧参数区域
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(15)
        
        # 参数设置区域
        param_title = QLabel("参数设置")
        param_title.setProperty("class", "section-title")
        left_layout.addWidget(param_title)
        
        current_ratio_group = QGroupBox()
        current_ratio_group.setObjectName("paramGroup")
        current_ratio_group.setTitle("")
        current_ratio_form = QFormLayout()
        current_ratio_form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        current_ratio_form.setSpacing(15)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 4000)
        self.width_spin.setValue(800)
        self.width_spin.setMinimumHeight(40)
        current_ratio_form.addRow("输出宽度 (px):", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 4000)
        self.height_spin.setValue(600)
        self.height_spin.setMinimumHeight(40)
        current_ratio_form.addRow("输出高度 (px):", self.height_spin)
        
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(10, 100)
        self.quality_spin.setValue(80)
        self.quality_spin.setMinimumHeight(40)
        current_ratio_form.addRow("压缩质量 (10-100):", self.quality_spin)
        
        self.crop_checkbox = QCheckBox("比例不匹配时启用智能居中裁剪")
        self.crop_checkbox.setChecked(True)
        self.crop_checkbox.setStyleSheet("font-size: 11pt;")
        current_ratio_form.addRow(self.crop_checkbox)
        
        # 参数设置区按钮布局 - 并排显示
        param_buttons_layout = QHBoxLayout()
        param_buttons_layout.setSpacing(10)
        
        # "添加到预设"按钮
        self.add_to_preset_btn = QPushButton("添加到预设")
        self.add_to_preset_btn.setIcon(QIcon.fromTheme("document-save"))
        self.add_to_preset_btn.setMinimumHeight(50)
        self.add_to_preset_btn.clicked.connect(self.save_current_as_preset)
        param_buttons_layout.addWidget(self.add_to_preset_btn)
        
        # "添加到队列"按钮
        self.add_to_queue_btn = QPushButton("添加到队列")
        self.add_to_queue_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_to_queue_btn.setMinimumHeight(50)
        self.add_to_queue_btn.clicked.connect(self.add_current_to_queue)
        param_buttons_layout.addWidget(self.add_to_queue_btn)
        
        current_ratio_form.addRow(param_buttons_layout)
        current_ratio_group.setLayout(current_ratio_form)
        left_layout.addWidget(current_ratio_group)
        
        # 已保存的尺寸预设区域
        preset_title = QLabel("尺寸预设")
        preset_title.setProperty("class", "section-title")
        left_layout.addWidget(preset_title)
        
        self.presets_group = QGroupBox()
        self.presets_group.setObjectName("presetGroup")
        self.presets_group.setTitle("")
        presets_layout = QVBoxLayout()
        
        self.presets_list = QListWidget()
        self.presets_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.presets_list.customContextMenuRequested.connect(self.show_preset_context_menu)
        self.presets_list.itemDoubleClicked.connect(self.load_preset)
        # 支持选择多个预设
        self.presets_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.presets_list.setMinimumHeight(200)
        
        presets_layout.addWidget(self.presets_list)
        
        # 预设管理按钮布局
        preset_management_layout = QHBoxLayout()
        preset_management_layout.setSpacing(10)
        
        # "删除选中预设"按钮（新增）
        self.delete_selected_presets_btn = QPushButton("删除选中预设")
        self.delete_selected_presets_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_selected_presets_btn.setMinimumHeight(40)
        self.delete_selected_presets_btn.clicked.connect(self.delete_selected_presets)
        preset_management_layout.addWidget(self.delete_selected_presets_btn)
        
        # "删除所有预设"按钮
        self.delete_all_presets_btn = QPushButton("删除所有预设")
        self.delete_all_presets_btn.setIcon(QIcon.fromTheme("edit-clear-all"))
        self.delete_all_presets_btn.setMinimumHeight(40)
        self.delete_all_presets_btn.clicked.connect(self.delete_all_presets)
        preset_management_layout.addWidget(self.delete_all_presets_btn)
        
        presets_layout.addLayout(preset_management_layout)
        self.presets_group.setLayout(presets_layout)
        left_layout.addWidget(self.presets_group)
        
        left_layout.addStretch(1)
        splitter.addWidget(left_frame)
        
        # 右侧处理队列区域
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setSpacing(15)
        
        # 处理队列区域
        queue_title = QLabel("处理队列")
        queue_title.setProperty("class", "section-title")
        right_layout.addWidget(queue_title)
        
        self.queue_group = QGroupBox()
        self.queue_group.setObjectName("queueGroup")
        self.queue_group.setTitle("")
        queue_layout = QVBoxLayout()
        
        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(500)
        # 支持选择多个队列项
        self.queue_list.setSelectionMode(QListWidget.ExtendedSelection)
        queue_layout.addWidget(self.queue_list)
        
        queue_buttons_layout = QHBoxLayout()
        queue_buttons_layout.setSpacing(10)
        
        # 1. 导入所有预设按钮
        self.import_all_presets_btn = QPushButton("导入所有预设")
        self.import_all_presets_btn.setIcon(QIcon.fromTheme("document-properties"))
        self.import_all_presets_btn.setMinimumHeight(50)
        self.import_all_presets_btn.clicked.connect(self.import_all_presets)
        queue_buttons_layout.addWidget(self.import_all_presets_btn)
        
        # 2. 导入预设按钮
        self.import_preset_btn = QPushButton("导入预设")
        self.import_preset_btn.setIcon(QIcon.fromTheme("document-import"))
        self.import_preset_btn.setMinimumHeight(50)
        self.import_preset_btn.clicked.connect(self.import_presets)
        queue_buttons_layout.addWidget(self.import_preset_btn)
        
        # 3. 删除选中队列按钮
        self.delete_selected_queue_btn = QPushButton("删除选中队列")
        self.delete_selected_queue_btn.setIcon(QIcon.fromTheme("edit-delete"))
        self.delete_selected_queue_btn.setMinimumHeight(50)
        self.delete_selected_queue_btn.clicked.connect(self.delete_selected_queue)
        queue_buttons_layout.addWidget(self.delete_selected_queue_btn)
        
        # 4. 清空队列按钮
        self.clear_queue_btn = QPushButton("清空队列")
        self.clear_queue_btn.setIcon(QIcon.fromTheme("edit-clear"))
        self.clear_queue_btn.setMinimumHeight(50)
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        queue_buttons_layout.addWidget(self.clear_queue_btn)
        
        queue_layout.addLayout(queue_buttons_layout)
        self.queue_group.setLayout(queue_layout)
        right_layout.addWidget(self.queue_group)
        
        # 处理按钮区域
        process_buttons_layout = QHBoxLayout()
        process_buttons_layout.setSpacing(15)
        
        self.process_btn = QPushButton("开始处理图片")
        self.process_btn.setIcon(QIcon.fromTheme("system-run"))
        self.process_btn.setMinimumSize(200, 110)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #1d7eff;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
        """)
        self.process_btn.clicked.connect(self.process_images)
        process_buttons_layout.addWidget(self.process_btn)
        
        self.output_folder_btn = QPushButton("设置输出文件夹")
        self.output_folder_btn.setIcon(QIcon.fromTheme("folder-open"))
        self.output_folder_btn.setMinimumHeight(110)
        self.output_folder_btn.clicked.connect(self.set_output_folder)
        process_buttons_layout.addWidget(self.output_folder_btn)
        
        right_layout.addLayout(process_buttons_layout)
        right_layout.addStretch(1)
        splitter.addWidget(right_frame)
        
        # 设置分割器比例
        splitter.setSizes([700, 1300])
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().setStyleSheet("color: #0d47a1; font-size: 10pt; padding: 5px;")
        self.statusBar().showMessage("就绪")

    def select_folder(self):
        """选择目标文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹", os.path.expanduser("~"))
        if folder:
            self.folder_path = folder
            self.folder_label.setText(f"目标文件夹: {folder}")
            self.statusBar().showMessage(f"已选择文件夹: {folder}")

    def add_current_to_queue(self):
        """将当前参数设置添加到处理队列"""
        # 获取当前参数设置
        current_settings = {
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'quality': self.quality_spin.value(),
            'crop': self.crop_checkbox.isChecked()
        }
        
        # 在队列列表中显示
        item_text = f"宽: {current_settings['width']}, 高: {current_settings['height']}, 质量: {current_settings['quality']}, 裁剪: {'是' if current_settings['crop'] else '否'}"
        self.queue_list.addItem(item_text)
        
        # 存储实际设置以便处理时使用
        self.process_queue.append(current_settings)
        
        self.statusBar().showMessage("已将当前设置添加到队列")

    def clear_queue(self):
        """清空处理队列"""
        if self.queue_list.count() > 0:
            reply = QMessageBox.question(
                self, "确认", "确定要清空队列吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.queue_list.clear()
                self.process_queue = []
                self.statusBar().showMessage("队列已清空")
        else:
            QMessageBox.information(self, "提示", "队列为空")

    def delete_selected_queue(self):
        """删除选中的队列项"""
        selected_items = self.queue_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的队列项")
            return
            
        # 获取选中项的索引
        selected_indices = sorted([self.queue_list.row(item) for item in selected_items], reverse=True)
        
        # 从队列中删除
        for index in selected_indices:
            del self.process_queue[index]
        
        # 从列表中删除
        for item in selected_items:
            self.queue_list.takeItem(self.queue_list.row(item))
            
        self.statusBar().showMessage(f"已删除 {len(selected_items)} 个队列项")

    def save_current_as_preset(self):
        """保存当前配置为预设"""
        name, ok = QInputDialog.getText(self, "保存预设", "请输入预设名称:")
        if ok and name:
            if name in self.size_presets:
                reply = QMessageBox.question(
                    self, "覆盖", f"预设 '{name}' 已存在，是否覆盖？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                    
            # 保存当前设置
            self.size_presets[name] = {
                'width': self.width_spin.value(),
                'height': self.height_spin.value(),
                'quality': self.quality_spin.value(),
                'crop': self.crop_checkbox.isChecked()
            }
            
            # 更新列表显示
            self.update_presets_list()
            # 保存到文件
            self.save_size_presets()
            self.statusBar().showMessage(f"已添加预设: {name}")

    def delete_selected_presets(self):
        """删除选中的预设"""
        selected_items = self.presets_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的预设")
            return
            
        # 确认删除
        count = len(selected_items)
        reply = QMessageBox.question(
            self, "确认", f"确定要删除选中的 {count} 个预设吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 获取选中的预设名称
            selected_names = [item.text() for item in selected_items]
            
            # 从预设字典中删除
            for name in selected_names:
                if name in self.size_presets:
                    del self.size_presets[name]
            
            # 更新列表显示
            self.update_presets_list()
            # 保存更改
            self.save_size_presets()
            
            self.statusBar().showMessage(f"已删除 {count} 个预设")

    def delete_all_presets(self):
        """删除所有预设"""
        if not self.size_presets:
            QMessageBox.information(self, "提示", "没有可删除的预设")
            return
            
        reply = QMessageBox.question(
            self, "确认", "确定要删除所有预设吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.size_presets = {}
            self.update_presets_list()
            self.save_size_presets()
            self.statusBar().showMessage("已删除所有预设")

    def import_presets(self):
        """导入单个预设到处理队列"""
        if not self.size_presets:
            QMessageBox.information(self, "提示", "没有可导入的预设，请先创建预设")
            return
            
        # 显示预设选择对话框
        preset_names = list(self.size_presets.keys())
        item, ok = QInputDialog.getItem(
            self, "选择预设", "请选择要导入的预设:", 
            preset_names, 0, False
        )
        
        if ok and item:
            # 获取选中的预设
            preset = self.size_presets[str(item)]
            
            # 添加到队列
            item_text = f"宽: {preset['width']}, 高: {preset['height']}, 质量: {preset['quality']}, 裁剪: {'是' if preset['crop'] else '否'} (预设: {item})"
            self.queue_list.addItem(item_text)
            self.process_queue.append(preset)
            
            self.statusBar().showMessage(f"已导入预设: {item} 到处理队列")

    def import_all_presets(self):
        """导入所有预设到处理队列"""
        if not self.size_presets:
            QMessageBox.information(self, "提示", "没有可导入的预设，请先创建预设")
            return
            
        # 确认提示
        reply = QMessageBox.question(
            self, "确认", f"确定要导入所有 {len(self.size_presets)} 个预设到处理队列吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            imported_count = 0
            for name, preset in self.size_presets.items():
                # 添加到队列
                item_text = f"宽: {preset['width']}, 高: {preset['height']}, 质量: {preset['quality']}, 裁剪: {'是' if preset['crop'] else '否'} (预设: {name})"
                self.queue_list.addItem(item_text)
                self.process_queue.append(preset)
                imported_count += 1
                
            self.statusBar().showMessage(f"已导入 {imported_count} 个预设到处理队列")

    def load_size_presets(self):
        """从文件加载尺寸预设"""
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    self.size_presets = json.load(f)
                self.update_presets_list()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载预设失败: {str(e)}")
            self.size_presets = {}

    def save_size_presets(self):
        """保存尺寸预设到文件"""
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.size_presets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存预设失败: {str(e)}")

    def update_presets_list(self):
        """更新预设列表显示"""
        self.presets_list.clear()
        for name in self.size_presets.keys():
            self.presets_list.addItem(name)

    def show_preset_context_menu(self, position):
        """显示预设右键菜单"""
        if not self.presets_list.selectedItems():
            return
            
        menu = QMenu()
        load_action = QAction("加载", self)
        rename_action = QAction("重命名", self)
        delete_action = QAction("删除", self)
        
        load_action.triggered.connect(self.load_preset)
        rename_action.triggered.connect(self.rename_preset)
        delete_action.triggered.connect(self.delete_selected_presets)  # 使用新的删除选中功能
        
        menu.addAction(load_action)
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        
        menu.exec_(self.presets_list.mapToGlobal(position))

    def load_preset(self):
        """加载选中的预设"""
        selected = self.presets_list.currentItem()
        if not selected:
            return
            
        name = selected.text()
        if name in self.size_presets:
            preset = self.size_presets[name]
            self.width_spin.setValue(preset['width'])
            self.height_spin.setValue(preset['height'])
            self.quality_spin.setValue(preset['quality'])
            self.crop_checkbox.setChecked(preset['crop'])
            self.statusBar().showMessage(f"已加载预设: {name}")

    def rename_preset(self):
        """重命名预设"""
        selected = self.presets_list.currentItem()
        if not selected:
            return
            
        old_name = selected.text()
        new_name, ok = QInputDialog.getText(self, "重命名预设", "请输入新名称:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            if new_name in self.size_presets:
                QMessageBox.warning(self, "错误", f"预设 '{new_name}' 已存在")
                return
                
            self.size_presets[new_name] = self.size_presets[old_name]
            del self.size_presets[old_name]
            self.update_presets_list()
            self.save_size_presets()
            self.statusBar().showMessage(f"已重命名预设: {old_name} -> {new_name}")

    def set_output_folder(self):
        """设置输出文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹", self.folder_path or os.path.expanduser("~"))
        if folder:
            self.output_folder = folder
            self.statusBar().showMessage(f"已设置输出文件夹: {folder}")

    def process_images(self):
        """处理队列中的预设配置"""
        if not self.folder_path:
            QMessageBox.warning(self, "警告", "请先选择图片文件夹")
            return
            
        if len(self.process_queue) == 0:
            QMessageBox.warning(self, "警告", "处理队列为空，请先添加配置到队列")
            return
            
        # 获取所有图片文件
        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
        image_files = [
            os.path.join(self.folder_path, f) 
            for f in os.listdir(self.folder_path) 
            if f.lower().endswith(image_extensions)
        ]
        
        if not image_files:
            QMessageBox.warning(self, "警告", "所选文件夹中没有图片文件")
            return
            
        # 如果未设置输出文件夹，使用源文件夹
        output_folder = getattr(self, 'output_folder', None) or self.folder_path
        
        # 创建输出文件夹（如果不存在）
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建输出文件夹: {str(e)}")
                return
                
        # 创建进度对话框
        total_items = len(image_files) * len(self.process_queue)
        progress = QProgressDialog("正在处理图片...", "取消", 0, total_items, self)
        progress.setWindowTitle("处理中")
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)
        
        # 处理每张图片和每个预设配置
        success_count = 0
        error_files = []
        current_progress = 0
        
        for preset_idx, preset in enumerate(self.process_queue):
            target_width = preset['width']
            target_height = preset['height']
            quality = preset['quality']
            crop = preset['crop']
            
            # 为每个预设创建子文件夹
            preset_folder = os.path.join(output_folder, f"preset_{preset_idx + 1}_w{target_width}_h{target_height}")
            if not os.path.exists(preset_folder):
                os.makedirs(preset_folder)
                
            for file_path in image_files:
                if progress.wasCanceled():
                    break
                    
                progress.setLabelText(f"正在处理: {os.path.basename(file_path)} (预设 {preset_idx + 1}/{len(self.process_queue)})")
                
                try:
                    # 打开图片
                    with Image.open(file_path) as img:
                        # 计算调整后的尺寸
                        original_width, original_height = img.size
                        
                        # 计算缩放比例
                        width_ratio = target_width / original_width
                        height_ratio = target_height / original_height
                        ratio = min(width_ratio, height_ratio)
                        
                        # 缩放图片
                        new_width = int(original_width * ratio)
                        new_height = int(original_height * ratio)
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        
                        # 如果需要裁剪
                        if crop and (new_width != target_width or new_height != target_height):
                            left = (new_width - target_width) // 2
                            top = (new_height - target_height) // 2
                            right = left + target_width
                            bottom = top + target_height
                            resized_img = resized_img.crop((left, top, right, bottom))
                        
                        # 构建输出文件路径
                        file_name = os.path.basename(file_path)
                        output_file = os.path.join(preset_folder, file_name)
                        
                        # 保存图片
                        if file_name.lower().endswith(('.jpg', '.jpeg')):
                            resized_img.save(output_file, 'JPEG', quality=quality)
                        elif file_name.lower().endswith('.png'):
                            # PNG质量处理方式不同，使用优化参数
                            resized_img.save(output_file, 'PNG', optimize=True)
                        else:
                            # 其他格式使用默认参数
                            resized_img.save(output_file)
                            
                        success_count += 1
                        
                except Exception as e:
                    error_files.append(f"{os.path.basename(file_path)} (预设 {preset_idx + 1}): {str(e)}")
                    
                current_progress += 1
                progress.setValue(current_progress)
                QApplication.processEvents()  # 更新UI
                
            if progress.wasCanceled():
                break
        
        # 处理结果
        result_msg = f"处理完成！成功: {success_count} 个, 失败: {len(error_files)} 个"
        if error_files:
            result_msg += "\n失败文件:\n" + "\n".join(error_files)
            
        QMessageBox.information(self, "处理结果", result_msg)
        self.statusBar().showMessage(result_msg)

    def show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "设置", "程序设置功能即将推出")

    def show_about(self):
        """显示关于对话框"""
        about_msg = """图片批量压缩工具 v1.0
            用于批量处理图片尺寸和压缩质量

            功能特点:
            - 支持多种图片格式
            - 可保存尺寸和质量预设
            - 支持智能裁剪
            - 批量处理提高效率

            © 2023 图片处理工具团队"""
        QMessageBox.about(self, "关于", about_msg)

    def show_help(self):
        """显示帮助信息"""
        help_msg = """使用帮助:
            1. 选择包含图片的文件夹
            2. 设置输出尺寸、质量和裁剪选项
            3. 点击"添加到预设"可保存当前设置
            4. 点击"添加到队列"可将当前设置添加到处理队列
            5. 在"已保存的尺寸预设"区域可:
            - 选择并删除多个预设
            - 删除所有预设
            - 重命名或加载预设
            6. 在"处理队列"区域可管理处理配置
            7. 设置输出文件夹（可选）
            8. 点击"开始处理图片"按钮开始处理

            提示:
            - 双击预设可快速加载
            - 右键点击预设可进行更多操作
            - 处理过程中可随时取消"""
        QMessageBox.information(self, "使用帮助", help_msg)

    def update_animation(self):
        """更新背景动画"""
        self.animation_frame = (self.animation_frame + 1) % 100

    def resizeEvent(self, event):
        """窗口大小改变时调整背景"""
        if hasattr(self, 'decorative_bg'):
            self.decorative_bg.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 确保中文显示正常
    font = QFont("Microsoft YaHei UI")
    app.setFont(font)
    compressor = ImageCompressor()
    compressor.show()
    sys.exit(app.exec_())
    