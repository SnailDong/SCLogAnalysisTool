from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QPushButton, QSplitter
from src.ui.workspace_panel.log_panel.log_viewer import SCLogViewer
from src.ui.workspace_panel.log_panel.filter_log_viewer import SCFilteredLogViewer
from src.ui.workspace_panel.mark_panel.mark_log import SCMarkLogViewer
from src.ui.filter_panel.filter_input import SCFilterInput
from PyQt6.QtCore import Qt
from src.resources.theme import THEME

class SCWorkspacePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.filter_input = SCFilterInput()  # 创建过滤输入框
        
        # 顶部过滤器面板
        main_layout.addWidget(self.filter_input)

        # 创建过滤器视图
        self.filtered_viewer = SCFilteredLogViewer(self.filter_input)
        
        # 创建垂直分割器
        self.vsplitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(self.vsplitter)
        
        # 中部日志原文
        self.log_viewer = self.filtered_viewer.original_viewer
        self.vsplitter.addWidget(self.log_viewer)

        # 连接标记信号
        self.log_viewer.markRequested.connect(self.add_mark)

        # 底部tab+内容区容器
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(60)
        self.tab_list.setStyleSheet(f"""
            QListWidget {{
                background: {THEME['background']};
                border: none;
            }}
            QListWidget::item {{
                color: {THEME['text']};
                font-size: 16px;
                padding: 16px 0;
                border: none;
                text-align: center;
            }}
            QListWidget::item:selected {{
                background: {THEME['tab_active_bg']};
                color: {THEME['keyword_text']};
                border-left: 4px solid {THEME['keyword_text']};
            }}
        """)
        self.tab_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tab_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.tab_list.currentRowChanged.connect(self._on_tab_changed)
        bottom_layout.addWidget(self.tab_list)

        # 右侧内容区和关闭按钮容器
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 顶部关闭按钮
        close_bar = QHBoxLayout()
        close_bar.setContentsMargins(0, 0, 0, 0)
        close_bar.setSpacing(0)
        close_bar.addStretch(1)
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(32, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: THEME['highlight_text'];
                background: transparent;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                background: THEME['hover_bg'];
                border-radius: 4px;
            }
        """)
        self.close_btn.clicked.connect(self._hide_bottom_panel)
        close_bar.addWidget(self.close_btn)
        right_layout.addLayout(close_bar)

        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack)

        bottom_layout.addWidget(right_container)
        
        # 将底部容器添加到分割器
        self.vsplitter.addWidget(bottom_container)

        # 设置分割器的初始大小比例
        self.vsplitter.setStretchFactor(0, 3)  # 日志面板占比
        self.vsplitter.setStretchFactor(1, 2)  # 底部面板占比

        # 下方内容：过滤结果和标记列表
        self.mark_viewer = SCMarkLogViewer()
        self.stack.addWidget(self.filtered_viewer.filtered_viewer)  # 只加过滤结果区
        self.stack.addWidget(self.mark_viewer)
        self.tab_list.addItem(QListWidgetItem("过滤"))
        self.tab_list.addItem(QListWidgetItem("标记"))
        self.tab_list.setCurrentRow(0)

        # 信号联动
        self.filter_input.filterChanged.connect(self._on_filter_changed)
        
        # 默认隐藏底部面板
        self._hide_bottom_panel()

    def set_filepath(self, filepath: str):
        self.mark_viewer.set_filepath(filepath)
        # 日志内容加载到log_viewer和filtered_viewer
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.log_viewer.setPlainText(content)
            self.filtered_viewer.load_text(content)
        except Exception:
            pass

    def get_filtered_view(self):
        return self.filtered_viewer

    def get_mark_view(self):
        return self.mark_viewer

    def add_mark(self, line_number: int, content: str):
        self.mark_viewer.add_mark(line_number, content)

    def remove_mark(self, line_number: int):
        self.mark_viewer.remove_mark(line_number)

    def is_marked(self, line_number: int) -> bool:
        return self.mark_viewer.mark_manager.is_marked(self.mark_viewer.current_filepath, line_number)

    def _on_tab_changed(self, index: int):
        self.stack.setCurrentIndex(index)
        # 更新菜单项的勾选状态
        main_window = self.window()
        if main_window.__class__.__name__ == 'SCMainWindow':
            # 如果切换到过滤标签页，确保菜单项勾选状态正确
            if index == 0:  # 过滤标签页
                main_window.filter_view_action.setChecked(True)
            else:  # 其他标签页
                main_window.filter_view_action.setChecked(False)

    def _on_filter_changed(self, expression: str):
        # 高亮主日志
        filter_options = self.filter_input.get_filter_options()
        self.log_viewer.highlighter.set_keywords({expression} if expression else set(), filter_options)
  

    def _hide_bottom_panel(self):
        # 隐藏所有底部面板的组件
        self.tab_list.hide()
        self.close_btn.hide()
        self.stack.hide()
        
        # 隐藏底部容器
        self.vsplitter.widget(1).hide()
        
        # 调整分割器大小
        sizes = self.vsplitter.sizes()
        self.vsplitter.setSizes([sum(sizes), 0])

    def show_bottom_panel(self):
        # 显示所有底部面板的组件
        self.tab_list.show()
        self.close_btn.show()
        self.stack.show()
        
        # 显示底部容器
        self.vsplitter.widget(1).show()
        
        # 恢复分割器的默认大小比例
        total_height = self.vsplitter.height()
        self.vsplitter.setSizes([int(total_height * 0.6), int(total_height * 0.4)])

    def set_read_only(self, read_only: bool):
        """设置只读模式"""
        # 设置日志查看器的只读状态
        self.log_viewer.setReadOnly(read_only)
        