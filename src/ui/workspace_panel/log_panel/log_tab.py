from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from src.ui.workspace_panel.workspace_panel import SCWorkspacePanel
from src.utils.logger import log_ui_event
from src.utils.file_utils import read_file_with_encoding
import os

class SCLogTab(QWidget):
    def __init__(self, filepath: str = "", parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self._is_modified = False  # 文件是否被修改
        self.setup_ui()
        self.setup_shortcuts()
        if filepath:
            self.load_file(filepath)
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工作区面板
        self.workspace_panel = SCWorkspacePanel()
        layout.addWidget(self.workspace_panel)
        
        # 连接过滤器变化信号
        self.workspace_panel.get_filtered_view().filterChanged.connect(self._on_filter_changed)
        
        # 连接文本修改信号
        self.workspace_panel.log_viewer.textModified.connect(self._on_text_modified)
        
    def setup_shortcuts(self):
        """设置快捷键"""
        # 保存文件快捷键 (Command+S/Ctrl+S)
        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self._on_save_shortcut)
        
    def _on_filter_changed(self, expression: str):
        """处理过滤器变化"""
        # 获取主窗口实例
        main_window = self.window()
        if main_window.__class__.__name__ == 'SCMainWindow':
            # 更新关键字列表中的当前过滤文本
            main_window.keyword_list.set_current_filter_text(expression)
            
    @property
    def is_modified(self) -> bool:
        """获取文件是否被修改"""
        return self._is_modified
        
    @is_modified.setter
    def is_modified(self, value: bool):
        """设置文件是否被修改，并更新标签页标题"""
        if self._is_modified != value:
            self._is_modified = value
            # 更新标签页标题
            self._update_tab_title()
            
    def _update_tab_title(self):
        """更新标签页标题"""
        main_window = self.window()
        if main_window.__class__.__name__ == 'SCMainWindow':
            for tab, tab_widget in main_window.tabs:
                if tab == self:
                    name = os.path.basename(self.filepath) if self.filepath else "New Tab"
                    # 先确保名字不带*号
                    if name.endswith('*'):
                        name = name[:-1]
                    # 如果已修改，添加*号
                    if self._is_modified:
                        name = name + '*'
                    tab_widget.setTitle(name)
                    break
            
    def _on_text_modified(self):
        """处理文本修改事件"""
        # 如果是只读模式，不设置修改标志
        if self.workspace_panel.log_viewer.isReadOnly():
            return
            
        if not self.is_modified:
            self.is_modified = True
            
    def set_read_only(self, read_only: bool):
        """设置只读模式"""
        self.workspace_panel.set_read_only(read_only)
        
    def load_file(self, filename: str) -> bool:
        try:
            content = read_file_with_encoding(filename)
            self.workspace_panel.get_filtered_view().load_text(content)
            self.workspace_panel.set_filepath(filename)
            self.filepath = filename
            # 重置修改状态
            self.is_modified = False
            return True
        except (UnicodeDecodeError, FileNotFoundError) as e:
            QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
            return False
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取文件时发生未知错误: {str(e)}")
            return False

    def save_file(self) -> bool:
        """保存文件"""
        try:
            # 如果没有路径，弹出保存对话框
            if not self.filepath:
                filepath, _ = QFileDialog.getSaveFileName(
                    self,
                    "保存文件",
                    "",
                    "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*.*)"
                )
                if not filepath:  # 用户取消了保存
                    return False
                self.filepath = filepath

            # 保存文件内容
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(self.workspace_panel.log_viewer.toPlainText())
                
            self.is_modified = False
            # 更新标签页标题，移除*号
            main_window = self.window()
            if main_window.__class__.__name__ == 'SCMainWindow':
                for tab, tab_widget in main_window.tabs:
                    if tab == self:
                        name = os.path.basename(self.filepath)
                        if name.endswith('*'):
                            tab_widget.setTitle(name[:-1])
                        break
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")
            return False

    def show_save_dialog(self) -> int:
        """显示保存确认对话框
        
        Returns:
            int: 返回用户的选择
                QMessageBox.StandardButton.Save - 用户选择保存
                QMessageBox.StandardButton.Discard - 用户选择不保存
                QMessageBox.StandardButton.Cancel - 用户选择取消
        """
        if not self.is_modified:
            return QMessageBox.StandardButton.Discard
            
        reply = QMessageBox.question(
            self,
            "保存修改",
            f"文件 {os.path.basename(self.filepath) if self.filepath else '未命名'} 已被修改，是否保存？",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Save:
            # 尝试保存文件
            if not self.save_file():
                # 如果保存失败，返回Cancel
                return QMessageBox.StandardButton.Cancel
            # 保存成功，重置修改状态
            self.is_modified = False
        elif reply == QMessageBox.StandardButton.Discard:
            # 不保存，重置修改状态
            self.is_modified = False
                
        return reply

    def _on_save_shortcut(self):
        """处理保存快捷键"""
        # 只在非只读模式下响应保存快捷键
        if not self.workspace_panel.log_viewer.isReadOnly() and self.is_modified:
            log_ui_event("shortcut", "SaveFile", f"File: {self.filepath if self.filepath else 'Untitled'}")
            if self.save_file():
                self.is_modified = False
