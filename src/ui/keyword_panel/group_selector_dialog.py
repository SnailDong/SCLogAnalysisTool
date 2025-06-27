from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                           QDialogButtonBox, QLabel, QHBoxLayout, QPushButton)
from PyQt6.QtCore import Qt
from src.resources.theme import THEME

class SCGroupSelectorDialog(QDialog):
    def __init__(self, keyword_list, parent=None):
        super().__init__(parent)
        self.keyword_list = keyword_list
        self.selected_group = None
        self.setup_ui()
        self.load_groups()
        
    def setup_ui(self):
        """设置UI"""
        print("[DEBUG] Setting up group selector UI")
        self.setWindowTitle("选择分组")
        layout = QVBoxLayout(self)
        
        # 创建树形控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)  # 隐藏表头
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {THEME['background']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
            }}
            QTreeWidget::item:selected {{
                background: {THEME['highlight']};
            }}
        """)
        self.tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.tree)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background: {THEME['button']['background']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background: {THEME['button']['hover']};
            }}
            QPushButton:pressed {{
                background: {THEME['button']['pressed']};
            }}
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # 确定按钮
        ok_button = QPushButton("确定")
        ok_button.setStyleSheet(f"""
            QPushButton {{
                background: {THEME['button']['background']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background: {THEME['button']['hover']};
            }}
            QPushButton:pressed {{
                background: {THEME['button']['pressed']};
            }}
        """)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # 设置窗口大小
        self.resize(300, 400)
        
        # 加载分组
        self.load_groups()
        
    def load_groups(self):
        """加载分组树"""
        # 清空树
        self.tree.clear()
        
        # 添加默认分组
        default_group = QTreeWidgetItem(["默认分组"])
        default_group.setData(0, Qt.ItemDataRole.UserRole, "default")
        self.tree.addTopLevelItem(default_group)
        
        # 遍历顶级分组
        for i in range(self.keyword_list.tree.topLevelItemCount()):
            item = self.keyword_list.tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == "group":
                # 创建分组项
                group_item = QTreeWidgetItem([item.text(0)])
                group_item.setData(0, Qt.ItemDataRole.UserRole, "group")
                self.tree.addTopLevelItem(group_item)
                
                # 递归添加子分组
                self.add_subgroups(item, group_item)
                
    def add_subgroups(self, source_item, target_item):
        """递归添加子分组"""
        for i in range(source_item.childCount()):
            child = source_item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) == "group":
                # 创建子分组项
                child_item = QTreeWidgetItem([child.text(0)])
                child_item.setData(0, Qt.ItemDataRole.UserRole, "group")
                target_item.addChild(child_item)
                
                # 递归添加子分组的子分组
                self.add_subgroups(child, child_item)
                
    def on_item_clicked(self, item, column):
        """处理项目点击事件"""
        # 如果点击的是分组，展开/折叠它
        if item.data(0, Qt.ItemDataRole.UserRole) == "group":
            item.setExpanded(not item.isExpanded())
            
    def get_selected_group(self):
        """获取选中的分组路径"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return "default"
            
        # 获取选中项
        item = selected_items[0]
        path = []
        
        # 构建分组路径
        while item:
            path.insert(0, item.text(0))
            item = item.parent()
            
        return "/".join(path) 