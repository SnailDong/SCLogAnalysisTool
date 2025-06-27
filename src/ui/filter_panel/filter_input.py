from PyQt6.QtWidgets import (QWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QMessageBox, QSplitter,
                           QListWidget, QListWidgetItem, QLabel, QTreeWidget,
                           QTreeWidgetItem, QInputDialog, QMenu, QDialog, QDialogButtonBox,
                           QCheckBox)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPoint
from PyQt6.QtGui import (QFont, QTextCursor, QIcon, QColor, QPalette, 
                      QTextCharFormat, QCursor, QKeySequence, QAction)
from src.utils.highlighter import LogHighlighter
from src.ui.filter_panel.filter_engine import FilterEngine
from src.resources.theme import THEME
from src.utils.logger import log_ui_event
from typing import Dict, List, TYPE_CHECKING
import re
import json
import os
from src.utils.expression_parser import FilterOptions
from src.ui.keyword_panel.keyword_dialog import SCKeywordDialog

class SCFilterInput(QWidget):
    filterChanged = pyqtSignal(str)
    navigateToMatch = pyqtSignal(int)  # 新增信号，用于导航到指定匹配项
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_match = 0
        self.total_matches = 0
        # 初始化匹配选项
        self.case_sensitive = False  # 默认不区分大小写
        self.whole_word = False      # 默认不严格匹配单词
        self.use_regex = False       # 默认不使用正则表达式
        self.setup_shortcuts()  # 添加快捷键设置
        
    def setup_shortcuts(self):
        """设置快捷键"""
        # 保存关键字快捷键 (Command+T)
        save_shortcut = QAction(self)
        save_shortcut.setShortcut(QKeySequence("Ctrl+T"))  # 使用自定义快捷键
        save_shortcut.triggered.connect(self._save_current_keyword)
        self.addAction(save_shortcut)
        
    def keyPressEvent(self, event):
        """处理按键事件"""
        # 处理 Command+T 保存关键字
        if event.key() == Qt.Key.Key_T and event.modifiers() == Qt.KeyboardModifier.MetaModifier:
            self._save_current_keyword()
            event.accept()
            return
            
        # 处理 Enter 键应用过滤
        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self._on_apply()
            event.accept()
            return
            
        super().keyPressEvent(event)
        
    def _save_current_keyword(self):
        """保存当前过滤输入框中的关键字"""
        # 获取当前关键字
        keyword = self.input.text().strip()
        if not keyword:
            return
            
        # 获取主窗口实例
        main_window = self.window()
        if main_window.__class__.__name__ == 'SCMainWindow':
            # 获取关键字列表
            keyword_list = main_window.keyword_list
            if not keyword_list:
                return
                
            # 创建添加关键字对话框
            dialog = SCKeywordDialog(self, keyword, self.get_filter_options(), keyword_list=keyword_list)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                keyword = dialog.get_keyword()
                alias = dialog.get_alias()
                options = dialog.get_options()
                target_group = dialog.get_selected_group()
                
                if keyword:
                    # 创建关键字项
                    keyword_item = QTreeWidgetItem([alias if alias else keyword])  # 显示文本
                    keyword_item.setData(0, Qt.ItemDataRole.UserRole, "keyword")
                    keyword_item.setData(0, Qt.ItemDataRole.UserRole + 1, options)  # 选项
                    keyword_item.setData(0, Qt.ItemDataRole.UserRole + 2, keyword)  # 实际关键字
                    keyword_item.setData(0, Qt.ItemDataRole.UserRole + 3, alias)  # 别名
                    
                    # 添加到指定分组
                    keyword_list.add_keyword(keyword, target_group, options, alias)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(4)
        
        # 创建输入框
        self.input = QLineEdit()
        self.input.setPlaceholderText('输入过滤表达式')
        
        # 连接回车键信号
        self.input.returnPressed.connect(self._on_apply)
        self.input.textChanged.connect(self._on_text_changed)
        
        # 创建匹配选项按钮
        options_layout = QHBoxLayout()
        options_layout.setSpacing(2)
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        # 区分大小写按钮
        self.case_btn = QPushButton("Cc")
        self.case_btn.setCheckable(True)
        self.case_btn.setFixedSize(24, 24)
        self.case_btn.setToolTip("区分大小写")
        
        # 全词匹配按钮
        self.word_btn = QPushButton("W")
        self.word_btn.setCheckable(True)
        self.word_btn.setFixedSize(24, 24)
        self.word_btn.setToolTip("全词匹配")
        
        # 正则表达式按钮
        self.regex_btn = QPushButton(".*")
        self.regex_btn.setCheckable(True)
        self.regex_btn.setFixedSize(24, 24)
        self.regex_btn.setToolTip("使用正则表达式")
        
        # 设置按钮样式
        option_button_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['text']};
                font-size: 12px;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: {THEME['hover_bg']};
                border-radius: 3px;
            }}
            QPushButton:checked {{
                background-color: {THEME['highlight_bg']};
                color: {THEME['highlight_text']};
                border-radius: 3px;
            }}
        """
        self.case_btn.setStyleSheet(option_button_style)
        self.word_btn.setStyleSheet(option_button_style)
        self.regex_btn.setStyleSheet(option_button_style)
        
        # 添加按钮到选项布局
        options_layout.addWidget(self.case_btn)
        options_layout.addWidget(self.word_btn)
        options_layout.addWidget(self.regex_btn)
        
        # 匹配计数标签
        self.match_count = QLabel("0/0")
        self.match_count.setStyleSheet(f"""
            QLabel {{
                color: {THEME['text']};
                padding: 0 5px;
                min-width: 40px;
            }}
        """)
        
        # 上一个匹配按钮
        self.prev_btn = QPushButton("▲")
        self.prev_btn.setFixedSize(24, 24)
        self.prev_btn.setEnabled(False)
        
        # 下一个匹配按钮
        self.next_btn = QPushButton("▼")
        self.next_btn.setFixedSize(24, 24)
        self.next_btn.setEnabled(False)
        
        # 设置导航按钮样式
        nav_button_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {THEME['tab_text']};
                font-size: 12px;
                padding: 3px;
                font-weight: bold;
            }}
            QPushButton:enabled {{
                color: {THEME['highlight_text']};
            }}
            QPushButton:hover {{
                background-color: {THEME['hover_bg']};
                border-radius: 3px;
            }}
            QPushButton:disabled {{
                color: {THEME['tab_text']};
                opacity: 0.5;
            }}
        """
        self.prev_btn.setStyleSheet(nav_button_style)
        self.next_btn.setStyleSheet(nav_button_style)
        
        # 创建按钮
        self.apply_button = QPushButton("检索关键字")
        self.clear_button = QPushButton("清除")
        
        # 添加到主布局
        layout.addWidget(self.input)
        layout.addLayout(options_layout)
        layout.addWidget(self.match_count)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.clear_button)
        
        # 连接信号
        self.apply_button.clicked.connect(self._on_apply)
        self.clear_button.clicked.connect(self._on_clear)
        self.prev_btn.clicked.connect(self._on_prev_match)
        self.next_btn.clicked.connect(self._on_next_match)
        self.case_btn.clicked.connect(self._on_case_option_changed)
        self.word_btn.clicked.connect(self._on_word_option_changed)
        self.regex_btn.clicked.connect(self._on_regex_option_changed)
        
    def _on_text_changed(self, text: str):
        """处理输入框文本变化"""
        log_ui_event("text_change", "FilterInput", f"Text: {text}")
        
    def _on_case_option_changed(self, checked: bool):
        """处理区分大小写选项变化"""
        log_ui_event("option_change", "CaseSensitiveButton", f"Checked: {checked}")
        self.case_sensitive = checked
        self._on_option_changed()
        
    def _on_word_option_changed(self, checked: bool):
        """处理全词匹配选项变化"""
        log_ui_event("option_change", "WholeWordButton", f"Checked: {checked}")
        self.whole_word = checked
        self._on_option_changed()
        
    def _on_regex_option_changed(self, checked: bool):
        """处理正则表达式选项变化"""
        log_ui_event("option_change", "RegexButton", f"Checked: {checked}")
        self.use_regex = checked
        self._on_option_changed()
        
    def _on_option_changed(self):
        """处理任何选项变化"""
        # 如果输入框有内容，立即应用新的过滤选项
        if self.input.text().strip():
            print(f"on_option_changed: {self.input.text().strip()}")
            self._on_apply()
            
    def _on_apply(self):
        """处理应用过滤"""
        text = self.input.text()
        log_ui_event("apply_filter", "FilterInput", f"Text: {text}, Options: case={self.case_sensitive}, word={self.whole_word}, regex={self.use_regex}")
        self.filterChanged.emit(text)
        # 让输入框失去焦点
        self.input.clearFocus()
        
    def _on_clear(self):
        """处理清除过滤"""
        log_ui_event("clear_filter", "FilterInput")
        self.input.clear()
        # 清除所有配置选项
        self.case_btn.setChecked(False)
        self.word_btn.setChecked(False)
        self.regex_btn.setChecked(False)
        # 更新内部状态
        self.case_sensitive = False
        self.whole_word = False
        self.use_regex = False
        # 发送过滤器变化信号
        self.filterChanged.emit("")
        self.update_match_count(0, 0)
        
    def _on_prev_match(self):
        """处理前一个匹配"""
        if self.total_matches > 0:
            if self.current_match <= 1:
                # 如果当前是第一个，则跳转到最后一个
                self.current_match = self.total_matches
            else:
                self.current_match -= 1
            log_ui_event("navigate", "PrevMatchButton", f"Current: {self.current_match}/{self.total_matches}")
            self.navigateToMatch.emit(self.current_match - 1)  # 发送0-based索引
            self.update_match_count(self.current_match, self.total_matches)
            
    def _on_next_match(self):
        """处理下一个匹配"""
        if self.total_matches > 0:
            if self.current_match >= self.total_matches:
                # 如果当前是最后一个，则跳转到第一个
                self.current_match = 1
            else:
                self.current_match += 1
            log_ui_event("navigate", "NextMatchButton", f"Current: {self.current_match}/{self.total_matches}")
            self.navigateToMatch.emit(self.current_match - 1)  # 发送0-based索引
            self.update_match_count(self.current_match, self.total_matches)
            
    def update_match_count(self, current: int, total: int):
        """更新匹配计数和导航按钮状态"""
        old_total = self.total_matches
        self.current_match = current
        self.total_matches = total
        if old_total != total:
            log_ui_event("match_count_change", "FilterInput", f"Total matches: {total}")
        self.match_count.setText(f"{current}/{total}")
        
        # 只要有匹配项，就启用导航按钮
        self.prev_btn.setEnabled(total > 0)
        self.next_btn.setEnabled(total > 0)
        
    def set_expression(self, expression: str):
        """设置过滤表达式"""
        log_ui_event("set_expression", "FilterInput", f"Expression: {expression}")
        self.input.setText(expression)
        # 立即应用过滤
        self._on_apply()
        
    def set_filter_options(self, options: dict):
        """设置过滤选项"""
        if not options:
            return
            
        log_ui_event("set_options", "FilterInput", f"Options: {options}")
        # 设置按钮状态
        self.case_btn.setChecked(options.get('case_sensitive', False))
        self.word_btn.setChecked(options.get('whole_word', False))
        self.regex_btn.setChecked(options.get('use_regex', False))
        
        # 更新内部状态
        self.case_sensitive = options.get('case_sensitive', False)
        self.whole_word = options.get('whole_word', False)
        self.use_regex = options.get('use_regex', False)
        
        # 如果输入框有内容，重新应用过滤器
        if self.input.text().strip():
            print(f"set_filter_options: {self.input.text().strip()}")
            self._on_apply()
            
    def get_filter_options(self) -> dict:
        """获取当前过滤选项"""
        return {
            'case_sensitive': self.case_sensitive,
            'whole_word': self.whole_word,
            'use_regex': self.use_regex
        }
