import json
import os
from typing import List, Dict, Set, Union
from PyQt6.QtCore import QObject, pyqtSignal
from functools import wraps

def singleton(cls):
    """单例模式装饰器"""
    _instance = {}
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]
    
    return get_instance

class ConfigManager(QObject):
    _instance = None
    recentFilesChanged = pyqtSignal()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # Initialize QObject in __new__ to ensure it's only done once
            super(ConfigManager, cls._instance).__init__()
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # 获取应用程序根目录
            app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.config_dir = os.path.join(app_root, "caches")
            self.config_file = os.path.join(self.config_dir, "config.json")
            
            # 检查是否存在旧的配置文件
            old_config_dir = os.path.expanduser("~/.sc_log_tool")
            old_config_file = os.path.join(old_config_dir, "config.json")
            
            # 确保新的配置目录存在
            self._ensure_config_dir()
            
            # 如果存在旧的配置文件，迁移到新位置
            if os.path.exists(old_config_file) and not os.path.exists(self.config_file):
                try:
                    import shutil
                    shutil.copy2(old_config_file, self.config_file)
                    # 迁移成功后删除旧的配置文件和目录
                    os.remove(old_config_file)
                    if not os.listdir(old_config_dir):  # 如果目录为空
                        os.rmdir(old_config_dir)
                except Exception as e:
                    print(f"迁移配置文件时出错: {e}")
            
            self._initialized = True
        
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
    def save_state(self, opened_files: List[str], current_tab: int, keyword_groups: Dict[str, List[Union[str, Dict]]], recent_files: List[str] = None):
        """保存程序状态"""
        # 过滤掉不存在的文件
        opened_files = [f for f in opened_files if os.path.exists(f)]
        if recent_files is not None:
            recent_files = [f for f in recent_files if os.path.exists(f)]
        
        # 转换旧格式的关键字为新格式
        converted_groups = {}
        for group_name, keywords in keyword_groups.items():
            converted_keywords = []
            for keyword in keywords:
                if isinstance(keyword, str):
                    # 旧格式：直接是字符串
                    converted_keywords.append({
                        'text': keyword,
                        'options': {}
                    })
                else:
                    # 新格式：已经是字典
                    converted_keywords.append(keyword)
            converted_groups[group_name] = converted_keywords
        
        state = {
            "opened_files": opened_files,
            "current_tab": current_tab,
            "keyword_groups": converted_groups,
            "recent_files": recent_files if recent_files is not None else []
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            
    def load_state(self) -> Dict:
        """加载程序状态"""
        default_state = {
            "opened_files": [],
            "current_tab": 0,
            "keyword_groups": {"default": []},
            "recent_files": []
        }
        
        if not os.path.exists(self.config_file):
            return default_state
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # 确保包含最近文件字段
                if "recent_files" not in state:
                    state["recent_files"] = []
                # 确保包含关键字分组字段
                if "keyword_groups" not in state:
                    state["keyword_groups"] = {"default": []}
                    
                # 转换旧格式的关键字为新格式
                converted_groups = {}
                for group_name, keywords in state["keyword_groups"].items():
                    converted_keywords = []
                    for keyword in keywords:
                        if isinstance(keyword, str):
                            # 旧格式：直接是字符串
                            converted_keywords.append({
                                'text': keyword,
                                'options': {}
                            })
                        else:
                            # 新格式：已经是字典
                            converted_keywords.append(keyword)
                    converted_groups[group_name] = converted_keywords
                state["keyword_groups"] = converted_groups
                
                return state
        except Exception:
            return default_state
            
    def update_recent_files(self, filepath: str, is_close: bool = False) -> List[str]:
        """更新最近文件列表
        
        Args:
            filepath: 文件路径
            is_close: 是否是关闭文件操作
        """
        print(f"update_recent_files called: filepath={filepath}, is_close={is_close}")
        state = self.load_state()
        recent_files = state.get("recent_files", [])
        opened_files = state.get("opened_files", [])
        
        # 如果是关闭文件操作
        if is_close:
            # 从已打开文件列表中移除
            if filepath in opened_files:
                opened_files.remove(filepath)
            # 将关闭的文件添加到最近文件列表的开头
            if filepath in recent_files:
                recent_files.remove(filepath)
            recent_files.insert(0, filepath)
        else:
            # 如果是打开文件操作
            # 如果文件已经在最近列表中，先移除它
            if filepath in recent_files:
                recent_files.remove(filepath)
            # 如果文件不在已打开列表中，将其添加到最近文件列表
            if filepath not in opened_files:
                recent_files.insert(0, filepath)
            # 确保文件在已打开列表中
            if filepath not in opened_files:
                opened_files.append(filepath)
        
        # 只保留除当前打开文件外的八条记录
        recent_files = [f for f in recent_files if f not in opened_files][:8]
        
        print(f"Recent files before save: {recent_files}")
        
        # 更新状态
        state["recent_files"] = recent_files
        state["opened_files"] = opened_files
        self.save_state(
            opened_files,
            state["current_tab"],
            state["keyword_groups"],
            recent_files
        )
        
        print("Emitting recentFilesChanged signal")
        # 发送信号
        self.recentFilesChanged.emit()
        
        return recent_files
        
    def remove_opened_file(self, filepath: str):
        """从已打开文件列表中移除文件"""
        state = self.load_state()
        opened_files = state.get("opened_files", [])
        
        if filepath in opened_files:
            opened_files.remove(filepath)
            
        self.save_state(
            opened_files,
            state["current_tab"],
            state["keyword_groups"],
            state.get("recent_files", [])
        )
        
    def remove_recent_file(self, filepath: str):
        """从最近文件列表中移除文件
        
        Args:
            filepath: 要移除的文件路径
        """
        state = self.load_state()
        recent_files = state.get("recent_files", [])
        
        if filepath in recent_files:
            recent_files.remove(filepath)
            
            # 更新状态
            self.save_state(
                state.get("opened_files", []),
                state.get("current_tab", 0),
                state.get("keyword_groups", {"default": []}),
                recent_files
            )
            print(f"recentFilesChanged: {recent_files}")
            # 发送信号
            self.recentFilesChanged.emit()
        return recent_files 