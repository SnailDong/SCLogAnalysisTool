from typing import List, Dict, Set, Tuple
from src.utils.expression_parser import ExpressionParser, FilterOptions
import re

class FilterEngine:
    def __init__(self):
        self.parser = ExpressionParser()
        self.current_expression: Optional[str] = None
        self.keywords: Set[str] = set()
        self.case_sensitive = False
        self.whole_word = False
        self.use_regex = False
        self.cached_matches = []  # 缓存匹配结果
        self.cached_text = None   # 缓存搜索的文本
        self.cached_options = {}  # 缓存搜索选项

    def set_filter_expression(self, expression: str, options: dict = None) -> dict:
        """设置过滤表达式和选项"""
        if options is None:
            options = {}
            
        # 清除缓存，因为表达式或选项改变了
        self.cached_matches = []
        self.cached_text = None
        self.cached_options = {}
            
        self.case_sensitive = options.get("case_sensitive", False)
        self.whole_word = options.get("whole_word", False)
        self.use_regex = options.get("use_regex", False)
        
        try:
            if self.use_regex:
                # 在正则表达式模式下，尝试编译表达式
                try:
                    # 先尝试直接编译
                    re.compile(expression)
                    self.current_expression = expression
                except re.error:
                    # 如果失败，尝试转义后再编译
                    escaped_expr = re.escape(expression)
                    re.compile(escaped_expr)
                    self.current_expression = escaped_expr
                
                self.keywords = {self.current_expression}
            else:
                # 非正则表达式模式下，直接使用输入的内容
                self.current_expression = expression
                self.keywords = {expression} if expression else set()
                
            return {"valid": True, "message": ""}
        except Exception as e:
            return {"valid": False, "message": str(e)}

    def _match_keyword(self, text: str, keyword: str) -> bool:
        """根据选项匹配关键字"""
        if not keyword:
            return False
            
        if self.use_regex:
            try:
                pattern = re.compile(keyword, flags=0 if self.case_sensitive else re.IGNORECASE)
                return bool(pattern.search(text))
            except re.error:
                # 如果正则表达式无效，将其作为普通文本处理
                if not self.case_sensitive:
                    text = text.lower()
                    keyword = keyword.lower()
                return keyword in text
        else:
            # 非正则表达式模式下的简单文本匹配
            if not self.case_sensitive:
                text = text.lower()
                keyword = keyword.lower()
                
            if self.whole_word:
                # 使用单词边界匹配
                pattern = r'\b' + re.escape(keyword) + r'\b'
                return bool(re.search(pattern, text))
            else:
                return keyword in text

    def filter_text(self, text: str, expression: str = None) -> Tuple[List[str], List[int]]:
        """根据表达式过滤文本"""
        if expression is not None:
            self.set_filter_expression(expression)
            
        if not self.current_expression:
            return [], []

        # 检查是否需要重新搜索
        current_options = {
            "case_sensitive": self.case_sensitive,
            "whole_word": self.whole_word,
            "use_regex": self.use_regex
        }
        
        if (text != self.cached_text or 
            current_options != self.cached_options):
            # 需要重新搜索并缓存结果
            self.cached_matches = self.find_keyword_matches(text)
            self.cached_text = text
            self.cached_options = current_options.copy()
            
        print(f"cached_matches: {self.cached_matches}")
        # 使用缓存的匹配结果
        lines = text.splitlines()
        filtered_lines = []
        line_mapping = []
        
        # 根据缓存的匹配结果构建过滤后的行列表
        matched_lines = set()
        for _, _, _, line_number, _ in self.cached_matches:
            if line_number not in matched_lines:
                matched_lines.add(line_number)
                filtered_lines.append(lines[line_number])
                line_mapping.append(line_number)
                
        return filtered_lines, line_mapping

    def get_keywords(self) -> Set[str]:
        """获取当前的关键字集合"""
        return self.keywords

    def find_keyword_matches(self, text: str) -> List[Tuple[int, int, str, int, int]]:
        """在文本中查找所有关键字的匹配位置
        返回一个列表，每个元素是一个元组 (start_pos, end_pos, matched_keyword, line_number, index)
        其中start_pos和end_pos是在该行中的位置
        按照index排序
        """
        matches = []
        index = 0  # 用于记录匹配项的顺序
        
        # 按行处理文本
        lines = text.splitlines(keepends=True)  # keepends=True 保留换行符
        
        for line_number, line in enumerate(lines):
            for keyword in self.keywords:
                if not keyword:
                    continue
                    
                if self.use_regex:
                    try:
                        pattern = re.compile(keyword, flags=0 if self.case_sensitive else re.IGNORECASE)
                        for match in pattern.finditer(line):
                            # 使用行内的匹配位置
                            matches.append((match.start(), match.end(), match.group(), line_number, index))
                            index += 1
                    except re.error:
                        continue
                else:
                    search_line = line if self.case_sensitive else line.lower()
                    search_keyword = keyword if self.case_sensitive else keyword.lower()
                    
                    if self.whole_word:
                        pattern = r'\b' + re.escape(search_keyword) + r'\b'
                        for match in re.finditer(pattern, search_line):
                            # 使用行内的匹配位置
                            matches.append((match.start(), match.end(), keyword, line_number, index))
                            index += 1
                    else:
                        pos = 0
                        while True:
                            pos = search_line.find(search_keyword, pos)
                            if pos == -1:
                                break
                            # 使用行内的匹配位置
                            matches.append((pos, pos + len(keyword), keyword, line_number, index))
                            index += 1
                            pos += 1
                        
        # 按照索引排序
        self.set_total_count(index)
        matches.sort(key=lambda x: x[4])
        return matches

    def set_total_count(self, count: int) -> int:
        self.total_count = count

    def get_keyword_total_count(self) -> int:
        return self.total_count

    def get_keyword_matches(self, text: str) -> List[Tuple[int, int, str, int, int]]:
        """获取文本中所有关键字的匹配位置
        返回一个列表，每个元素是一个元组 (start_pos, end_pos, matched_keyword, line_number, index)
        """ 
        # 从缓存结果中提取需要的信息
        return [(start, end, keyword, line_number, index) for start, end, keyword, line_number, index in self.cached_matches]

    def clear_filter(self):
        """清除当前过滤器"""
        self.current_expression = None
        self.keywords.clear()

    def _find_matches(self, text: str) -> List[Tuple[int, int]]:
        """在文本中查找所有匹配的位置
        
        Args:
            text: 要搜索的文本
            
        Returns:
            List[Tuple[int, int]]: 匹配位置的列表，每个元素是(开始位置, 结束位置)
        """
        matches = []
        for keyword in self.keywords:
            if not keyword:
                continue
                
            # 根据大小写敏感设置进行匹配
            if self.case_sensitive:
                pattern = re.compile(re.escape(keyword))
            else:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            
            # 查找所有匹配
            for match in pattern.finditer(text):
                matches.append((match.start(), match.end()))
        
        # 按位置排序
        return sorted(matches) 