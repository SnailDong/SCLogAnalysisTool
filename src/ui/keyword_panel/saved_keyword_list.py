from PyQt6.QtWidgets import (QWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLineEdit, QMessageBox, QSplitter,
                           QListWidget, QListWidgetItem, QLabel, QTreeWidget,
                           QTreeWidgetItem, QInputDialog, QMenu, QDialog, QDialogButtonBox)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPoint
from PyQt6.QtGui import (QFont, QTextCursor, QIcon, QColor, QPalette, 
                      QTextCharFormat, QCursor, QKeySequence, QAction)
from src.utils.highlighter import LogHighlighter
from src.ui.filter_panel.filter_engine import FilterEngine
from src.resources.theme import THEME
from src.utils.const import KEYWORDS_FILE
from src.ui.keyword_panel.keyword_dialog import SCKeywordDialog
from typing import Dict, List, TYPE_CHECKING
import re
import json
import os
class SCSavedKeywordList(QWidget):
    keywordSelected = pyqtSignal(str, dict)  # 修改信号以包含选项
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_group = "default"  # 默认选中的分组
        self.last_selected_group = None  # 记录最后一次选中关键字所在的分组
        self.current_filter_text = ""  # 存储当前过滤框中的文本
        self.current_filter_options = None  # 存储当前过滤选项
        
        # 确保存储目录存在
        os.makedirs(os.path.dirname(KEYWORDS_FILE), exist_ok=True)
        
        self.setup_ui()
        self.load_from_file()  # 从文件加载保存的关键字
        
    def save_to_file(self):
        """保存关键字到文件"""
        try:
            keywords = self.get_all_keywords()
            with open(KEYWORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(keywords, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"保存关键字失败：{str(e)}")
            
    def load_from_file(self):
        """从文件加载关键字"""
        try:
            if os.path.exists(KEYWORDS_FILE):
                with open(KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                    keywords = json.load(f)
                self.load_keywords(keywords)
            else:
                # 如果文件不存在，创建默认分组
                self.load_keywords({"default": []})
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"加载关键字失败：{str(e)}")
            # 创建默认分组
            self.load_keywords({"default": []})

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建树形视图
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {THEME['background']};
                border: 1px solid {THEME['border']};
                border-radius: 4px;
            }}
            QTreeWidget::item {{
                color: {THEME['text']};
                padding: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {THEME['highlight_bg']};
            }}
            QTreeWidget::item:hover {{
                background-color: {THEME['hover_bg']};
            }}
        """)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.tree)

    def _check_duplicate_group_name(self, parent_item: QTreeWidgetItem, name: str) -> bool:
        """检查同级分组中是否存在相同名称
        
        Args:
            parent_item: 父分组项，如果是顶级分组则为None
            name: 要检查的分组名称
            
        Returns:
            bool: 如果存在重名返回True，否则返回False
        """
        if parent_item is None:
            # 检查顶级分组
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if item.data(0, Qt.ItemDataRole.UserRole) == "group" and item.text(0) == name:
                    return True
        else:
            # 检查子分组
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if child.data(0, Qt.ItemDataRole.UserRole) == "group" and child.text(0) == name:
                    return True
        return False

    def _add_sub_group(self, parent_item: QTreeWidgetItem):
        """添加子分组"""
        # 创建输入对话框
        dialog = QInputDialog(self)
        dialog.setWindowTitle("新建分组")
        dialog.setLabelText("请输入分组名称：")
        # 设置对话框大小为屏幕的1/3
        screen = dialog.screen()
        screen_size = screen.size()
        dialog_width = screen_size.width() // 3
        dialog_height = screen_size.height() // 3
        dialog.resize(dialog_width, dialog_height)
        # 将对话框移动到屏幕中心
        dialog.move(screen.geometry().center() - dialog.frameGeometry().center())
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.textValue()
            if name:
                if name == "default":
                    QMessageBox.warning(self, "警告", "不能使用保留名称 'default'")
                    return
                # 检查是否已存在同名分组
                if self._check_duplicate_group_name(parent_item, name):
                    QMessageBox.warning(self, "警告", "该分组名称已存在于同级分组中")
                    return
                
                # 创建新分组
                group_item = QTreeWidgetItem([name])
                group_item.setData(0, Qt.ItemDataRole.UserRole, "group")
                
                # 找到插入位置（在所有子分组之后，关键字之前）
                insert_pos = 0
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    if child.data(0, Qt.ItemDataRole.UserRole) != "group":
                        break
                    insert_pos += 1
                
                # 在正确的位置插入新分组
                parent_item.insertChild(insert_pos, group_item)
                parent_item.setExpanded(True)
                group_item.setExpanded(True)
                
                # 保存到文件
                self.save_to_file()

    def _add_keyword_to_group(self, parent_item: QTreeWidgetItem):
        """添加关键字到分组"""
        # 获取主窗口实例
        main_window = self.window()
        # 使用字符串类型检查来避免循环导入
        if main_window.__class__.__name__ == 'SCMainWindow':
            # 获取当前标签页
            current_widget = main_window.stack.currentWidget()
            if current_widget.__class__.__name__ == 'SCLogTab':
                # 获取过滤输入框的文本和选项
                filter_text = current_widget.workspace_panel.get_filtered_view().filter_input.input.text()
                filter_options = current_widget.workspace_panel.get_filtered_view().filter_input.get_filter_options()
                # 如果过滤输入框有值，优先使用它
                if filter_text:
                    self.current_filter_text = filter_text
                    self.current_filter_options = filter_options

        # 创建添加关键字对话框
        dialog = SCKeywordDialog(self, self.current_filter_text, self.current_filter_options, keyword_list=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            keyword = dialog.get_keyword()
            alias = dialog.get_alias()
            options = dialog.get_options()
            
            if keyword:
                # 检查是否已存在
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    if (child.data(0, Qt.ItemDataRole.UserRole) != "group" and 
                        child.data(0, Qt.ItemDataRole.UserRole + 2) == keyword):
                        QMessageBox.warning(self, "警告", "该关键字已存在")
                        return
                
                # 创建关键字项
                keyword_item = QTreeWidgetItem([alias if alias else keyword])  # 显示文本
                keyword_item.setData(0, Qt.ItemDataRole.UserRole, "keyword")
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 1, options)  # 选项
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 2, keyword)  # 实际关键字
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 3, alias)  # 别名
                
                # 找到插入位置（在所有子分组之后）
                insert_pos = 0
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    if child.data(0, Qt.ItemDataRole.UserRole) == "group":
                        insert_pos += 1
                    else:
                        break
                
                # 在正确的位置插入关键字
                parent_item.insertChild(insert_pos, keyword_item)
                parent_item.setExpanded(True)
                
                # 保存到文件
                self.save_to_file()

    def add_group(self):
        """添加顶级分组"""
        # 创建输入对话框
        dialog = QInputDialog(self)
        dialog.setWindowTitle("新建分组")
        dialog.setLabelText("请输入分组名称：")
        # 设置对话框大小为屏幕的1/3
        screen = dialog.screen()
        screen_size = screen.size()
        dialog_width = screen_size.width() // 3
        dialog_height = screen_size.height() // 3
        dialog.resize(dialog_width, dialog_height)
        # 将对话框移动到屏幕中心
        dialog.move(screen.geometry().center() - dialog.frameGeometry().center())
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.textValue()
            if name:
                if name == "default":
                    QMessageBox.warning(self, "警告", "不能使用保留名称 'default'")
                    return
                # 检查是否已存在同名分组
                if self._check_duplicate_group_name(None, name):
                    QMessageBox.warning(self, "警告", "该分组名称已存在于顶级分组中")
                    return
                    
                group_item = QTreeWidgetItem([name])
                group_item.setData(0, Qt.ItemDataRole.UserRole, "group")
                self.tree.addTopLevelItem(group_item)
                group_item.setExpanded(True)
                
                # 保存到文件
                self.save_to_file()

    def delete_group(self, item: QTreeWidgetItem):
        """删除分组"""
        reply = QMessageBox.question(self, "确认删除",
                                   f"确定要删除分组 '{item.text(0)}' 及其所有内容吗？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
            # 保存到文件
            self.save_to_file()

    def delete_keyword(self, parent_item: QTreeWidgetItem, keyword_item: QTreeWidgetItem):
        """删除关键字"""
        reply = QMessageBox.question(self, "确认删除",
                                   f"确定要删除关键字 '{keyword_item.text(0)}' 吗？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            parent_item.removeChild(keyword_item)
            # 保存到文件
            self.save_to_file()

    def rename_group(self, item: QTreeWidgetItem):
        """重命名分组"""
        old_name = item.text(0)
        # 创建输入对话框
        dialog = QInputDialog(self)
        dialog.setWindowTitle("重命名分组")
        dialog.setLabelText("请输入新的分组名称：")
        dialog.setTextValue(old_name)
        # 设置对话框大小为屏幕的1/3
        screen = dialog.screen()
        screen_size = screen.size()
        dialog_width = screen_size.width() // 3
        dialog_height = screen_size.height() // 3
        dialog.resize(dialog_width, dialog_height)
        # 将对话框移动到屏幕中心
        dialog.move(screen.geometry().center() - dialog.frameGeometry().center())
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.textValue()
            if new_name and new_name != old_name:
                if new_name == "default":
                    QMessageBox.warning(self, "警告", "不能使用保留名称 'default'")
                    return
                    
                # 检查是否与同级分组重名
                parent = item.parent()
                if self._check_duplicate_group_name(parent, new_name):
                    QMessageBox.warning(self, "警告", "该分组名称已存在于同级分组中")
                    return
                        
                item.setText(0, new_name)
                # 保存到文件
                self.save_to_file()

    def _edit_keyword(self, parent_item: QTreeWidgetItem, keyword_item: QTreeWidgetItem):
        """修改关键字"""
        # 获取当前关键字的文本、别名和选项
        current_text = keyword_item.data(0, Qt.ItemDataRole.UserRole + 2) or keyword_item.text(0)  # 获取实际的关键字
        current_alias = keyword_item.data(0, Qt.ItemDataRole.UserRole + 3) or ""  # 获取别名
        current_options = keyword_item.data(0, Qt.ItemDataRole.UserRole + 1) or {}
        
        # 创建修改关键字对话框
        dialog = SCKeywordDialog(self, current_text, current_options, current_alias, keyword_list=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_text = dialog.get_keyword()
            new_alias = dialog.get_alias()
            new_options = dialog.get_options()
            
            if new_text:
                # 检查是否与其他关键字重名（排除自己）
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    if (child != keyword_item and 
                        child.data(0, Qt.ItemDataRole.UserRole) != "group" and 
                        child.data(0, Qt.ItemDataRole.UserRole + 2) == new_text):
                        QMessageBox.warning(self, "警告", "该关键字已存在")
                        return
                
                # 更新关键字文本、别名和选项
                keyword_item.setText(0, new_alias if new_alias else new_text)  # 显示文本
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 2, new_text)  # 实际关键字
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 3, new_alias)  # 别名
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 1, new_options)  # 选项
                
                # 保存到文件
                self.save_to_file()

    def _show_context_menu(self, position: QPoint):
        """显示上下文菜单"""
        item = self.tree.itemAt(position)
        
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME['background']};
                color: {THEME['text']};
                border: 1px solid {THEME['border']};
            }}
            QMenu::item:selected {{
                background-color: {THEME['highlight_bg']};
            }}
        """)
        
        if item:
            # 如果点击的是分组（包括顶级分组和子分组）
            if item.data(0, Qt.ItemDataRole.UserRole) == "group":
                # 添加新建子分组选项
                new_sub_group_action = menu.addAction("新建分组")
                new_sub_group_action.triggered.connect(lambda: self._add_sub_group(item))
                
                # 添加添加关键字选项
                add_keyword_action = menu.addAction("添加关键字")
                add_keyword_action.triggered.connect(lambda: self._add_keyword_to_group(item))
                
                if item.text(0) != "default":
                    menu.addSeparator()
                    rename_action = menu.addAction("重命名分组")
                    rename_action.triggered.connect(lambda: self.rename_group(item))
                    delete_action = menu.addAction("删除分组")
                    delete_action.triggered.connect(lambda: self.delete_group(item))
            # 如果点击的是关键字
            elif item.data(0, Qt.ItemDataRole.UserRole) == "keyword":
                edit_action = menu.addAction("修改关键字")
                edit_action.triggered.connect(lambda: self._edit_keyword(item.parent(), item))
                menu.addSeparator()
                delete_action = menu.addAction("删除关键字")
                delete_action.triggered.connect(lambda: self.delete_keyword(item.parent(), item))
        else:
            # 如果点击的是空白区域，添加新建顶级分组选项
            new_group_action = menu.addAction("新建分组")
            new_group_action.triggered.connect(self.add_group)
            
        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(position))
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """处理项目点击事件"""
        # 如果点击的是分组（包括顶级分组和子分组）
        if item.data(0, Qt.ItemDataRole.UserRole) == "group":
            self.current_group = item.text(0)
            # 清除最后选中的关键字分组记录
            self.last_selected_group = None
        # 如果点击的是关键字
        elif item.data(0, Qt.ItemDataRole.UserRole) == "keyword":
            # 记录该关键字所在的分组
            self.last_selected_group = item.parent().text(0)
            self.current_group = self.last_selected_group
            # 发送关键字和其匹配选项
            keyword = item.data(0, Qt.ItemDataRole.UserRole + 2)  # 获取实际关键字
            options = item.data(0, Qt.ItemDataRole.UserRole + 1) or {}
            self.keywordSelected.emit(keyword, options)
            
    def add_keyword(self, keyword: str, target_group: str = None, options=None, alias=""):
        """添加关键字到指定分组"""
        # 如果没有指定目标分组，使用当前分组
        if not target_group:
            target_group = self.current_group or "default"
            
        # 解析分组路径
        group_path = target_group.split("/")
        current_item = None
        
        # 遍历分组路径
        for i, group_name in enumerate(group_path):
            if i == 0:  # 顶级分组
                # 查找顶级分组
                found = False
                for j in range(self.tree.topLevelItemCount()):
                    item = self.tree.topLevelItem(j)
                    if item.text(0) == group_name:
                        current_item = item
                        found = True
                        break
                        
                # 如果顶级分组不存在，创建它
                if not found:
                    current_item = QTreeWidgetItem([group_name])
                    current_item.setData(0, Qt.ItemDataRole.UserRole, "group")
                    self.tree.addTopLevelItem(current_item)
            else:  # 子分组
                # 查找子分组
                found = False
                for j in range(current_item.childCount()):
                    child = current_item.child(j)
                    if child.data(0, Qt.ItemDataRole.UserRole) == "group" and child.text(0) == group_name:
                        current_item = child
                        found = True
                        break
                        
                # 如果子分组不存在，创建它
                if not found:
                    new_item = QTreeWidgetItem([group_name])
                    new_item.setData(0, Qt.ItemDataRole.UserRole, "group")
                    current_item.addChild(new_item)
                    current_item = new_item
                    
        # 检查关键字是否已存在
        for i in range(current_item.childCount()):
            child = current_item.child(i)
            if (child.data(0, Qt.ItemDataRole.UserRole) == "keyword" and 
                child.data(0, Qt.ItemDataRole.UserRole + 2) == keyword):
                QMessageBox.warning(self, "警告", "该关键字已存在")
                return
                
        # 创建关键字项
        keyword_item = QTreeWidgetItem([alias if alias else keyword])  # 显示文本
        keyword_item.setData(0, Qt.ItemDataRole.UserRole, "keyword")
        keyword_item.setData(0, Qt.ItemDataRole.UserRole + 1, options)  # 选项
        keyword_item.setData(0, Qt.ItemDataRole.UserRole + 2, keyword)  # 实际关键字
        keyword_item.setData(0, Qt.ItemDataRole.UserRole + 3, alias)  # 别名
        
        # 找到插入位置（在所有子分组之后）
        insert_pos = 0
        for i in range(current_item.childCount()):
            child = current_item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) == "group":
                insert_pos += 1
            else:
                break
                
        # 在正确的位置插入关键字
        current_item.insertChild(insert_pos, keyword_item)
        current_item.setExpanded(True)
        
        # 保存到文件
        self.save_to_file()

    def get_all_keywords(self) -> Dict[str, List[dict]]:
        """获取所有分组及其关键字"""
        result = {}
        
        def process_group(group_item: QTreeWidgetItem, path: str = ""):
            group_name = path + group_item.text(0)
            keywords = []
            
            # 处理所有子项
            for i in range(group_item.childCount()):
                child = group_item.child(i)
                # 如果是子分组
                if child.data(0, Qt.ItemDataRole.UserRole) == "group":
                    sub_results = process_group(child, group_name + "/")
                    result.update(sub_results)
                # 如果是关键字
                else:
                    keywords.append({
                        'text': child.data(0, Qt.ItemDataRole.UserRole + 2),  # 实际关键字
                        'alias': child.data(0, Qt.ItemDataRole.UserRole + 3) or "",  # 别名
                        'options': child.data(0, Qt.ItemDataRole.UserRole + 1) or {}
                    })
            
            result[group_name] = keywords
            return result
        
        # 处理所有顶级分组
        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)
            process_group(group_item)
        
        return result
        
    def load_keywords(self, keyword_groups: Dict[str, List[dict]]):
        """加载关键字分组"""
        self.tree.clear()
        self.last_selected_group = None  # 重置最后选中的分组
        
        def create_group_hierarchy(group_path: str) -> QTreeWidgetItem:
            parts = group_path.split("/")
            current_item = None
            
            # 查找或创建分组层级
            for i, part in enumerate(parts):
                if i == 0:
                    # 查找顶级分组
                    found = False
                    for j in range(self.tree.topLevelItemCount()):
                        if self.tree.topLevelItem(j).text(0) == part:
                            current_item = self.tree.topLevelItem(j)
                            found = True
                            break
                    if not found:
                        current_item = QTreeWidgetItem([part])
                        current_item.setData(0, Qt.ItemDataRole.UserRole, "group")
                        self.tree.addTopLevelItem(current_item)
                else:
                    # 查找或创建子分组
                    found = False
                    for j in range(current_item.childCount()):
                        child = current_item.child(j)
                        if child.data(0, Qt.ItemDataRole.UserRole) == "group" and child.text(0) == part:
                            current_item = child
                            found = True
                            break
                    if not found:
                        new_item = QTreeWidgetItem([part])
                        new_item.setData(0, Qt.ItemDataRole.UserRole, "group")
                        current_item.addChild(new_item)
                        current_item = new_item
            
            return current_item
        
        # 首先创建并填充default分组
        if "default" in keyword_groups:
            default_item = QTreeWidgetItem(["default"])
            default_item.setData(0, Qt.ItemDataRole.UserRole, "group")
            self.tree.addTopLevelItem(default_item)
            for keyword_data in keyword_groups["default"]:
                display_text = keyword_data.get('alias', '') or keyword_data['text']
                keyword_item = QTreeWidgetItem([display_text])
                keyword_item.setData(0, Qt.ItemDataRole.UserRole, "keyword")
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 1, keyword_data.get('options', {}))
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 2, keyword_data['text'])  # 实际关键字
                keyword_item.setData(0, Qt.ItemDataRole.UserRole + 3, keyword_data.get('alias', ''))  # 别名
                default_item.addChild(keyword_item)
            default_item.setExpanded(True)
        
        # 加载其他分组
        for group_path, keywords in keyword_groups.items():
            if group_path != "default":
                group_item = create_group_hierarchy(group_path)
                for keyword_data in keywords:
                    display_text = keyword_data.get('alias', '') or keyword_data['text']
                    keyword_item = QTreeWidgetItem([display_text])
                    keyword_item.setData(0, Qt.ItemDataRole.UserRole, "keyword")
                    keyword_item.setData(0, Qt.ItemDataRole.UserRole + 1, keyword_data.get('options', {}))
                    keyword_item.setData(0, Qt.ItemDataRole.UserRole + 2, keyword_data['text'])  # 实际关键字
                    keyword_item.setData(0, Qt.ItemDataRole.UserRole + 3, keyword_data.get('alias', ''))  # 别名
                    group_item.addChild(keyword_item)
                group_item.setExpanded(True)
        
        # 选中default分组
        for i in range(self.tree.topLevelItemCount()):
            if self.tree.topLevelItem(i).text(0) == "default":
                self.tree.setCurrentItem(self.tree.topLevelItem(i))
                self.current_group = "default"
                break

    def set_current_filter_text(self, text: str):
        """设置当前过滤框中的文本"""
        self.current_filter_text = text

    def set_current_filter_options(self, options: dict):
        """设置当前过滤选项"""
        self.current_filter_options = options

