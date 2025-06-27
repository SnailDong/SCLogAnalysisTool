from typing import Dict, List, Optional
import json
import os
from datetime import datetime

class MarkManager:
    def __init__(self):
        self.marks: Dict[str, List[Dict]] = {}  # filepath -> marks list
        
    def add_mark(self, filepath: str, line_number: int, content: str, note: str = "") -> bool:
        """添加标记"""
        if filepath not in self.marks:
            self.marks[filepath] = []
            
        # 检查是否已存在相同行的标记
        for mark in self.marks[filepath]:
            if mark["line_number"] == line_number:
                return False
                
        mark = {
            "line_number": line_number,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "note": note
        }
        self.marks[filepath].append(mark)
        return True
        
    def remove_mark(self, filepath: str, line_number: int) -> bool:
        """删除标记"""
        if filepath not in self.marks:
            return False
            
        for i, mark in enumerate(self.marks[filepath]):
            if mark["line_number"] == line_number:
                self.marks[filepath].pop(i)
                return True
        return False
        
    def get_marks(self, filepath: str) -> List[Dict]:
        """获取文件的所有标记"""
        return self.marks.get(filepath, [])
        
    def is_marked(self, filepath: str, line_number: int) -> bool:
        """检查行是否已标记"""
        if filepath not in self.marks:
            return False
            
        for mark in self.marks[filepath]:
            if mark["line_number"] == line_number:
                return True
        return False
        
    def save_marks(self, filepath: str):
        """保存标记到文件"""
        marks_file = os.path.join(os.path.dirname(filepath), ".marks.json")
        with open(marks_file, 'w', encoding='utf-8') as f:
            json.dump(self.marks, f, ensure_ascii=False, indent=2)
            
    def load_marks(self, filepath: str):
        """从文件加载标记"""
        marks_file = os.path.join(os.path.dirname(filepath), ".marks.json")
        if os.path.exists(marks_file):
            with open(marks_file, 'r', encoding='utf-8') as f:
                self.marks = json.load(f) 