import logging
import os
from datetime import datetime

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        # 创建logs目录（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 创建文件处理器
        log_file = os.path.join('logs', f'ui_events_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 配置根日志记录器
        self.logger = logging.getLogger('SCLogAnalysisTool')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    @staticmethod
    def get_logger():
        return Logger()._instance.logger

def log_ui_event(event_type: str, widget_name: str, additional_info: str = ""):
    """记录UI事件的辅助函数
    
    Args:
        event_type: 事件类型（如 'click', 'focus', 'change' 等）
        widget_name: 控件名称
        additional_info: 额外信息
    """
    message = f"UI Event - {event_type} - {widget_name}"
    if additional_info:
        message += f" - {additional_info}"
    Logger.get_logger().info(message) 