from typing import List, Dict, Set, Union, Optional, Tuple
import re
from dataclasses import dataclass
from enum import Enum

class TokenType(Enum):
    KEYWORD = "KEYWORD"
    AND = "AND"
    OR = "OR"
    LEFT_PAREN = "LEFT_PAREN"
    RIGHT_PAREN = "RIGHT_PAREN"

@dataclass
class Token:
    type: TokenType
    value: str

@dataclass
class FilterOptions:
    case_sensitive: bool = False
    whole_word: bool = False
    use_regex: bool = False

class ExpressionNode:
    pass

class KeywordNode(ExpressionNode):
    def __init__(self, keyword: str):
        self.keyword = keyword

    def evaluate(self, line: str) -> bool:
        return self.keyword in line

class AndNode(ExpressionNode):
    def __init__(self, left: ExpressionNode, right: ExpressionNode):
        self.left = left
        self.right = right

    def evaluate(self, line: str) -> bool:
        return self.left.evaluate(line) and self.right.evaluate(line)

class OrNode(ExpressionNode):
    def __init__(self, left: ExpressionNode, right: ExpressionNode):
        self.left = left
        self.right = right

    def evaluate(self, line: str) -> bool:
        return self.left.evaluate(line) or self.right.evaluate(line)

class ParserError(Exception):
    pass

class ExpressionParser:
    def __init__(self):
        self.tokens: List[Token] = []
        self.current = 0
        self.error_message = ""

    def parse(self, expression: str) -> Union[ExpressionNode, None]:
        try:
            self.tokens = self._tokenize(expression)
            self.current = 0
            return self._parse_expression()
        except ParserError as e:
            self.error_message = str(e)
            return None

    def _tokenize(self, expression: str) -> List[Token]:
        tokens = []
        i = 0
        while i < len(expression):
            char = expression[i]
            
            # 跳过空白字符
            if char.isspace():
                i += 1
                continue
                
            # 处理关键字
            if char == '"':
                keyword, new_i = self._extract_keyword(expression, i)
                if keyword is None:
                    raise ParserError("关键字格式错误：缺少闭合的双引号")
                tokens.append(Token(TokenType.KEYWORD, keyword))
                i = new_i
                continue
                
            # 处理操作符和括号
            if char == '(':
                tokens.append(Token(TokenType.LEFT_PAREN, char))
            elif char == ')':
                tokens.append(Token(TokenType.RIGHT_PAREN, char))
            elif expression[i:i+3].lower() == 'and':
                tokens.append(Token(TokenType.AND, 'and'))
                i += 2
            elif expression[i:i+2].lower() == 'or':
                tokens.append(Token(TokenType.OR, 'or'))
                i += 1
            else:
                raise ParserError(f"非法字符: {char}")
            i += 1
            
        return tokens

    def _extract_keyword(self, expression: str, start: int) -> tuple[Union[str, None], int]:
        i = start + 1
        while i < len(expression):
            if expression[i] == '"':
                # 返回关键字内容和新的索引位置
                return expression[start+1:i], i + 1
            i += 1
        return None, start

    def _parse_expression(self) -> ExpressionNode:
        return self._parse_or()

    def _parse_or(self) -> ExpressionNode:
        expr = self._parse_and()
        
        while self.current < len(self.tokens) and self.tokens[self.current].type == TokenType.OR:
            self.current += 1
            right = self._parse_and()
            expr = OrNode(expr, right)
            
        return expr

    def _parse_and(self) -> ExpressionNode:
        expr = self._parse_primary()
        
        while self.current < len(self.tokens) and self.tokens[self.current].type == TokenType.AND:
            self.current += 1
            right = self._parse_primary()
            expr = AndNode(expr, right)
            
        return expr

    def _parse_primary(self) -> ExpressionNode:
        token = self.tokens[self.current]
        
        if token.type == TokenType.LEFT_PAREN:
            self.current += 1
            expr = self._parse_expression()
            
            if self.current >= len(self.tokens) or self.tokens[self.current].type != TokenType.RIGHT_PAREN:
                raise ParserError("括号不匹配：缺少右括号")
                
            self.current += 1
            return expr
            
        elif token.type == TokenType.KEYWORD:
            self.current += 1
            return KeywordNode(token.value)
            
        raise ParserError(f"非法表达式：{token.value}")

    def validate_expression(self, expression: str) -> Dict[str, Union[bool, str]]:
        """验证表达式的合法性"""
        try:
            node = self.parse(expression)
            if node is None:
                return {
                    "valid": False,
                    "message": self.error_message
                }
            return {
                "valid": True,
                "message": "表达式合法"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": str(e)
            } 