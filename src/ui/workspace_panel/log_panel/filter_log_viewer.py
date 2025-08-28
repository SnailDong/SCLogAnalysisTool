from PyQt6.QtWidgets import (QWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QMessageBox, QSplitter,
                           QListWidget, QListWidgetItem, QLabel, QTreeWidget,
                           QTreeWidgetItem, QInputDialog, QMenu, QDialog, QDialogButtonBox)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPoint, QThread, QObject
from PyQt6.QtGui import (QFont, QTextCursor, QIcon, QColor, QPalette, 
                      QTextCharFormat, QCursor, QKeySequence, QAction)
from src.utils.highlighter import LogHighlighter
from src.ui.filter_panel.filter_engine import FilterEngine
from src.ui.filter_panel.filter_input import SCFilterInput
from src.ui.workspace_panel.log_panel.log_viewer import SCLogViewer
from src.resources.theme import THEME
from typing import Dict, List, TYPE_CHECKING, Tuple
import re
import json
import os
import traceback

class TextWorker(QObject):
    finished = pyqtSignal(str, list, list)  # 发送处理完成的信号
    error = pyqtSignal(str)  # 错误信号
    progress = pyqtSignal(int)  # 进度信号
    
    def __init__(self, text: str, filter_engine: FilterEngine, filter_expression: str = None, filter_options: dict = None):
        super().__init__()
        self.text = text
        self.filter_engine = filter_engine
        self.filter_expression = filter_expression
        self.filter_options = filter_options
        self.is_cancelled = False
        
    def cancel(self):
        """取消处理"""
        print("正在取消文本处理...")
        self.is_cancelled = True
        
    def process(self):
        """处理文本"""
        try:
            if self.is_cancelled:
                print("处理已被取消")
                return
                
            filtered_lines = []
            line_mapping = []
            
            # 如果有过滤表达式，执行过滤
            if self.filter_expression:
                # 设置过滤表达式
                result = self.filter_engine.set_filter_expression(self.filter_expression, self.filter_options)
                if not result["valid"]:
                    raise ValueError(result["message"])
                
                if self.is_cancelled:
                    print("过滤表达式设置后被取消")
                    return
                
                # 执行过滤
                filtered_lines, line_mapping = self.filter_engine.filter_text(self.text)
                
                if self.is_cancelled:
                    print("过滤执行后被取消")
                    return
            
            # 发送处理完成的信号
            if not self.is_cancelled:
                self.finished.emit(self.text, filtered_lines, line_mapping)
            else:
                print("发送结果前被取消")
            
        except Exception as e:
            if not self.is_cancelled:
                print(f"处理文本时出错: {str(e)}")
                self.error.emit(str(e))
            else:
                print("发生错误时已被取消")

class SCFilteredLogViewer(QWidget):
    filterChanged = pyqtSignal(str)  # 添加过滤器变化信号
    
    def __init__(self, filter_input: SCFilterInput = None, parent=None):
        super().__init__(parent)
        self.filter_engine = FilterEngine()
        self.line_mapping = []  # 初始化行号映射
        self.current_line_matches = []  # 当前行的所有匹配位置
        self.current_match_index = -1  # 当前匹配项在当前行中的索引
        self.current_line = -1  # 当前行号
        self.total_matches = 0  # 所有匹配项的总数
        self.current_global_match = 0  # 当前全局匹配项索引
        self.initial_filter_position = None  # 初始过滤位置（行号，位置）
        self.filter_input = filter_input
        self.thread = None
        self.worker = None
        self.setup_ui()
        
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        self._cleanup_thread()
        super().closeEvent(event)
        
    def hideEvent(self, event):
        """处理窗口隐藏事件"""
        self._cleanup_thread()
        super().hideEvent(event)
        
    def __del__(self):
        """析构函数"""
        try:
            self._cleanup_thread()
        except:
            pass

    def set_filter_input(self, filter_input: SCFilterInput):
        self.filter_input = filter_input
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 创建原始日志查看器
        self.original_viewer = SCLogViewer()
        self.original_viewer.set_filter_type("original")
        self.splitter.addWidget(self.original_viewer)
        
        # 创建过滤后的日志查看器，完全禁用点击响应
        self.filtered_viewer = SCLogViewer()
        self.filtered_viewer.set_filter_type("filtered")
        self.filtered_viewer.setReadOnly(True)  # 设置为只读
        self.filtered_viewer.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)  # 允许鼠标和键盘选择文本
        self.filtered_viewer.viewport().setCursor(Qt.CursorShape.ArrowCursor)  # 设置鼠标指针为箭头
        # 覆盖鼠标事件处理
        # self.filtered_viewer.mousePressEvent = self._on_filtered_viewer_mouse_press
        self.filtered_viewer.mouseDoubleClickEvent = self._on_filtered_viewer_double_click
        self.splitter.addWidget(self.filtered_viewer)
        
        # 设置分割器比例
        self.splitter.setSizes([int(self.splitter.size().height() * 0.6),
                              int(self.splitter.size().height() * 0.4)])
        
        layout.addWidget(self.splitter)
        
        # 初始时隐藏过滤视图
        self.filtered_viewer.hide()
        
        # 连接信号
        self.filtered_viewer.cursorPositionChanged.connect(self._on_filtered_cursor_changed)
        self.filter_input.filterChanged.connect(self.apply_filter)
        self.filter_input.navigateToMatch.connect(self._on_navigate_to_match)
        self.original_viewer.filterRequested.connect(self._on_filter_requested)
        
        # 连接过滤器变化信号
        self.filter_input.filterChanged.connect(self.filterChanged.emit)
            
    def _find_keyword_positions(self, text: str, keywords: set) -> list:
        """在文本中查找所有关键字的位置，返回按位置排序的列表"""
        positions = []  # [(position, keyword_length), ...]
        
        # 遍历所有关键字，找到所有出现的位置
        for keyword in keywords:
            if not keyword:
                continue
                
            # 根据过滤选项进行匹配
            if self.filter_engine.use_regex:
                try:
                    pattern = re.compile(keyword, flags=0 if self.filter_engine.case_sensitive else re.IGNORECASE)
                    for match in pattern.finditer(text):
                        positions.append((match.start(), len(match.group())))
                except re.error:
                    continue
            else:
                search_text = text if self.filter_engine.case_sensitive else text.lower()
                search_keyword = keyword if self.filter_engine.case_sensitive else keyword.lower()
                
                if self.filter_engine.whole_word:
                    pattern = r'\b' + re.escape(search_keyword) + r'\b'
                    for match in re.finditer(pattern, search_text):
                        positions.append((match.start(), len(keyword)))
                else:
                    pos = 0
                    while True:
                        pos = search_text.find(search_keyword, pos)
                        if pos == -1:
                            break
                        positions.append((pos, len(keyword)))
                        pos += 1
                        
        # 按位置排序
        positions.sort(key=lambda x: x[0])
        return positions

    def _find_next_keyword_position(self, text: str, current_pos: int, keywords: set) -> tuple:
        """在文本中查找当前位置之后的下一个关键字位置"""
        positions = self._find_keyword_positions(text, keywords)
        
        # 找到第一个位置大于当前位置的关键字
        for pos, length in positions:
            if pos > current_pos:
                return pos, length
                
        # 如果没有找到，返回None表示需要跳转到下一行
        return None

    def _find_first_keyword_position(self, text: str, keywords: set) -> tuple:
        """在文本中查找第一个关键字的位置"""
        positions = self._find_keyword_positions(text, keywords)
        return positions[0] if positions else (0, 0)

    def _on_filtered_cursor_changed(self):
        # 获取过滤后查看器中的当前行号
        filtered_line = self.filtered_viewer.get_current_line_number()
        
        # 获取对应的原始行号
        # if filtered_line < len(self.line_mapping):
        #     original_line = self.line_mapping[filtered_line]
        #     # 在原始查看器中高亮对应行，不需要传入 previous_rect，因为这里我们希望居中显示
        #     self.original_viewer.scroll_to_line(original_line)
            
    def _on_filtered_viewer_mouse_press(self, event):
        """处理过滤视图的鼠标点击事件"""
        # 完全忽略单击事件
        event.accept()

    def _on_filtered_viewer_double_click(self, event):
        """处理过滤视图的双击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            print("\n=== 双击事件开始 ===")
            # 获取双击位置的光标
            cursor = self.filtered_viewer.cursorForPosition(event.pos())
            line_number = cursor.blockNumber()
            click_position = cursor.positionInBlock()  # 获取在行内的点击位置
            print(f"双击位置 - 行号: {line_number}, 行内位置: {click_position}")
            
            if line_number < len(self.line_mapping):
                # 获取当前行对应的原始行号
                original_line = self.line_mapping[line_number]
                print(f"对应的原始行号: {original_line}")
                
                # 从缓存的匹配结果中找到当前行的所有匹配项
                line_matches = []
                print(f"cached_matches: {self.filter_engine.cached_matches}")
                for match in self.filter_engine.cached_matches:
                    if match[3] == original_line:  # match[3] 是行号
                        line_matches.append(match)
                
                print(f"当前行的匹配项数量: {len(line_matches)}")
                if not line_matches:
                    print("没有找到匹配项，退出")
                    return
                    
                # 找到点击位置对应的匹配项索引
                clicked_match_index = -1
                clicked_match = None
                for match in line_matches:
                    start_pos, end_pos = match[0], match[1]
                    if start_pos <= click_position <= end_pos:
                        clicked_match_index = match[4]  # match[4] 是全局索引
                        clicked_match = match
                        print(f"直接点击到匹配项 - 索引: {clicked_match_index}, 位置: {start_pos}-{end_pos}")
                        break
                
                # 如果没有点击在任何匹配项上，使用最近的匹配项
                if clicked_match_index == -1:
                    print("未直接点击到匹配项，寻找最近的匹配项")
                    # 找到最近的匹配项
                    min_distance = float('inf')
                    for match in line_matches:
                        start_pos = match[0]
                        distance = abs(click_position - start_pos)
                        if distance < min_distance:
                            min_distance = distance
                            clicked_match_index = match[4]  # match[4] 是全局索引
                            clicked_match = match
                            print(f"找到最近的匹配项 - 索引: {clicked_match_index}, 距离: {min_distance}")
                
                # 使用导航函数跳转到对应位置
                if clicked_match_index != -1:
                    print(f"准备高亮显示 - 全局索引: {clicked_match_index}")
                    # 高亮显示匹配项
                    keyword_pos = clicked_match[0]
                    keyword_length = clicked_match[1] - clicked_match[0]
                    print(f"关键字信息 - 位置: {keyword_pos}, 长度: {keyword_length}")
                    
                    # 在过滤视图中高亮显示
                    print("在过滤视图中高亮显示")
                    self.filtered_viewer.highlight_line(line_number, keyword_position=keyword_pos,
                                                    keyword_length=keyword_length, center_on_screen=False,select_whole_line=False)
                    # 在原始视图中高亮显示
                    print(f"在原始视图中高亮显示 - 行号: {original_line}")
                    self.original_viewer.highlight_line(original_line, keyword_position=keyword_pos,
                                                    keyword_length=keyword_length, center_on_screen=True,select_whole_line=True)
                    
                    # 更新匹配计数显示
                    self.current_global_match = clicked_match_index
                    display_index = clicked_match_index + 1
                    print(f"更新匹配计数 - 当前/总数: {display_index}/{self.total_matches}")
                    self.filter_input.update_match_count(display_index, self.total_matches)
                else:
                    print("未找到有效的匹配项")
            else:
                print(f"行号 {line_number} 超出映射范围 {len(self.line_mapping)}")
            print("=== 双击事件结束 ===\n")
        event.accept()

    def _on_filter_requested(self, text: str, line_number: int, start_pos: int, end_pos: int):
        """处理过滤请求，记录选中文本的完整位置信息"""
        print(f"on_filter_requested: {text}, {line_number}, {start_pos}, {end_pos}")
        if line_number >= 0:
            self.initial_filter_position = {
                'line_number': line_number,
                'start_pos': start_pos,
                'end_pos': end_pos
            }
        else:
            self.initial_filter_position = None

    def _find_match_index_for_position(self, line_number: int, position: int) -> int:
        """找到指定位置对应的全局匹配索引"""
        if not self.initial_filter_position:
            return 0

        # 获取所有匹配项
        matches = self.filter_engine.get_keyword_matches(self.original_viewer.toPlainText())
        
        # 如果是从选中文本触发的搜索，尝试精确匹配位置
        if isinstance(self.initial_filter_position, dict):
            start_pos = self.initial_filter_position['start_pos']
            end_pos = self.initial_filter_position['end_pos']
            
            # 查找完全匹配的位置
            for match in matches:
                if match[3] == line_number and match[0] == start_pos and match[1] == end_pos:
                    return match[4]  # 返回全局索引
        
        # 如果没有找到精确匹配或不是从选中文本触发，使用近似匹配
        for match in matches:
            if match[3] == line_number and match[0] <= position <= match[1]:
                return match[4]  # 返回全局索引
                
        # 如果没有找到匹配，返回该行的第一个匹配
        for match in matches:
            if match[3] == line_number:
                return match[4]  # 返回该行的第一个匹配的全局索引

        return 0

    def apply_filter(self, expression: str):
        """应用过滤器"""
        # 获取原始文本
        text = self.original_viewer.toPlainText()
        
        if not expression:
            # 如果表达式为空，清除过滤
            self.clear_filter()
            return
            
        # 获取过滤选项
        filter_options = self.filter_input.get_filter_options()
        
        # 如果有正在运行的线程，先停止它
        if hasattr(self, 'thread') and self.thread is not None:
            try:
                if hasattr(self.thread, 'isRunning') and self.thread.isRunning():
                    if hasattr(self, 'worker') and self.worker is not None:
                        self.worker.cancel()  # 取消当前的处理
                    self.thread.quit()
                    self.thread.wait()  # 等待线程结束
            except Exception as e:
                print(f"停止线程时出错: {str(e)}")
                # 确保清理资源
                if hasattr(self, 'worker') and self.worker is not None:
                    self.worker = None
                self.thread = None
        
        # 创建工作线程
        self.thread = QThread()
        self.worker = TextWorker(text, self.filter_engine, expression, filter_options)
        
        # 将worker移动到线程
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.thread.started.connect(self.worker.process)
        self.worker.finished.connect(self._on_filter_processed)
        self.worker.error.connect(self._on_processing_error)
        self.worker.finished.connect(lambda: self._cleanup_thread())  # 使用清理函数
        
        # 启动线程
        self.thread.start()
        
    def _on_filter_processed(self, text: str, filtered_lines: list, line_mapping: list):
        """处理过滤完成"""
        try:
            # 获取过滤选项
            filter_options = self.filter_input.get_filter_options()
            
            # 获取过滤关键字并设置给高亮器
            keywords = self.filter_engine.get_keywords()
            self.original_viewer.highlighter.set_keywords(keywords, filter_options)
            self.filtered_viewer.highlighter.set_keywords(keywords, filter_options)
            
            # 更新过滤后的查看器
            self.line_mapping = line_mapping
            self.filtered_viewer.setPlainText('\n'.join(filtered_lines))
            
            # 计算总匹配数
            self.total_matches = self._calculate_total_matches()
            
            # 如果有匹配项，显示过滤视图
            if self.total_matches > 0:
                self.filtered_viewer.show()  # 显示过滤视图
                
                # 如果有初始过滤位置，找到对应的匹配项
                if self.initial_filter_position:
                    line_number, position = self.initial_filter_position['line_number'], self.initial_filter_position['start_pos']
                    match_index = self._find_match_index_for_position(line_number, position)
                    print(f"match_index: {match_index}")
                    if match_index >= 0:
                        self._on_navigate_to_match(match_index)
                    else:
                        self._on_navigate_to_match(0)
                else:
                    # 否则显示第一个匹配项
                    self._on_navigate_to_match(0)
                self.initial_filter_position = None  # 清除初始位置
        except Exception as e:
            QMessageBox.warning(self, "过滤错误", str(e))
            
    def clear_filter(self):
        # 清除过滤后的查看器
        self.filtered_viewer.clear()
        self.filtered_viewer.hide()  # 隐藏过滤视图
        self.line_mapping = []
        self.filter_input.update_match_count(0, 0)
        # 清除高亮器的关键字
        self.original_viewer.highlighter.set_keywords(set(), {})
        self.filtered_viewer.highlighter.set_keywords(set(), {})

    def load_text(self, text: str):
        """加载文本内容"""
        self.load_text_async(text)
        
    def load_text_async(self, text: str):
        """异步加载文本内容"""
        # 如果有正在运行的线程，先停止它
        if hasattr(self, 'thread') and self.thread is not None:
            try:
                if hasattr(self.thread, 'isRunning') and self.thread.isRunning():
                    if hasattr(self, 'worker') and self.worker is not None:
                        self.worker.cancel()  # 取消当前的处理
                    self.thread.quit()
                    self.thread.wait()  # 等待线程结束
            except Exception as e:
                print(f"停止线程时出错: {str(e)}")
                # 确保清理资源
                if hasattr(self, 'worker') and self.worker is not None:
                    self.worker = None
                self.thread = None
        
        # 创建工作线程
        self.thread = QThread()
        self.worker = TextWorker(
            text,
            self.filter_engine,
            self.filter_input.input.text() if self.filter_input else None,
            self.filter_input.get_filter_options() if self.filter_input else None
        )
        
        # 将worker移动到线程
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.thread.started.connect(self.worker.process)
        self.worker.finished.connect(self._on_text_processed)
        self.worker.error.connect(self._on_processing_error)
        self.worker.finished.connect(lambda: self._cleanup_thread())  # 使用清理函数
        
        # 启动线程
        self.thread.start()
        
    def _on_text_processed(self, text: str, filtered_lines: list, line_mapping: list):
        """处理文本加载完成"""
        self.original_viewer.setPlainText(text)
        if filtered_lines:
            self.filtered_viewer.setPlainText('\n'.join(filtered_lines))
            self.line_mapping = line_mapping
            self.filtered_viewer.show()
            
            # 更新匹配计数
            self.total_matches = self._calculate_total_matches()
            if self.total_matches > 0:
                self._on_navigate_to_match(0)
        else:
            self.clear_filter()
            
    def _on_processing_error(self, error_message: str):
        """处理错误"""
        QMessageBox.warning(self, "处理错误", error_message)

    def _calculate_total_matches(self):
        """计算所有匹配项的总数"""
        return self.filter_engine.get_keyword_total_count()

    def _get_match_at_index(self, global_index):
        """根据全局索引获取对应的行号和行内匹配索引"""
        for match in self.filter_engine.cached_matches:
            if match[4] == global_index:  # match[4] 是全局索引
                return match 
        return None

    def _on_navigate_to_match(self, global_match_index: int):
        """处理导航到指定匹配项
        Args:
            global_match_index: 0-based的全局匹配索引
        """
        if self.total_matches == 0:  # 使用已经计算好的总数
            return
            
        print(f"on_navigate_to_match: {global_match_index} / {self.total_matches}")
        
        # 获取目标匹配
        match = self._get_match_at_index(global_match_index)
        if not match:
            return

        # 更新当前状态（保持0-based）
        self.current_line = match[3]
        self.current_match_index = match[4]
        self.current_global_match = global_match_index
        print(f"current_line: {self.current_line}, current_line_matches: {self.current_line_matches}, current_match_index: {self.current_match_index}, current_global_match: {self.current_global_match}")

        # 获取当前匹配项的位置和长度
        keyword_pos = match[0]
        keyword_length = match[1] - match[0]

        # 在过滤后的视图中高亮并定位
        self.filtered_viewer.highlight_line(self.current_match_index, keyword_position=keyword_pos,
                                        keyword_length=keyword_length, center_on_screen=True,
                                        select_whole_line=False)
        # 在原始视图中执行相同操作
        self.original_viewer.highlight_line(self.current_line , keyword_position=keyword_pos,
                                        keyword_length=keyword_length, center_on_screen=True,
                                        select_whole_line=False)

        # 更新匹配计数（转换为1-based用于显示）
        display_index = self.current_global_match + 1
        self.filter_input.update_match_count(display_index, self.total_matches)

    def set_expression(self, expression: str):
        """设置过滤表达式"""
        self.filter_input.set_expression(expression) 
        
    def _cleanup_thread(self):
        """清理线程资源"""
        try:
            if self.thread is not None:
                # 先处理 worker
                if self.worker is not None:
                    try:
                        self.worker.cancel()  # 尝试取消当前操作
                    except:
                        pass
                    try:
                        self.worker.deleteLater()
                    except:
                        pass
                    self.worker = None

                # 再处理线程
                try:
                    if hasattr(self.thread, 'isRunning') and self.thread.isRunning():
                        self.thread.quit()
                        # 最多等待3秒
                        if not self.thread.wait(3000):
                            print("警告：线程未能在3秒内结束")
                except Exception as e:
                    print(f"停止线程时出错: {str(e)}")

                try:
                    self.thread.deleteLater()
                except:
                    pass
                self.thread = None
        except Exception as e:
            print(f"清理线程资源时出错: {str(e)}")
            # 确保引用被清除
            self.worker = None
            self.thread = None

    def _find_keyword_position(self, text: str, keywords: set) -> Tuple[int, str]:
        """在文本中查找第一个关键字的位置"""
        matches = self.filter_engine.get_keyword_matches(text)
        if matches:
            return matches[0][0], matches[0][2]  # 返回第一个匹配的位置和关键字
        return 0, None

    def _get_all_matches(self, text: str) -> List[Tuple[int, int, str, int, int]]:
        """获取文本中所有关键字的匹配位置"""
        return self.filter_engine.get_keyword_matches(text) 