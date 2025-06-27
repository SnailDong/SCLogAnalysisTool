from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import re
from typing import Set

# 从theme.py导入主题颜色
from src.resources.theme import THEME

class LogHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keywords = set()
        self.case_sensitive = False
        self.whole_word = False
        self.use_regex = False
        
        # 创建高亮格式
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor(THEME['keyword_text']))  # 绿色关键字
        # 设置高优先级，确保关键字高亮不会被其他高亮覆盖
        self.keyword_format.setProperty(QTextCharFormat.Property.UserProperty, 2)  # 增加优先级
        # 设置不受选择影响
        self.keyword_format.setProperty(QTextCharFormat.Property.FullWidthSelection, False)
        # 强制使用前景色
        self.keyword_format.setFontWeight(QFont.Weight.Bold)  # 加粗

    def set_keywords(self, keywords: set, options: dict = None):
        """设置要高亮的关键字和选项"""
        self.keywords = keywords
        if options:
            self.case_sensitive = options.get("case_sensitive", False)
            self.whole_word = options.get("whole_word", False)
            self.use_regex = options.get("use_regex", False)
        self.rehighlight()

    def highlightBlock(self, text: str):
        """高亮文本块中的关键字"""
        if not text or not self.keywords:
            return
            
        for keyword in self.keywords:
            if not keyword:
                continue
                
            if self.use_regex:
                try:
                    pattern = re.compile(keyword, flags=0 if self.case_sensitive else re.IGNORECASE)
                    for match in pattern.finditer(text):
                        self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)
                except re.error:
                    continue
            else:
                search_text = text if self.case_sensitive else text.lower()
                search_keyword = keyword if self.case_sensitive else keyword.lower()
                
                if self.whole_word:
                    pattern = r'\b' + re.escape(search_keyword) + r'\b'
                    for match in re.finditer(pattern, search_text):
                        self.setFormat(match.start(), len(keyword), self.keyword_format)
                else:
                    pos = 0
                    while True:
                        pos = search_text.find(search_keyword, pos)
                        if pos == -1:
                            break
                        self.setFormat(pos, len(keyword), self.keyword_format)
                        pos += 1 