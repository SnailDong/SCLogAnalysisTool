import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget,
                           QVBoxLayout, QFileDialog, QMenuBar, QToolBar,
                           QDockWidget, QListWidget, QMessageBox, QStackedWidget,
                           QHBoxLayout, QLabel, QPushButton, QMenu)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QColor
from src.ui.welcome_page import SCWelcomePage
from src.ui.workspace_panel.log_panel.log_tab import SCLogTab
from src.ui.widgets.custom_tab import SCCustomTab
from src.ui.keyword_panel.saved_keyword_list import SCSavedKeywordList
from src.resources.config_manager import ConfigManager
from src.resources.theme import THEME
from src.utils.logger import log_ui_event

class SCMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.tabs = []  # 存储标签页对象
        self.keyword_dock = None  # 关键字视图
        self.filter_dock = None   # 过滤视图
        self.setup_ui()
        self.setup_shortcuts()  # 添加快捷键设置
        self.restore_state()
        
        # 启用拖放功能
        self.setAcceptDrops(True)

    def setup_shortcuts(self):
        """设置快捷键"""
        # 打开文件快捷键 (Ctrl+O/Command+O)
        open_shortcut = QAction(self)
        open_shortcut.setShortcut(QKeySequence.StandardKey.Open)  # 使用标准快捷键
        open_shortcut.triggered.connect(self.open_file)
        self.addAction(open_shortcut)
        
        # 关闭标签页快捷键 (Ctrl+W/Command+W)
        close_shortcut = QAction(self)
        close_shortcut.setShortcut(QKeySequence.StandardKey.Close)  # 使用标准快捷键
        close_shortcut.triggered.connect(self._close_current_tab)
        self.addAction(close_shortcut)
        
    def _close_current_tab(self):
        """关闭当前标签页"""
        current_widget = self.stack.currentWidget()
        if isinstance(current_widget, SCLogTab):
            # 找到对应的标签页和标签部件
            for tab, tab_widget in self.tabs:
                if tab == current_widget:
                    self.close_tab(tab, tab_widget)
                    break

    def setup_ui(self):
        self.setWindowTitle("SC Log Analysis Tool")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中央部件和堆叠部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet(f"""
            QToolBar {{
                background: {THEME['tab_bg']};
                border: none;
                spacing: 0px;
                padding: 0px;
            }}
        """)
        self.addToolBar(self.toolbar)
        
        # 创建SCTool按钮和菜单
        self.create_sc_tool_menu()
        
        # 创建堆叠部件
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # 创建欢迎页面
        self.welcome_page = SCWelcomePage()
        self.welcome_page.openFileClicked.connect(self.open_file)
        self.welcome_page.openRecentFileClicked.connect(self.open_recent_file)
        self.stack.addWidget(self.welcome_page)
        
        # 创建关键字停靠窗口
        self.create_keyword_dock()
        
        # 设置应用程序样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {THEME['tab_bg']};
                color: {THEME['text']};
            }}
            QWidget {{
                background-color: {THEME['tab_bg']};
                color: {THEME['text']};
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
            }}
            QScrollBar::handle:vertical:hover {{
                background: {THEME['scrollbar_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: {THEME['scrollbar_bg']};
            }}
            QLineEdit {{
                background-color: {THEME['tab_bg']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
                padding: 4px;
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME['highlight_text']};
            }}
            QListWidget {{
                background-color: {THEME['tab_bg']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
            }}
        """)

    def create_sc_tool_menu(self):
        # 创建SCTool按钮
        self.sc_tool_btn = QPushButton("SCTool")
        self.sc_tool_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {THEME['text']};
                border: none;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {THEME['hover_bg']};
            }}
        """)
        self.toolbar.addWidget(self.sc_tool_btn)
        
        # 创建菜单
        self.menu = QMenu(self)
        self.menu.setStyleSheet(f"""
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
        
        # 添加菜单项
        self.new_action = self.menu.addAction("新建标签页")
        self.new_action.triggered.connect(self.create_new_tab)
        
        self.open_action = self.menu.addAction("打开文件")
        self.open_action.triggered.connect(self.open_file)
        
        # 创建最近文件子菜单
        self.recent_menu = QMenu("打开最近的文件", self)
        self.recent_menu.setStyleSheet(self.menu.styleSheet())
        self.recent_menu.aboutToShow.connect(self.update_recent_files_menu)
        self.menu.addMenu(self.recent_menu)
        
        self.menu.addSeparator()
        
        # 添加视图切换选项
        self.keyword_view_action = self.menu.addAction("关键字视图")
        self.keyword_view_action.setCheckable(True)
        self.keyword_view_action.triggered.connect(self.toggle_keyword_view)
        
        self.filter_view_action = self.menu.addAction("筛选视图")
        self.filter_view_action.setCheckable(True)
        self.filter_view_action.triggered.connect(self.toggle_filter_view)
        
        # 设置按钮的上下文菜单
        self.sc_tool_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sc_tool_btn.customContextMenuRequested.connect(self.show_menu)
        
        # 左键点击也显示菜单
        self.sc_tool_btn.clicked.connect(self.show_menu)
        
        # 添加分隔符
        separator = QLabel("|")
        separator.setStyleSheet(f"""
            QLabel {{
                color: {THEME['separator']};
                margin: 0 8px;
                padding: 4px 0;
                background: {THEME['tab_bg']};
            }}
        """)
        self.toolbar.addWidget(separator)

    def update_recent_files_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.clear()
        state = self.config_manager.load_state()
        recent_files = state.get("recent_files", [])
        
        if not recent_files:
            action = self.recent_menu.addAction("无最近文件")
            action.setEnabled(False)
            return
            
        for filepath in recent_files:
            action = self.recent_menu.addAction(filepath)  # 显示完整路径
            action.setToolTip(filepath)  # 保留工具提示
            action.triggered.connect(lambda checked, path=filepath: self.open_recent_file(path))

    def open_recent_file(self, filepath: str):
        """打开最近的文件"""
        if not os.path.exists(filepath):
            # 显示错误对话框
            QMessageBox.critical(
                self,
                "错误",
                f"文件不存在：\n{filepath}\n\n该文件将从最近打开的文件列表中移除。"
            )
            # 从最近文件列表中移除
            self.config_manager.remove_recent_file(filepath)
            # 更新菜单
            self.update_recent_files_menu()
            return

        # 检查文件是否已经打开
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if isinstance(widget, SCLogTab) and widget.filepath == filepath:
                self.switch_to_tab(widget)
                return
        
        # 更新最近文件列表
        self.config_manager.update_recent_files(filepath)
        
        # 创建新标签页
        self.add_new_tab(filepath)
        self.save_state()

    def show_menu(self):
        # 更新视图状态
        if self.keyword_dock:
            self.keyword_view_action.setChecked(not self.keyword_dock.isHidden())
            
        # 检查当前标签页的过滤视图状态
        current_widget = self.stack.currentWidget()
        if isinstance(current_widget, SCLogTab):
            workspace_panel = current_widget.workspace_panel
            # 检查底部面板是否显示，以及当前是否在过滤标签页
            is_filter_visible = (workspace_panel.tab_list.isVisible() and 
                               workspace_panel.tab_list.currentRow() == 0)
            self.filter_view_action.setChecked(is_filter_visible)
            
        # 显示菜单
        pos = self.sc_tool_btn.mapToGlobal(self.sc_tool_btn.rect().bottomLeft())
        self.menu.popup(pos)

    def toggle_keyword_view(self, checked):
        log_ui_event("toggle_view", "KeywordPanel", f"Visible: {checked}")
        if self.keyword_dock:
            self.keyword_dock.setVisible(checked)

    def toggle_filter_view(self, checked):
        log_ui_event("toggle_view", "FilterPanel", f"Visible: {checked}")
        current_widget = self.stack.currentWidget()
        if isinstance(current_widget, SCLogTab):
            workspace_panel = current_widget.workspace_panel
            if checked:
                # 显示底部面板并切换到过滤标签页
                workspace_panel.show_bottom_panel()
                workspace_panel.tab_list.setCurrentRow(0)
            else:
                # 如果当前是过滤标签页，则隐藏底部面板
                if workspace_panel.tab_list.currentRow() == 0:
                    workspace_panel._hide_bottom_panel()

    def create_keyword_dock(self):
        dock = QDockWidget(self)  # 移除标题文本
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | 
                            Qt.DockWidgetArea.RightDockWidgetArea)
        
        # 创建关键字列表
        self.keyword_list = SCSavedKeywordList()
        self.keyword_list.setStyleSheet(f"""
            QListWidget {{
                background: {THEME['tab_bg']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-radius: 3px;
            }}
            QListWidget::item:hover {{
                background: {THEME['hover_bg']};
            }}
            QListWidget::item:selected {{
                background: {THEME['highlight_bg']};
                color: {THEME['highlight_text']};
            }}
        """)
        self.keyword_list.keywordSelected.connect(self._on_keyword_selected)
        
        # 创建自定义标题栏部件
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(6, 2, 6, 2)
        title_layout.setSpacing(4)
        
        # 标题文本
        title_label = QLabel("保存的关键字")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME['text']};
                font-weight: bold;
            }}
        """)
        
        # 增加分组按钮
        add_group_btn = QPushButton("+")
        add_group_btn.setFixedSize(16, 16)
        add_group_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {THEME['text']};
                border: none;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background: {THEME['tab_hover_bg']};
                border-radius: 3px;
            }}
        """)
        add_group_btn.clicked.connect(self.keyword_list.add_group)
        
        # 最小化按钮
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(16, 16)
        minimize_btn.setStyleSheet(add_group_btn.styleSheet())
        minimize_btn.clicked.connect(lambda: dock.setFloating(not dock.isFloating()))
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet(add_group_btn.styleSheet())
        close_btn.clicked.connect(lambda: self.toggle_keyword_view(False))
        
        # 添加所有部件到标题栏布局
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(add_group_btn)
        title_layout.addWidget(minimize_btn)
        title_layout.addWidget(close_btn)
        
        # 设置自定义标题栏部件
        dock.setTitleBarWidget(title_widget)
        
        # 设置停靠窗口样式
        dock.setStyleSheet(f"""
            QDockWidget {{
                background: {THEME['tab_bg']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
            }}
            QWidget#qt_dockwidget_titlebar {{
                background: {THEME['tab_bg']};
                border-bottom: 1px solid {THEME['border']};
            }}
        """)
        
        dock.setWidget(self.keyword_list)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.keyword_dock = dock

    def _on_keyword_selected(self, expression: str, options: dict):
        """处理关键字选择事件"""
        # 获取当前标签页
        current_widget = self.stack.currentWidget()
        if isinstance(current_widget, SCLogTab):
            # 设置过滤输入框的文本和选项
            current_widget.workspace_panel.get_filtered_view().filter_input.set_expression(expression)
            current_widget.workspace_panel.get_filtered_view().filter_input.set_filter_options(options)
            
    def add_saved_keyword(self, expression: str):
        """添加关键字到保存列表"""
        # 获取当前标签页
        current_widget = self.stack.currentWidget()
        if isinstance(current_widget, SCLogTab):
            # 获取当前过滤选项
            options = current_widget.workspace_panel.get_filtered_view().filter_input.get_filter_options()
            # 设置当前过滤选项到关键字列表
            self.keyword_list.set_current_filter_options(options)
        # 添加关键字
        self.keyword_list.add_keyword(expression)
        self.save_state()

    def add_new_tab(self, filepath: str = "") -> SCLogTab:
        new_tab = SCLogTab(filepath)
        # 如果有文件路径使用文件名，否则使用 "New Tab"
        name = os.path.basename(filepath) if filepath else "New Tab"
        
        # 如果已经有标签页，添加分隔符
        if self.tabs and not self.toolbar.actions()[-1].isSeparator():
            separator = QLabel("|")
            separator.setStyleSheet(f"""
                QLabel {{
                    color: {THEME['separator']};
                    margin: 0;
                    padding: 4px 0;
                    background: {THEME['tab_bg']};
                }}
            """)
            self.toolbar.addWidget(separator)
        
        # 创建自定义标签
        tab_widget = SCCustomTab(name, is_read_only=bool(filepath))  # 如果有文件路径则为只读，否则为可编辑
        tab_widget.closeClicked.connect(lambda: self.close_tab(new_tab, tab_widget))
        tab_widget.clicked.connect(lambda: self.switch_to_tab(new_tab))
        tab_widget.readOnlyChanged.connect(lambda read_only: new_tab.set_read_only(read_only))  # 连接只读模式信号
        
        # 添加到工具栏
        self.toolbar.addWidget(tab_widget)
        
        # 存储标签页
        self.tabs.append((new_tab, tab_widget))
        
        # 添加到堆叠部件
        self.stack.addWidget(new_tab)
        self.switch_to_tab(new_tab)
        
        # 确保显示编辑器视图
        self.show_editor_view()
        
        return new_tab

    def switch_to_tab(self, tab: SCLogTab):
        log_ui_event("switch_tab", "MainWindow", f"Tab: {tab.filepath if tab.filepath else 'Untitled'}")
        # 更新标签页状态
        for t, widget in self.tabs:
            widget.set_selected(t == tab)
            
        # 切换到对应的部件
        self.stack.setCurrentWidget(tab)

    def close_tab(self, tab: SCLogTab, tab_widget: SCCustomTab):
        log_ui_event("close_tab", "MainWindow", f"Tab: {tab.filepath if tab.filepath else 'Untitled'}")
        
        # 显示保存确认对话框
        reply = tab.show_save_dialog()
        if reply == QMessageBox.StandardButton.Cancel:
            return  # 用户取消关闭
        
        # 获取标签页的索引
        tab_index = -1
        for i, (t, w) in enumerate(self.tabs):
            if t == tab:
                tab_index = i
                break
        
        if tab_index >= 0:
            # 如果不是第一个标签，删除前面的分隔符
            if tab_index > 0:
                # 查找分隔符并删除
                actions = self.toolbar.actions()
                for i in range(len(actions)):
                    widget = self.toolbar.widgetForAction(actions[i])
                    if isinstance(widget, QLabel) and widget.text() == "|":
                        self.toolbar.removeAction(actions[i])
                        break
            # 如果是最后一个标签，删除后面的分隔符
            elif tab_index < len(self.tabs) - 1:
                # 查找分隔符并删除
                actions = self.toolbar.actions()
                for i in range(len(actions)):
                    widget = self.toolbar.widgetForAction(actions[i])
                    if isinstance(widget, QLabel) and widget.text() == "|":
                        self.toolbar.removeAction(actions[i])
                        break
        
        # 从工具栏移除标签
        for action in self.toolbar.actions():
            if self.toolbar.widgetForAction(action) == tab_widget:
                self.toolbar.removeAction(action)
                break
        
        # 从列表中移除
        self.tabs = [(t, w) for t, w in self.tabs if t != tab]
        
        # 如果有文件路径，更新最近文件列表和已打开文件列表
        if tab.filepath:
            self.config_manager.update_recent_files(tab.filepath, is_close=True)
        
        # 移除标签页
        self.stack.removeWidget(tab)
        tab.deleteLater()
        tab_widget.deleteLater()
        
        # 如果没有标签页了，显示欢迎页面
        if not self.tabs:
            self.show_welcome_page()
        else:
            # 切换到最后一个标签页
            last_tab, _ = self.tabs[-1]
            self.switch_to_tab(last_tab)
        
        self.save_state()

    def open_file(self):
        log_ui_event("open_file_dialog", "MainWindow")
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "打开日志文件",
            "",
            "所有文件 (*.*)"
        )
        
        if filename:
            log_ui_event("open_file", "MainWindow", f"File: {filename}")
            # 检查文件是否已经打开
            for i in range(self.stack.count()):
                widget = self.stack.widget(i)
                if isinstance(widget, SCLogTab) and widget.filepath == filename:
                    self.switch_to_tab(widget)
                    return
            
            # 更新最近文件列表
            self.config_manager.update_recent_files(filename)
            
            # 创建新标签页
            self.add_new_tab(filename)
            self.save_state()

    def show_welcome_page(self):
        """显示欢迎页面"""
        log_ui_event("show_page", "MainWindow", "WelcomePage")
        self.welcome_page.update_recent_files()  # 更新最近文件列表
        self.stack.setCurrentWidget(self.welcome_page)
        # 隐藏关键字面板
        for dock in self.findChildren(QDockWidget):
            dock.hide()

    def show_editor_view(self):
        """显示编辑器视图"""
        log_ui_event("show_page", "MainWindow", "EditorView")
        # 显示关键字面板
        for dock in self.findChildren(QDockWidget):
            dock.show()

    def save_state(self):
        """保存程序状态"""
        opened_files = []
        for t, _ in self.tabs:
            filepath = t.filepath
            if filepath:
                opened_files.append(filepath)
        
        current_widget = self.stack.currentWidget()
        current_index = 0  # 默认为欢迎页面
        if isinstance(current_widget, SCLogTab):
            for i, (t, _) in enumerate(self.tabs):
                if t == current_widget:
                    current_index = i
                    break
        
        # 获取所有关键字分组
        keyword_groups = self.keyword_list.get_all_keywords()
        
        # 获取当前的最近文件列表
        state = self.config_manager.load_state()
        recent_files = state.get("recent_files", [])
        
        self.config_manager.save_state(opened_files, current_index, keyword_groups, recent_files)

    def restore_state(self):
        """恢复程序状态"""
        state = self.config_manager.load_state()
        
        # 恢复保存的关键字分组
        self.keyword_list.load_keywords(state["keyword_groups"])
        
        # 恢复打开的文件
        if state["opened_files"]:
            valid_files = []  # 用于存储有效的文件
            for filepath in state["opened_files"]:
                if os.path.exists(filepath):
                    self.add_new_tab(filepath)
                    valid_files.append(filepath)
                else:
                    # 显示错误对话框
                    QMessageBox.critical(
                        self,
                        "错误",
                        f"文件不存在：\n{filepath}\n\n该文件将从最近打开的文件列表中移除。"
                    )
                    # 从最近文件列表中移除
                    self.config_manager.update_recent_files(filepath, is_close=True)
            
            # 如果有有效的文件，切换到指定的标签页
            if valid_files:
                # 确保 current_tab 索引有效
                current_tab = min(state["current_tab"], len(valid_files) - 1)
                if current_tab >= 0:
                    tab, _ = self.tabs[current_tab]
                    if isinstance(tab, SCLogTab):
                        self.switch_to_tab(tab)
            else:
                # 如果没有有效的文件，显示欢迎页面
                self.show_welcome_page()
        else:
            # 如果没有保存的文件，显示欢迎页面
            self.show_welcome_page()
            
        # 更新最近文件菜单
        self.update_recent_files_menu()

    def closeEvent(self, event):
        """程序关闭时保存状态"""
        self.save_state()
        super().closeEvent(event)

    def dragEnterEvent(self, event):
        """处理拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event):
        """处理放下事件"""
        urls = event.mimeData().urls()
        for url in urls:
            # 获取文件路径
            filepath = url.toLocalFile()
            if os.path.isfile(filepath):
                # 检查文件是否已经打开
                for i in range(self.stack.count()):
                    widget = self.stack.widget(i)
                    if isinstance(widget, SCLogTab) and widget.filepath == filepath:
                        self.switch_to_tab(widget)
                        return
                
                # 更新最近文件列表
                self.config_manager.update_recent_files(filepath)
                
                # 创建新标签页
                self.add_new_tab(filepath)
                self.save_state()

    def create_new_tab(self):
        """创建新的标签页"""
        log_ui_event("create_tab", "MainWindow", "New tab created")
        new_tab = self.add_new_tab()
        # 设置为可编辑模式
        new_tab.set_read_only(False)
        # 设置为已修改状态
        new_tab.is_modified = True
        # 设置默认地址
        new_tab.filepath = ""
        # 更新标签页标题
        new_tab._update_tab_title()
        
        # 找到对应的标签部件并设置只读状态为 False
        for tab, tab_widget in self.tabs:
            if tab == new_tab:
                tab_widget.is_read_only = False
                break
                
        return new_tab

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SCMainWindow()
    window.show()
    sys.exit(app.exec()) 