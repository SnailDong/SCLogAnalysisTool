from PyQt6.QtWidgets import (QWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QMessageBox, QSplitter,
                           QListWidget, QListWidgetItem, QLabel, QTreeWidget,
                           QTreeWidgetItem, QInputDialog, QMenu, QDialog, QDialogButtonBox)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPoint
from PyQt6.QtGui import (QFont, QTextCursor, QIcon, QColor, QPalette, 
                      QTextCharFormat, QCursor, QKeySequence, QAction)
from src.utils.highlighter import LogHighlighter
from src.ui.filter_panel.filter_engine import FilterEngine
from src.resources.theme import THEME
from typing import Dict, List, TYPE_CHECKING
import re
import json
import os
class SCKeywordItem(QListWidgetItem):
    def __init__(self, expression: str, alias: str = ""):
        super().__init__()
        self.expression = expression
        self.alias = alias
        self.display_text = alias if alias else expression  # 如果有别名就显示别名，否则显示表达式
        self.setSizeHint(QSize(0, 30))
class SCKeywordItemWidget(QWidget):
    deleteClicked = pyqtSignal(QListWidgetItem)
    clicked = pyqtSignal(str)
    
    def __init__(self, item: QListWidgetItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)  # 设置间距
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # 垂直居中对齐
        
        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(16, 16)  # 减小按钮尺寸
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['tab_text']};
                border: none;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                color: {THEME['highlight_text']};
            }}
        """)
        delete_btn.clicked.connect(lambda: self.deleteClicked.emit(self.item))
        
        # 关键字文本
        text_label = QLabel(self.item.display_text)  # 使用display_text显示
        text_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME['text']};
                padding: 0px;
                margin: 0px;
                background: transparent;
            }}
        """)
        
        layout.addWidget(delete_btn)
        layout.addWidget(text_label, 1)
