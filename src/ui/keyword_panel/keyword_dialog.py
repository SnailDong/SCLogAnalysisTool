from PyQt6.QtWidgets import (QWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QMessageBox, QSplitter,
                           QListWidget, QListWidgetItem, QLabel, QTreeWidget,
                           QTreeWidgetItem, QInputDialog, QMenu, QDialog, QDialogButtonBox,
                           QCheckBox)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPoint, QEvent
from PyQt6.QtGui import (QFont, QTextCursor, QIcon, QColor, QPalette, 
                      QTextCharFormat, QCursor, QKeySequence, QAction)
from src.utils.highlighter import LogHighlighter
from src.ui.filter_panel.filter_engine import FilterEngine
from src.resources.theme import THEME
from typing import Dict, List, TYPE_CHECKING
import re
import json
import os
from src.ui.keyword_panel.group_selector_dialog import SCGroupSelectorDialog

class SCKeywordDialog(QDialog):
    def __init__(self, parent=None, initial_text="", initial_options=None, initial_alias="", keyword_list=None):
        super().__init__(parent)
        print("[DEBUG] Initializing keyword dialog")  # 添加初始化调试打印
        self.initial_text = initial_text
        self.initial_options = initial_options or {}
        self.initial_alias = initial_alias
        self.keyword_list = keyword_list
        self.selected_group = None
        self.setup_ui()
        print("[DEBUG] Keyword dialog initialized")  # 打印初始化完成状态
        # 设置对话框宽度为屏幕的1/3，高度自适应
        screen = self.screen()
        screen_size = screen.size()
        dialog_width = screen_size.width() // 3
        self.setFixedWidth(dialog_width)
        # 将对话框移动到屏幕中心
        self.move(screen.geometry().center() - self.frameGeometry().center())
        
    def setup_ui(self):
        self.setWindowTitle("添加关键字")
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # 设置垂直间距
        
        # 创建表单布局
        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)  # 设置表单项之间的垂直间距
        
        # 设置统一的标签宽度
        label_width = 50  # 减小标签宽度
        
        # 关键字描述输入
        alias_layout = QHBoxLayout()
        alias_layout.setSpacing(4)  # 设置标签和输入框之间的水平间距
        alias_label = QLabel("标签描述：")
        alias_label.setFixedWidth(label_width)
        alias_label.setStyleSheet(f"color: {THEME['text']}")
        self.alias_input = QLineEdit()
        self.alias_input.setText(self.initial_alias)
        self.alias_input.setStyleSheet(f"color: {THEME['text']}; background: {THEME['background']}")
        alias_layout.addWidget(alias_label)
        alias_layout.addWidget(self.alias_input)
        form_layout.addLayout(alias_layout)
        
        # 关键字输入
        keyword_layout = QHBoxLayout()
        keyword_layout.setSpacing(4)  # 设置标签和输入框之间的水平间距
        keyword_label = QLabel("关键字值：")
        keyword_label.setFixedWidth(label_width)
        keyword_label.setStyleSheet(f"color: {THEME['text']}")
        self.keyword_input = QLineEdit()
        self.keyword_input.setText(self.initial_text)
        self.keyword_input.setStyleSheet(f"color: {THEME['text']}; background: {THEME['background']}")
        keyword_layout.addWidget(keyword_label)
        keyword_layout.addWidget(self.keyword_input)
        form_layout.addLayout(keyword_layout)

        # 分组选择
        group_layout = QHBoxLayout()
        group_layout.setSpacing(4)  # 设置标签和输入框之间的水平间距
        group_label = QLabel("分组名称：")
        group_label.setFixedWidth(label_width)
        group_label.setStyleSheet(f"color: {THEME['text']}")
        self.group_input = QLineEdit()
        self.group_input.setReadOnly(True)
        self.group_input.setPlaceholderText("点击选择分组...")
        self.group_input.setStyleSheet(f"color: {THEME['text']}; background: {THEME['background']}")
        self.group_input.installEventFilter(self)  # 安装事件过滤器
        group_layout.addWidget(group_label)
        group_layout.addWidget(self.group_input)
        form_layout.addLayout(group_layout)
        
        # 添加表单布局到主布局
        layout.addLayout(form_layout)
        
        # 匹配选项
        checkboxes_layout = QHBoxLayout()  # 直接使用水平布局
        checkboxes_layout.setSpacing(15)  # 设置选项之间的间距
        
        self.case_sensitive = QCheckBox("区分大小写")
        self.case_sensitive.setChecked(self.initial_options.get("case_sensitive", False))
        self.case_sensitive.setStyleSheet(f"color: {THEME['text']}")
        checkboxes_layout.addWidget(self.case_sensitive)
        
        self.word_only = QCheckBox("全词匹配")
        self.word_only.setChecked(self.initial_options.get("word_only", False))
        self.word_only.setStyleSheet(f"color: {THEME['text']}")
        checkboxes_layout.addWidget(self.word_only)
        
        self.use_regex = QCheckBox("使用正则表达式")
        self.use_regex.setChecked(self.initial_options.get("use_regex", False))
        self.use_regex.setStyleSheet(f"color: {THEME['text']}")
        checkboxes_layout.addWidget(self.use_regex)
        
        # 直接添加水平布局到主布局
        layout.addLayout(checkboxes_layout)
        
        # 创建保存和取消按钮
        save_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        # 设置按钮样式
        save_button.setStyleSheet(f"color: {THEME['text']}")
        cancel_button.setStyleSheet(f"color: {THEME['text']}")
        
        # 创建水平布局并使用比例布局
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)  # 1/6
        button_layout.addWidget(cancel_button)
        button_layout.addStretch(1)  # 1/6
        button_layout.addWidget(save_button)
        button_layout.addStretch(1)  # 1/6
        
        # 添加按钮布局到主布局
        layout.addSpacing(10)  # 添加一些垂直间距
        layout.addLayout(button_layout)
        
    def eventFilter(self, obj, event):
        """事件过滤器"""
        if obj == self.group_input and event.type() == QEvent.Type.MouseButtonPress:
            print("[DEBUG] Group input clicked through event filter")
            self.show_group_selector(event)
            return True
        return super().eventFilter(obj, event)

    def show_group_selector(self, event=None):
        """显示分组选择器"""
        print("[DEBUG] Show group selector called")
        
        # 获取关键字列表
        keyword_list = self.keyword_list
        print(f"[DEBUG] Using keyword_list: {keyword_list}")
        
        if keyword_list:
            dialog = SCGroupSelectorDialog(keyword_list, self)
            print("[DEBUG] Group selector dialog created")
            print("[DEBUG] About to show dialog")
            result = dialog.exec()
            print(f"[DEBUG] Dialog exec result: {result}")
            
            if result == QDialog.DialogCode.Accepted:
                self.selected_group = dialog.get_selected_group()
                self.group_input.setText(self.selected_group)
                print(f"[DEBUG] Selected group: {self.selected_group}")
        else:
            print("[DEBUG] No keyword_list available")
        
    def get_keyword(self):
        """获取关键字"""
        return self.keyword_input.text().strip()
        
    def get_alias(self):
        """获取别名"""
        return self.alias_input.text().strip()
        
    def get_options(self):
        """获取匹配选项"""
        return {
            "case_sensitive": self.case_sensitive.isChecked(),
            "word_only": self.word_only.isChecked(),
            "use_regex": self.use_regex.isChecked()
        }
        
    def get_selected_group(self):
        """获取选中的分组"""
        return self.selected_group
