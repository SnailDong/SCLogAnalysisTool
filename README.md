# SC Log Analysis Tool

一个功能强大的日志分析工具，专为 Mac 用户设计，提供类似 Notepad++ 的文本查看和过滤功能。

## 主要功能

- 多窗口支持：同时打开多个日志文件
- 关键字搜索：支持普通文本和正则表达式搜索
- 搜索导航：支持在搜索结果间上下跳转
- 关键字管理：保存和管理常用搜索关键字
- 日志过滤：支持根据关键字过滤日志内容
- 实时更新：支持实时监控日志文件变化

## 安装要求

- Python 3.8+
- PyQt6

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/SCLogAnalysisTool.git
cd SCLogAnalysisTool
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行程序：
```bash
python main.py
```

## 使用说明

1. 文件操作
   - 使用 File -> Open 打开日志文件
   - 支持拖拽文件到窗口打开
   - 可以同时打开多个标签页查看不同文件

2. 搜索功能
   - 使用 Ctrl+F (Command+F) 打开搜索框
   - 支持普通文本和正则表达式搜索
   - 使用 F3/Shift+F3 在搜索结果间导航

3. 关键字管理
   - 可以保存常用搜索关键字
   - 支持关键字分类管理
   - 快速应用已保存的关键字

4. 日志过滤
   - 支持实时过滤显示匹配的行
   - 可以同时应用多个过滤条件
   - 支持过滤条件的与/或逻辑组合

## 快捷键

- Ctrl+O (Command+O): 打开文件
- Ctrl+F (Command+F): 搜索
- F3: 查找下一个
- Shift+F3: 查找上一个
- Ctrl+W (Command+W): 关闭当前标签页 
- Ctrl+T (Command+T): 保存当前关键字到选中的分组