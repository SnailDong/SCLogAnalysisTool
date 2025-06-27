from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QMenu, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from src.resources.theme import THEME
from src.utils.logger import log_ui_event
import os

class SCCustomTab(QWidget):
    closeClicked = pyqtSignal()
    clicked = pyqtSignal()
    readOnlyChanged = pyqtSignal(bool)  # 新增信号
    
    def __init__(self, title, parent=None, is_read_only=True):
        super().__init__(parent)
        self.title = title
        self.is_selected = False
        self.is_read_only = is_read_only  # 使用传入的参数
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # 文件名标签
        self.title_label = QLabel(self.title)
        # 设置最大宽度和省略模式
        self.title_label.setMaximumWidth(150)  # 设置最大宽度
        self.title_label.setMinimumWidth(50)   # 设置最小宽度
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # 启用省略模式
        metrics = self.title_label.fontMetrics()
        elided_text = metrics.elidedText(self.title, Qt.TextElideMode.ElideMiddle, 150)
        self.title_label.setText(elided_text)
        
        # 关闭按钮
        self.close_button = QLabel("×")
        self.close_button.setStyleSheet(f"""
            QLabel {{
                color: {THEME['tab_text']};
                padding: 2px 4px;
                border-radius: 3px;
                background: transparent;
            }}
            QLabel:hover {{
                background: {THEME['tab_hover_bg']};
            }}
        """)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.close_button)
        
        # 设置整体样式
        self.setStyleSheet(f"""
            SCCustomTab {{
                background: {THEME['tab_bg']};
                border-radius: 4px;
                margin: 4px 0px 4px 0;
                border-bottom: 2px solid transparent;
                border-right: 1px solid {THEME['tab_border']};
                padding-right: 4px;
            }}
            SCCustomTab[selected="true"] {{
                border-bottom: 2px solid {THEME['tab_active_text']};
                padding-bottom: 2px;
            }}
        """)
        
        # 连接信号
        self.close_button.mousePressEvent = self._on_close_clicked
        self.mousePressEvent = self._on_tab_clicked
        
        # 设置固定高度和最大宽度
        self.setFixedHeight(32)
        self.setMaximumWidth(200)  # 设置整个标签的最大宽度
        
        # 初始化未选中状态
        self.set_selected(False)
        
        # 设置右键菜单策略
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def _on_close_clicked(self, event):
        log_ui_event("click", "TabCloseButton", f"Tab: {self.title}")
        self.closeClicked.emit()
        
    def _on_tab_clicked(self, event):
        log_ui_event("click", "TabItem", f"Tab: {self.title}")
        self.clicked.emit()
        
    def set_selected(self, selected):
        if selected != self.is_selected:
            self.is_selected = selected
            log_ui_event("state_change", "TabItem", f"Tab: {self.title}, Selected: {selected}")
            
        self.setProperty("selected", selected)
        
        # 更新标签文本样式
        if selected:
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {THEME['tab_active_text']};
                    font-weight: bold;
                    background: transparent;
                }}
            """)
            self.close_button.setStyleSheet(f"""
                QLabel {{
                    color: {THEME['tab_active_text']};
                    padding: 2px 4px;
                    border-radius: 3px;
                    background: transparent;
                }}
                QLabel:hover {{
                    background: {THEME['tab_hover_bg']};
                }}
            """)
        else:
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {THEME['tab_text']};
                    font-weight: normal;
                    background: transparent;
                }}
            """)
            self.close_button.setStyleSheet(f"""
                QLabel {{
                    color: {THEME['tab_text']};
                    padding: 2px 4px;
                    border-radius: 3px;
                    background: transparent;
                }}
                QLabel:hover {{
                    background: {THEME['tab_hover_bg']};
                }}
            """)
        
        # 刷新样式
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        
    def setTitle(self, title):
        """更新标签标题，保持省略效果"""
        old_title = self.title
        self.title = title
        metrics = self.title_label.fontMetrics()
        elided_text = metrics.elidedText(title, Qt.TextElideMode.ElideMiddle, 150)
        self.title_label.setText(elided_text)
        log_ui_event("title_change", "TabItem", f"Old: {old_title}, New: {title}")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME['tab_bg']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
                padding: 5px;
            }}
            QMenu::item {{
                padding: 5px 15px 5px 8px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {THEME['hover_bg']};
            }}
            QMenu::indicator {{
                left: 4px;
                width: 16px;
                height: 16px;
            }}
        """)
        
        # 获取主窗口和当前标签页
        main_window = self.window()
        if main_window.__class__.__name__ == 'SCMainWindow':
            current_tab = None
            for tab, tab_widget in main_window.tabs:
                if tab_widget == self:
                    current_tab = tab
                    break
                    
            if current_tab and current_tab.filepath:  # 只在有文件路径时显示只读模式选项
                # 只读模式选项
                read_only_action = menu.addAction("只读模式")
                read_only_action.setCheckable(True)
                read_only_action.setChecked(self.is_read_only)
                read_only_action.triggered.connect(self.toggle_read_only)
                menu.addSeparator()
        
        # 关闭选项
        close_action = menu.addAction("关闭标签页")
        close_action.triggered.connect(self.closeClicked.emit)
        
        # 显示菜单
        menu.exec(self.mapToGlobal(pos))
        
    def toggle_read_only(self):
        """切换只读模式
        
        当切换到只读模式时：
        1. 如果文件被修改，弹出保存对话框
           - 选择保存：保存后进入只读模式
           - 选择不保存：恢复文件内容后进入只读模式
           - 选择取消：保持编辑模式
        2. 如果文件未修改，直接进入只读模式
        """
        # 获取主窗口和当前标签页
        main_window = self.window()
        if main_window.__class__.__name__ != 'SCMainWindow':
            return
            
        current_tab = None
        for tab, tab_widget in main_window.tabs:
            if tab_widget == self:
                current_tab = tab
                break
                
        if not current_tab:
            return
            
        # 如果要切换到只读模式，且文件被修改
        if not self.is_read_only and current_tab.is_modified:
            # 显示保存确认对话框
            reply = current_tab.show_save_dialog()
            
            if reply == QMessageBox.StandardButton.Save:
                # 已在show_save_dialog中处理保存
                self.is_read_only = True
                # 更新标签页标题（移除*号）
                name = os.path.basename(current_tab.filepath) if current_tab.filepath else "未命名"
                if name.endswith('*'):
                    self.setTitle(name[:-1])
            elif reply == QMessageBox.StandardButton.Discard:
                # 不保存，恢复文件内容
                if current_tab.filepath:
                    current_tab.load_file(current_tab.filepath)
                self.is_read_only = True
                # 更新标签页标题（移除*号）
                name = os.path.basename(current_tab.filepath) if current_tab.filepath else "未命名"
                if name.endswith('*'):
                    self.setTitle(name[:-1])
            elif reply == QMessageBox.StandardButton.Cancel:
                # 取消操作，保持编辑模式
                return
        else:
            # 如果文件未修改，直接切换模式
            self.is_read_only = not self.is_read_only
            
        log_ui_event("toggle_read_only", "TabItem", f"Tab: {self.title}, ReadOnly: {self.is_read_only}")
        self.readOnlyChanged.emit(self.is_read_only)
