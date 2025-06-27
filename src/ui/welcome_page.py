from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QMenu
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFontMetrics
from src.resources.theme import THEME
from src.resources.config_manager import ConfigManager
from src.utils.logger import log_ui_event
import os

class SCWelcomePage(QWidget):
    openFileClicked = pyqtSignal()
    openRecentFileClicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()  # 这里会返回单例实例
        # 连接信号
        print("Connecting signal...")
        self.config_manager.recentFilesChanged.connect(self._on_recent_files_changed)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建一个容器来包含所有内容，并设置最大宽度
        container = QWidget()
        container.setMaximumWidth(600)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 欢迎文本
        welcome_label = QLabel("欢迎使用 SC Log Analysis Tool")
        welcome_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME['text']};
                font-size: 24px;
                margin-bottom: 20px;
            }}
        """)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 提示文本
        hint_label = QLabel("点击下方按钮打开日志文件")
        hint_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME['text']};
                font-size: 16px;
                margin-bottom: 30px;
            }}
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 打开文件按钮
        open_button = QPushButton("打开文件")
        open_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['highlight_bg']};
                color: {THEME['text']};
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {THEME['bright_blue']};
            }}
        """)
        open_button.clicked.connect(self._on_open_file_clicked)
        
        # 最近文件列表
        recent_label = QLabel("最近打开的文件")
        recent_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME['text']};
                font-size: 14px;
                margin-top: 30px;
                margin-bottom: 10px;
            }}
        """)
        recent_label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # 左对齐
        
        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                color: {THEME['text']};
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:hover {{
                background-color: {THEME['hover_bg']};
            }}
        """)
        self.recent_list.setMaximumHeight(200)  # 限制最大高度
        self.recent_list.itemClicked.connect(self._on_recent_file_clicked)
        
        # 设置右键菜单
        self.recent_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.recent_list.customContextMenuRequested.connect(self._show_context_menu)
        
        # 添加到容器布局
        container_layout.addStretch()
        container_layout.addWidget(welcome_label)
        container_layout.addWidget(hint_label)
        container_layout.addWidget(open_button)
        container_layout.addWidget(recent_label)
        container_layout.addWidget(self.recent_list)
        container_layout.addStretch()
        
        # 将容器添加到主布局
        layout.addWidget(container)
        
    def _on_open_file_clicked(self):
        """处理打开文件按钮点击"""
        log_ui_event("click", "OpenFileButton", "WelcomePage")
        self.openFileClicked.emit()
        
    def _on_recent_file_clicked(self, item: QListWidgetItem):
        """处理最近文件项点击"""
        filepath = item.data(Qt.ItemDataRole.UserRole)
        log_ui_event("click", "RecentFileItem", f"File: {filepath}")
        self.openRecentFileClicked.emit(filepath)
        
    def _on_recent_files_changed(self):
        """处理最近文件列表变化的回调"""
        print("Signal received: recentFilesChanged")
        self.update_recent_files()
        
    def update_recent_files(self):
        """更新最近文件列表"""
        print("update_recent_files")
        self.recent_list.clear()
        state = self.config_manager.load_state()
        recent_files = state.get("recent_files", [])
        print(f"update_recent_files: {recent_files}")
        for filepath in recent_files:
            item = QListWidgetItem(os.path.basename(filepath))
            item.setToolTip(filepath)
            item.setData(Qt.ItemDataRole.UserRole, filepath)
            self.recent_list.addItem(item)
    
    def resizeEvent(self, event):
        """当窗口大小改变时更新文件列表"""
        super().resizeEvent(event)
        # self.update_recent_files()
                
    def _on_recent_file_clicked(self, item):
        """处理最近文件点击事件"""
        filepath = item.toolTip()
        self.openRecentFileClicked.emit(filepath)
        
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.recent_list.itemAt(pos)
        if not item:
            return
            
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
        """)
        
        # 添加删除操作
        remove_action = menu.addAction("从最近文件列表中移除")
        remove_action.triggered.connect(lambda: self._remove_recent_file(item))
        
        # 显示菜单
        menu.exec(self.recent_list.mapToGlobal(pos))
        
    def _remove_recent_file(self, item):
        """从最近文件列表中移除文件"""
        filepath = item.data(Qt.ItemDataRole.UserRole)
        log_ui_event("remove_recent_file", "WelcomePage", f"File: {filepath}")
        self.config_manager.remove_recent_file(filepath) 