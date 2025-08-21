import chardet
from typing import Optional, List

def read_file_with_encoding(filepath: str, fallback_encodings: Optional[List[str]] = None) -> str:
    """
    智能读取文件内容，自动检测和尝试多种编码格式。
    
    Args:
        filepath: 文件路径
        fallback_encodings: 备选编码列表，如果为None则使用默认列表
        
    Returns:
        str: 文件内容
        
    Raises:
        UnicodeDecodeError: 当所有编码方式都无法正确解码文件时抛出
        FileNotFoundError: 当文件不存在时抛出
    """
    if fallback_encodings is None:
        fallback_encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']
    
    # 读取文件的一小部分来检测编码
    try:
        with open(filepath, 'rb') as f:
            raw = f.read(4096)  # 读取前4KB来检测编码
            if not raw:  # 空文件
                return ""
            result = chardet.detect(raw)
            detected_encoding = result['encoding']
    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在：{filepath}")
    
    # 首先尝试使用检测到的编码
    if detected_encoding:
        try:
            with open(filepath, 'r', encoding=detected_encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            pass  # 如果检测的编码不正确，继续尝试备选编码
    
    # 尝试备选编码
    for encoding in fallback_encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，抛出异常
    raise UnicodeDecodeError(
        f"无法使用以下编码格式读取文件：{[detected_encoding] + fallback_encodings if detected_encoding else fallback_encodings}"
    )
