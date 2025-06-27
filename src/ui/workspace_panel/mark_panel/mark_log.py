from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox, QHeaderView)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction
from src.utils.mark_manager import MarkManager
from src.resources.theme import THEME

class SCMarkLogViewer(QWidget):
    markClicked = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mark_manager = MarkManager()
        self.current_filepath = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建树形视图
        self.mark_tree = QTreeWidget()
        self.mark_tree.setColumnCount(2)  # 设置2列：行号、内容
        self.mark_tree.setHeaderLabels(["行号", "内容"])
        
        # 设置列宽和调整模式
        header = self.mark_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # 行号列可以手动调整宽度
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # 内容列固定宽度，不自动扩展
        
        # 设置行号列的最小和默认宽度
        self.mark_tree.setColumnWidth(0, 100)  # 设置行号列默认宽度为100像素
        header.setMinimumSectionSize(60)  # 设置行号列最小宽度
        
        # 设置内容列宽度
        self.mark_tree.setColumnWidth(1, 1000)  # 设置内容列宽度为1000像素
        
        # 启用水平滚动条
        self.mark_tree.setHorizontalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        self.mark_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # 启用垂直滚动条
        self.mark_tree.setVerticalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        self.mark_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # 设置文本不换行，允许水平滚动
        self.mark_tree.setWordWrap(False)
        self.mark_tree.setUniformRowHeights(True)  # 统一行高
        self.mark_tree.setTextElideMode(Qt.TextElideMode.ElideNone)  # 不省略文本
        
        # 设置样式
        self.mark_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {THEME['background']};
                color: {THEME['text']};
                border: none;
                padding: 0px;
                margin: 0px;
            }}
            QTreeWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {THEME['border']};
                margin: 0px;
            }}
            QTreeWidget::item:hover {{
                background-color: {THEME['hover_bg']};
            }}
            QHeaderView::section {{
                background-color: {THEME['background']};
                color: {THEME['text']};
                padding: 5px;
                border: none;
                border-bottom: 1px solid {THEME['border']};
            }}
            QScrollBar:vertical {{
                background: {THEME['scrollbar_bg']};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME['scrollbar_thumb']};
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
                width: 8px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {THEME['scrollbar_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            
            QScrollBar:horizontal {{
                background: {THEME['scrollbar_bg']};
                height: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {THEME['scrollbar_thumb']};
                min-width: 20px;
                border-radius: 6px;
                margin: 2px;
                height: 8px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {THEME['scrollbar_hover']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        
        self.mark_tree.itemDoubleClicked.connect(self._on_mark_double_clicked)
        self.mark_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.mark_tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.mark_tree)

    def refresh_marks(self):
        self.mark_tree.clear()
        if not self.current_filepath:
            return
        marks = self.mark_manager.get_marks(self.current_filepath)
        marks.sort(key=lambda x: x["line_number"])
        
        # 计算最长内容的宽度
        font_metrics = self.mark_tree.fontMetrics()
        max_content_width = 0
        
        for mark in marks:
            item = QTreeWidgetItem()
            item.setText(0, str(mark["line_number"]))  # 行号
            content = mark["content"].strip()
            item.setText(1, content)  # 内容，去除首尾空白
            item.setData(0, Qt.ItemDataRole.UserRole, mark["line_number"])
            # 设置文本对齐方式
            item.setTextAlignment(0, Qt.AlignmentFlag.AlignRight)  # 行号右对齐
            item.setTextAlignment(1, Qt.AlignmentFlag.AlignLeft)  # 内容左对齐
            self.mark_tree.addTopLevelItem(item)
            
            # 计算当前内容的宽度
            content_width = font_metrics.horizontalAdvance(content)
            max_content_width = max(max_content_width, content_width)
        
        # 设置内容列的宽度为最长内容的宽度加上一些padding
        padding = 20  # 添加一些padding，避免文字紧贴边缘
        self.mark_tree.setColumnWidth(1, max_content_width + padding)

    def _on_mark_double_clicked(self, item: QTreeWidgetItem, column: int):
        line_number = item.data(0, Qt.ItemDataRole.UserRole)
        self.markClicked.emit(line_number)

    def _show_context_menu(self, pos):
        item = self.mark_tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        remove_action = QAction("删除标记", self)
        remove_action.triggered.connect(lambda: self._remove_mark(item))
        menu.addAction(remove_action)
        menu.exec(self.mark_tree.mapToGlobal(pos))

    def _remove_mark(self, item: QTreeWidgetItem):
        line_number = item.data(0, Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "确认删除", "确定要删除这个标记吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.remove_mark(line_number)

    def set_filepath(self, filepath: str):
        self.current_filepath = filepath
        self.mark_manager.load_marks(filepath)
        self.refresh_marks()

    def add_mark(self, line_number: int, content: str):
        if not self.current_filepath:
            return
        if self.mark_manager.is_marked(self.current_filepath, line_number):
            return
        if self.mark_manager.add_mark(self.current_filepath, line_number, content):
            self.refresh_marks()
            self.mark_manager.save_marks(self.current_filepath)

    def remove_mark(self, line_number: int):
        if not self.current_filepath:
            return
        if self.mark_manager.remove_mark(self.current_filepath, line_number):
            self.refresh_marks()
            self.mark_manager.save_marks(self.current_filepath) 