import codecs
import os
from typing import Optional, List, Callable, Generator, Tuple

def detect_encoding(filepath: str, fallback_encodings: Optional[List[str]] = None) -> str:
    """
    检测文件编码。
    
    Args:
        filepath: 文件路径
        fallback_encodings: 备选编码列表，如果为None则使用默认列表
        
    Returns:
        str: 检测到的编码
    """
    if fallback_encodings is None:
        fallback_encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']
        
    def check_bom(raw: bytes) -> Optional[str]:
        """检查BOM标记"""
        boms = {
            (0xEF, 0xBB, 0xBF): 'utf-8-sig',
            (0xFE, 0xFF): 'utf-16be',
            (0xFF, 0xFE): 'utf-16le',
            (0x00, 0x00, 0xFE, 0xFF): 'utf-32be',
            (0xFF, 0xFE, 0x00, 0x00): 'utf-32le',
        }
        for bom, encoding in boms.items():
            if raw.startswith(bytes(bom)):
                return encoding
        return None
        
    def is_valid_utf8(raw: bytes) -> bool:
        """快速检查是否是有效的UTF-8编码"""
        try:
            raw.decode('utf-8')
            return True
        except UnicodeDecodeError:
            return False
            
    # 读取文件头部来检测编码
    with open(filepath, 'rb') as f:
        raw = f.read(4096)  # 读取前4KB
        if not raw:
            return 'utf-8'  # 空文件默认使用UTF-8
            
        # 检查BOM
        bom_encoding = check_bom(raw)
        if bom_encoding:
            return bom_encoding
            
        # 检查是否是UTF-8
        if is_valid_utf8(raw):
            return 'utf-8'
            
        # 尝试其他编码
        for encoding in fallback_encodings:
            try:
                raw.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
                
        # 如果都失败，返回第一个备选编码
        return fallback_encodings[0]

def read_file_with_encoding(
    filepath: str,
    fallback_encodings: Optional[List[str]] = None,
    chunk_callback: Optional[Callable[[str], None]] = None,
    chunk_size_mb: int = 8
) -> str:
    """
    使用分块加载方式读取文件，支持多种编码。
    
    Args:
        filepath: 文件路径
        fallback_encodings: 备选编码列表，如果为None则使用默认列表
        chunk_callback: 分块读取回调函数，用于实时处理读取的内容
        chunk_size_mb: 分块大小（MB），默认8MB
        
    Returns:
        str: 文件内容
        
    Raises:
        UnicodeDecodeError: 当所有编码方式都无法正确解码文件时抛出
        FileNotFoundError: 当文件不存在时抛出
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在：{filepath}")
        
    # 检测文件编码
    encoding = detect_encoding(filepath, fallback_encodings)
    chunk_size = chunk_size_mb * 1024 * 1024  # 转换为字节
    
    # 分块读取文件
    result = []
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                    
                if chunk_callback:
                    chunk_callback(chunk)
                result.append(chunk)
                
        return ''.join(result)
        
    except UnicodeDecodeError:
        # 如果解码失败，尝试使用replace模式
        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
            if chunk_callback:
                chunk_callback(content)
            return content
            
    except Exception as e:
        raise Exception(f"读取文件时发生错误：{str(e)}")

def read_file_chunks(
    filepath: str,
    chunk_size_mb: int = 8,
    fallback_encodings: Optional[List[str]] = None
) -> Generator[Tuple[str, int], None, None]:
    """
    生成器函数，逐块读取文件内容。
    
    Args:
        filepath: 文件路径
        chunk_size_mb: 分块大小（MB），默认8MB
        fallback_encodings: 备选编码列表
        
    Yields:
        Tuple[str, int]: (块内容, 块序号)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在：{filepath}")
        
    # 检测文件编码
    encoding = detect_encoding(filepath, fallback_encodings)
    chunk_size = chunk_size_mb * 1024 * 1024  # 转换为字节
    
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            chunk_index = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk, chunk_index
                chunk_index += 1
                
    except UnicodeDecodeError:
        # 如果解码失败，尝试使用replace模式
        with open(filepath, 'r', encoding=encoding, errors='replace') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk, 0  # 在replace模式下，只返回一个块