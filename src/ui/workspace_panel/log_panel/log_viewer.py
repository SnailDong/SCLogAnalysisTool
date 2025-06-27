from PyQt6.QtWidgets import (QWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QMessageBox, QSplitter,
                           QListWidget, QListWidgetItem, QLabel, QTreeWidget,
                           QTreeWidgetItem, QInputDialog, QMenu, QDialog, QDialogButtonBox,
                           QPlainTextEdit)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPoint, QRect, QCoreApplication
from PyQt6.QtGui import (QFont, QTextCursor, QIcon, QColor, QPalette, 
                      QTextCharFormat, QCursor, QKeySequence, QAction,
                      QPainter, QFontMetrics)
from src.utils.highlighter import LogHighlighter
from src.ui.filter_panel.filter_engine import FilterEngine
from src.resources.theme import THEME
from typing import Dict, List, TYPE_CHECKING
import re
import json
import os
import traceback

class LineNumberArea(QWidget):
    def __init__(self, viewer):
        super().__init__(viewer)
        self.viewer = viewer

    def sizeHint(self):
        return QSize(self.viewer.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.viewer.line_number_area_paint_event(event)

class SCLogViewer(QPlainTextEdit):
    markRequested = pyqtSignal(int, str)  # 请求添加标记的信号
    filterRequested = pyqtSignal(str, int, int, int)  # 请求过滤的信号，包含选中文本、行号和位置
    textModified = pyqtSignal()  # 文本修改信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_highlighted_line = -1
        self._text_change_connected = False
        self.setReadOnly(True)  # 设置为只读状态
        
        # 添加行号区域
        self.line_number_area = LineNumberArea(self)
        
        # 连接信号
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        
        # 初始化行号区域宽度
        self.update_line_number_area_width(0)
        
        # 导入 traceback 模块
        self.traceback = traceback
        
        # 连接滚动条值变化信号
        self.verticalScrollBar().valueChanged.connect(self._on_vertical_scroll)
    def set_filter_type(self, filter_type: str):
        self.filter_type = filter_type
        
    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        digit_width = self.fontMetrics().horizontalAdvance('9')
        
        # 左边距 3像素
        left_padding = 3
        # 右边距 15像素
        right_padding = 15
        
        # 总宽度 = 左边距 + 数字宽度 * 位数 + 右边距
        space = left_padding + (digit_width * digits) + right_padding
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(THEME['background']))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # 设置行号字体与内容字体相同
        font = self.font()
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(THEME['text']))
                # 使用右对齐，但是不要完全贴右，留出右边距
                right_margin = 15  # 与line_number_area_width中的right_padding相同
                painter.drawText(0, int(top), 
                               self.line_number_area.width() - right_margin, 
                               self.fontMetrics().height(),
                               Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
            
    def setFont(self, font):
        """重写setFont方法以更新行号区域宽度"""
        super().setFont(font)
        self.update_line_number_area_width(0)
        
    def setReadOnly(self, read_only: bool):
        """重写setReadOnly方法以处理文本修改信号的连接"""
        super().setReadOnly(read_only)
        # 只在非只读状态下连接文本修改信号
        if not read_only and not self._text_change_connected:
            try:
                self.textChanged.connect(self.textModified.emit)
                self._text_change_connected = True
            except Exception:
                pass
        elif read_only and self._text_change_connected:
            try:
                self.textChanged.disconnect(self.textModified.emit)
                self._text_change_connected = False
            except Exception:
                pass
        
    def keyPressEvent(self, event):
        # 检查是否按下了Ctrl+F或Command+F
        if (event.key() == Qt.Key.Key_F and 
            (event.modifiers() & Qt.KeyboardModifier.ControlModifier or 
             event.modifiers() & Qt.KeyboardModifier.MetaModifier)):
            # 获取主窗口实例
            main_window = self.window()
            if main_window.__class__.__name__ == 'SCMainWindow':
                # 获取当前标签页
                current_widget = main_window.stack.currentWidget()
                if current_widget.__class__.__name__ == 'SCLogTab':
                    # 确保过滤面板可见
                    current_widget.workspace_panel.show_bottom_panel()
                    current_widget.workspace_panel.tab_list.setCurrentRow(0)  # 切换到过滤标签页
                    
                    # 获取过滤输入框
                    filter_input = current_widget.workspace_panel.get_filtered_view().filter_input
                    # 获取选中的文本和位置信息
                    cursor = self.textCursor()
                    selected_text = cursor.selectedText()
                    
                    if selected_text:
                        # 获取选中文本的行号和位置
                        line_number = cursor.blockNumber()
                        position = cursor.positionInBlock()
                        
                        # 重置过滤选项为默认值
                        filter_input.case_btn.setChecked(False)
                        filter_input.word_btn.setChecked(False)
                        filter_input.regex_btn.setChecked(False)
                        filter_input.case_sensitive = False
                        filter_input.whole_word = False
                        filter_input.use_regex = False
                        
                        # 发出过滤请求信号
                        self.filterRequested.emit(selected_text, line_number, position, position)
                        
                        # 让输入框获取焦点并全选内容
                        filter_input.input.setFocus()
                        # 设置新的过滤文本
                        filter_input.set_expression(selected_text)
                        filter_input.input.selectAll()
                    else:
                        # 如果没有选中文本，只让输入框获取焦点并全选当前内容
                        filter_input.input.setFocus()
                        filter_input.input.selectAll()
            event.accept()
        else:
            super().keyPressEvent(event)
            
    def setup_ui(self):
        # 设置等宽字体
        font = QFont("Courier New")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(14)  # 设置默认字体大小为14
        self.setFont(font)
        
        # 禁用自动换行
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # 设置字体大小范围
        self.default_font_size = 14
        self.min_font_size = int(self.default_font_size * 0.8)  # 最小为默认大小的0.8倍（11）
        self.max_font_size = int(self.default_font_size * 2)    # 最大为默认大小的2倍（28）
        
        # 设置滚动条样式
        self.setStyleSheet(f"""
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
        
        # 创建高亮器
        self.highlighter = LogHighlighter(self.document())
        
        # 设置选中文本的背景色
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Highlight, QColor(THEME['highlight_bg']))  # 蓝色背景
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(THEME['highlight_text']))  # 白色文字
        self.setPalette(palette)
        
        # 设置右键菜单策略
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 获取当前行
        cursor = self.cursorForPosition(pos)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        line_number = self.document().findBlock(cursor.position()).blockNumber()
        line_text = cursor.block().text()
        
        # 添加标记选项
        mark_action = QAction("添加标记", self)
        mark_action.triggered.connect(lambda: self.markRequested.emit(line_number, line_text))
        menu.addAction(mark_action)
        
        # 复制选项
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy)
        menu.addAction(copy_action)
        
        menu.exec(self.mapToGlobal(pos))
        
    def highlight_line(self, line_number: int, keyword_position: int = 0, keyword_length: int = 0, 
                      center_on_screen: bool = True, select_whole_line: bool = False):
        """高亮显示指定行
        
        Args:
            line_number: 要高亮的行号
            keyword_position: 关键字在行中的起始位置
            keyword_length: 关键字的长度
            center_on_screen: 是否将选中内容居中显示
            select_whole_line: 是否选中整行，True则选中整行，False则只选中关键字
        """
        # 清除之前的高亮
        if self.current_highlighted_line >= 0:
            self.clear_line_highlight(self.current_highlighted_line)
            
        # 获取目标行的块
        block = self.document().findBlockByLineNumber(line_number)
        if not block.isValid():
            return
            
        # 创建光标并移动到目标行
        cursor = QTextCursor(block)
        if not select_whole_line and keyword_length > 0:
            print(f"line_number: {line_number}, keyword_position: {keyword_position}, keyword_length: {keyword_length}")
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, keyword_position)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, keyword_length)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            
        # 设置选中区域的背景色
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(THEME['highlight_bg']))
        selection.cursor = cursor
        self.setExtraSelections([selection])
            
        # 设置光标位置
        old_value = self.verticalScrollBar().value()
        self.setTextCursor(cursor)
        
        if(center_on_screen):
            # 将光标居中显示
            self.centerCursor()
        
        self.current_highlighted_line = line_number

    def clear_line_highlight(self, line_number: int):
        if line_number >= 0:
            self.setExtraSelections([])
            self.current_highlighted_line = -1

    def get_current_line_number(self) -> int:
        """获取当前行号"""
        return self.textCursor().blockNumber()
        
    def mouseDoubleClickEvent(self, event):
        # 获取点击位置的光标
        cursor = self.cursorForPosition(event.pos())
        
        # 清除之前的行高亮
        if self.current_highlighted_line >= 0:
            self.clear_line_highlight(self.current_highlighted_line)
        
        # 获取当前行的文本
        block_text = cursor.block().text()
        pos = cursor.positionInBlock()
        
        # 向左扩展直到遇到空格或符号
        left = pos
        while left > 0 and not block_text[left-1].isspace() and not block_text[left-1] in ',.;:()[]{}=<>|"\'':
            left -= 1
            
        # 向右扩展直到遇到空格或符号
        right = pos
        while right < len(block_text) and not block_text[right].isspace() and not block_text[right] in ',.;:()[]{}=<>|"\'':
            right += 1
            
        # 设置新的选择范围
        cursor.setPosition(cursor.block().position() + left)
        cursor.setPosition(cursor.block().position() + right, QTextCursor.MoveMode.KeepAnchor)
        
        # 应用选择
        self.setTextCursor(cursor)
        
        # 不调用父类的双击事件，以防止默认的选择行为
        event.accept()

    def _handle_find_shortcut(self):
        """处理查找快捷键"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            block_number = cursor.blockNumber()
            block = cursor.block()
            # 获取选中文本在当前行的起始和结束位置
            start_pos = cursor.selectionStart() - block.position()
            end_pos = cursor.selectionEnd() - block.position()
            # 发送包含完整位置信息的信号
            self.filterRequested.emit(selected_text, block_number, start_pos, end_pos)
        else:
            self.filterRequested.emit("", -1, -1, -1)

    def increase_font_size(self):
        """增加字体大小"""
        current_size = self.font().pointSize()
        max_size = int(self.default_font_size * 2)
        if current_size >= max_size:
            return
        font = self.font()
        font.setPointSize(min(current_size + 1, max_size))
        self.setFont(font)
        self.update_line_number_area_width()
        self.line_number_area.update()

    def decrease_font_size(self):
        """减小字体大小"""
        current_size = self.font().pointSize()
        min_size = int(self.default_font_size * 0.8)
        if current_size <= min_size:
            return
        font = self.font()
        font.setPointSize(max(current_size - 1, min_size))
        self.setFont(font)
        self.update_line_number_area_width()
        self.line_number_area.update()

    def reset_font_size(self):
        """重置字体大小为默认值"""
        font = self.font()
        font.setPointSize(self.default_font_size)
        self.setFont(font)
        self.update_line_number_area_width()
        self.line_number_area.update()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # 获取当前字体大小
            current_size = self.font().pointSize()
            
            # 计算最大和最小字体大小
            max_size = int(self.default_font_size * 2)    # 最大为默认大小的2倍
            min_size = int(self.default_font_size * 0.8)  # 最小为默认大小的0.8倍
            
            # 根据滚轮方向调整字体大小
            delta = event.angleDelta().y()
            if delta > 0:  # 向上滚动，放大
                if current_size >= max_size:
                    return
                new_size = min(current_size + 1, max_size)
            else:  # 向下滚动，缩小
                if current_size <= min_size:
                    return
                new_size = max(current_size - 1, min_size)
            
            # 应用新的字体大小
            font = self.font()
            font.setPointSize(new_size)
            self.setFont(font)
            
            # 更新行号区域
            self.update_line_number_area_width(0)
            self.line_number_area.update()
            
            event.accept()
            return
        
        super().wheelEvent(event)

    def _on_vertical_scroll(self, value):
        """处理垂直滚动条值变化"""
        print(f"\n滚动条值变化: {value}, 最大值: {self.verticalScrollBar().maximum()}")
        print("调用栈:")
        for line in self.traceback.format_stack()[:-1]:  # 排除当前函数的调用
            print(line.strip())
