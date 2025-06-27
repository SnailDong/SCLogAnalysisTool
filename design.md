帮我设计一个日志分析工具，创建代码时请以组件化模块化的思想去创建，每个模块应改命名清晰、每个组件应该使用单独的类文件保存代码。
主要功能如下：
暂时无法在飞书文档外展示此内容
主要页面如下
当没有任何文件被打开时：
[图片1]

当有文件被打开时显示如下
[图片2]
其中工具栏显示开始按钮SCTool，每打开一个文件显示一个标签页
页面内容分为两部分，上方显示一个检索面板，是一个过滤关键字输入框和选项的面板
下方是完整日志视图面板，显示打开的文件日志
点击SCTool时，会展开菜单栏，菜单栏如下图，光标移动到打开最近的文件时会最多展示5条最近打开的文件的完整路径
[图片3]
当选中关键字视图和过滤视图时主界面如下，主界面被分割为三个区域
左上是日志显示面板
右侧展示一个关键字列表面板
左下展示一个筛选视图面板
[图片4]
关键字列表面板可以新建分组、新建关键字用来保存关键字，点击时可以将该关键字的内容和配置设置到检索面板的输入框和选项
筛选视图面板可以切换为过滤的日志面板、标记的日志面板等


---

实现方案与架构设计

一、整体架构设计

1. 组件化/模块化思想
- 每个功能模块单独成类，文件独立，便于维护和扩展。
- 采用 MVC（Model-View-Controller）或 MVVM（Model-View-ViewModel）架构，分离数据、界面和逻辑。
- 主要模块：文件操作、日志查看、过滤功能、关键词管理、界面功能、其他功能。

2. 主要模块划分
- 文件操作模块：负责文件的打开、关闭、保存、导出等。
- 日志显示模块：负责原始日志、过滤后日志的显示与高亮。
- 过滤模块：负责关键词、正则、时间、级别等多种过滤方式。
- 关键词管理模块：分组、增删改查、配置保存。
- 界面管理模块：标签页、分割视图、主题、快捷键等。
- 配置与状态模块：全局配置、状态栏、错误处理等。

二、界面设计思路

3. 主窗口（MainWindow）
- 菜单栏（SCTool 按钮，弹出菜单）
- 标签页（QTabWidget，每个打开的日志文件一个标签）
- 分割视图（QSplitter，上下/左右分割）
- 状态栏（显示状态、提示信息）

4. 日志视图区
- 上方：检索面板（QWidget + QLineEdit + 过滤选项控件）
- 下方：日志内容区（QTextEdit/QPlainTextEdit，支持高亮、跳转、搜索）

5. 侧边栏与分区
- 右侧：关键词列表面板（QTreeView/QListWidget，支持分组、增删改查）
- 左下：筛选视图（QStackedWidget，切换过滤日志、标记日志等）

6. 弹出菜单
- 文件操作（打开、最近文件、导出等）
- 视图切换（关键词视图、过滤视图）

三、功能实现思路

7. 文件操作
- 使用 QFileDialog 实现文件选择、最近文件列表（本地保存最近5条路径）。
- 支持多标签页，每个文件独立视图。

8. 日志查看与高亮
- 日志内容用 QPlainTextEdit/QTextEdit 展示，支持大文件分段加载。
- 关键词/正则/级别等高亮，使用 QSyntaxHighlighter 实现。

9. 过滤功能
- 检索面板输入关键词/正则/时间/级别，实时过滤日志内容。
- 支持多条件组合过滤，过滤结果可导出。

10. 关键词管理
- 关键词分组管理，持久化保存（如 JSON 文件）。
- 支持新建、编辑、删除分组和关键词。
- 点击关键词可快速应用到检索面板。

11. 界面与交互
- QTabWidget 管理多文件标签页。
- QSplitter 实现分割视图，上下/左右可拖动调整。
- 主题切换（浅色/深色），快捷键支持（如 Ctrl+F 搜索）。

12. 其他功能
- 日志解析（可扩展为多种格式解析）。
- 错误处理（弹窗提示、状态栏显示）。
- 配置管理（如主题、最近文件、关键词分组等）。

四、类与文件结构建议

/core
    file_manager.py         # 文件操作相关
    log_parser.py           # 日志解析与处理
    filter_engine.py        # 过滤逻辑
    keyword_manager.py      # 关键词分组与管理
    config_manager.py       # 配置管理
/ui
    main_window.py          # 主窗口
    log_viewer.py           # 日志显示组件
    search_panel.py         # 检索面板
    keyword_panel.py        # 关键词列表面板
    workspace_panel.py      # 工作区视图面板
    menu.py                 # 菜单栏
    status_bar.py           # 状态栏
/resources
    themes/                 # 主题样式
    icons/                  # 图标资源
    config/                 # 默认配置
main.py                    # 程序入口

五、扩展性与维护性

- 每个功能独立成类，便于后续功能扩展和维护。
- 采用信号槽机制（Qt），实现模块间解耦。
- 关键配置、关键词、最近文件等持久化存储，方便用户体验。
详细类图（核心模块）
classDiagram
    class MainWindow {
        +initUI()
        +openFile()
        +closeTab()
        +switchTheme()
    }
    class FileManager {
        +openFile(path)
        +getRecentFiles()
        +saveConfig()
    }
    class LogViewer {
        +setLogContent()
        +highlightKeywords()
        +scrollToLine()
    }
    class SearchPanel {
        +setFilter()
        +getFilterOptions()
        +onKeywordSelected()
    }
    class FilterEngine {
        +applyFilters()
        +setKeywordFilter()
        +setRegexFilter()
        +setTimeFilter()
        +setLevelFilter()
    }
    class KeywordManager {
        +addGroup()
        +removeGroup()
        +addKeyword()
        +removeKeyword()
        +saveKeywords()
    }
    class WorkspacePanel {
        +switchView()
        +showFilteredLogs()
        +showMarkedLogs()
    }
    class ConfigManager {
        +loadConfig()
        +saveConfig()
    }

    MainWindow --> FileManager
    MainWindow --> LogViewer
    MainWindow --> SearchPanel
    MainWindow --> WorkspacePanel
    SearchPanel --> FilterEngine
    SearchPanel --> KeywordManager
    LogViewer --> FilterEngine
    MainWindow --> ConfigManager
打开日志文件流程
flowchart TD
    A[用户点击"打开文件"] --> B[弹出文件选择对话框]
    B --> C[选择日志文件]
    C --> D[FileManager 读取文件内容]
    D --> E[MainWindow 新建标签页]
    E --> F[LogViewer 显示日志内容]
    F --> G[更新最近文件列表]
日志过滤流程
flowchart TD
    A[用户输入过滤条件] --> B[SearchPanel 收集过滤条件]
    B --> C[FilterEngine 应用过滤逻辑]
    C --> D1[LogViewer 显示完整日志，高亮关键字]
    C --> D2[WorkspacePanel 显示过滤结果，高亮关键字]
关键词管理流程
flowchart TD
    A[用户新建/编辑/删除分组或关键词] --> B[KeywordManager 更新数据]
    B --> C[保存到本地配置]
    B --> D[SearchPanel/LogViewer 响应变更]
日志文件自动恢复与最近文件管理实现细节
已打开日志自动恢复
- 记录机制
  - 每次关闭程序时，将当前所有已打开日志文件的完整路径（按标签页顺序）保存到本地配置文件（如 config/opened_files.json 或主配置文件）。
- 恢复机制
  - 程序启动时，自动读取该配置，依次尝试打开这些日志文件，并为每个文件新建一个标签页。
  - 若某个文件不存在或无法打开，自动跳过并提示用户。
# 伪代码示例
# 关闭程序时
ConfigManager.save_opened_files([tab.file_path for tab in all_open_tabs])

# 启动程序时
for path in ConfigManager.load_opened_files():
    if os.path.exists(path):
        FileManager.open_file(path)
        MainWindow.add_tab(path)
最近打开文件管理（LRU）
- 记录机制
  - 每次成功打开一个日志文件时，将其路径插入最近文件列表的最前面。
  - 如果该文件已在列表中，先移除再插入最前。
  - 若该文件已在"已打开文件"列表中，则不加入最近文件列表。
  - 保持最近文件列表最大长度为5（超出则移除最旧的）。
- 展示机制
  - 主界面"最近打开的文件"区域和菜单栏"最近打开的文件"子菜单，均展示这5条记录，显示完整路径。
  - 点击可直接打开对应日志文件。
# 伪代码示例
def update_recent_files(file_path):
    if file_path in opened_files:
        return
    if file_path in recent_files:
        recent_files.remove(file_path)
    recent_files.insert(0, file_path)
    if len(recent_files) > 5:
        recent_files.pop()
    ConfigManager.save_recent_files(recent_files)
配置管理建议
- ConfigManager 负责所有本地配置的读写，包括：
- 已打开文件列表（用于自动恢复标签页）
- 最近打开文件列表（用于主界面和菜单栏展示）
- 配置建议采用 JSON 格式，便于扩展和调试。
配置文件结构示例
{
  "opened_files": [
    "/path/to/log1.log",
    "/path/to/log2.txt"
  ],
  "recent_files": [
    "/path/to/log3.log",
    "/path/to/log4.txt",
    "/path/to/log5.log"
  ]
}
交互细节
- 打开文件时，优先检查是否已在标签页中打开，避免重复。
- 最近文件列表中不包含当前已打开的文件。
关键字列表与检索面板联动实现细节
新建关键字时自动填充
- 触发时机
  - 用户在关键字列表面板点击"新建关键字"按钮时。
- 自动填充内容
  - 检查检索面板的过滤输入框是否有内容或配置选项（如：大小写忽略、精准匹配、正则表达式匹配）。
  - 若有，则将当前输入框内容和配置选项自动填充到新建关键字弹窗的对应字段中，用户可直接保存或编辑后保存。
- 配置选项同步
  - 配置选项包括但不限于：是否区分大小写、是否精准匹配、是否正则表达式匹配等。
# 伪代码示例
def on_new_keyword():
    filter_text, options = SearchPanel.get_current_filter()
    NewKeywordDialog.set_default_values(filter_text, options)
    NewKeywordDialog.exec_()
点击关键字自动应用到检索面板
- 触发时机
  - 用户点击关键字列表中的某个关键字时。
- 自动填充与检索
  - 将该关键字及其保存时的配置选项（如大小写、精准、正则等）设置到检索面板的过滤输入框和配置选项。
  - 自动触发一次检索，刷新日志展示和过滤面板的内容与高亮。
- 交互体验
  - 用户可一键切换不同关键字检索，无需手动输入和配置。
# 伪代码示例
def on_keyword_clicked(keyword):
    SearchPanel.set_filter(keyword.text, keyword.options)
    SearchPanel.trigger_search()
配置选项说明
- 大小写忽略：是否区分大小写（case sensitive）
- 精准匹配：是否全词匹配
- 正则表达式匹配：是否按正则表达式处理
交互细节
- 新建关键字弹窗应支持手动修改自动填充的内容和配置。
- 检索面板与关键字面板之间通过信号槽机制实现数据同步和事件响应。
- 关键字的配置选项需与检索面板的选项保持一致，便于用户理解和操作。
过滤日志高亮与交互跳转实现细节
1. 关键字高亮
- 高亮范围
  - 日志显示面板（LogViewer）和过滤面板（WorkspacePanel）在显示过滤日志时，均需对所有匹配的关键字进行高亮。
- 高亮实现
  - 推荐使用 QSyntaxHighlighter 或自定义高亮逻辑，支持多关键字、正则、大小写等配置。
关键字遍历与跳转
- 遍历操作
  - 用户点击"上一个/下一个"按钮遍历关键字匹配日志时：
  - 日志显示面板和过滤面板都需要同步跳转到当前关键字所在的行。
  - 关键字在视图中需"水平+垂直居中"显示，确保用户一眼看到。
  - 可通过滚动条和光标定位实现居中（如：QTextEdit.centerCursor() 并调整滚动条）。
- 同步跳转
  - 两个面板需通过信号槽机制同步跳转，保证用户无论在哪个面板操作，另一个面板都能同步定位。
# 伪代码示例
def on_next_keyword():
    line_no = FilterEngine.get_next_keyword_line()
    LogViewer.scroll_to_line_center(line_no)
    WorkspacePanel.scroll_to_line_center(line_no)
过滤面板双击跳转
- 操作说明
  - 用户在过滤面板（WorkspacePanel）双击某条过滤日志时：
  - 日志显示面板（LogViewer）自动跳转到该日志在完整日志中的对应行。
  - 关键字在该行中高亮，并且光标居中显示（水平+垂直）。
- 实现建议
  - 过滤面板需记录每条过滤日志在原始日志中的行号，便于跳转。
# 伪代码示例
def on_filtered_log_double_clicked(line_no):
    LogViewer.scroll_to_line_center(line_no)
交互体验细节
- 过滤面板可与标记面板并列或切换显示。
日志显示面板双击选词
- 操作说明
  - 用户在日志显示面板（LogViewer）双击时，应自动选中离双击点水平方向最近的单词。
- 实现建议
  - 获取鼠标双击位置，定位到最近的单词边界，设置为选中状态（QTextCursor.select(QTextCursor.WordUnderCursor)）。
# 伪代码示例
def on_logviewer_double_click(event):
    cursor = LogViewer.cursorForPosition(event.pos())
    cursor.select(QTextCursor.WordUnderCursor)
    LogViewer.setTextCursor(cursor)
交互体验细节
- 跳转时，若目标行已在视图中，仍需确保关键字高亮和光标居中。
- 支持键盘快捷键遍历关键字（如 F3/Shift+F3）。
- 双击过滤面板日志时，跳转到双击的日志在完整日志中所在的行。
日志标记功能与交互实现细节
1. 日志显示面板右键标记
- 右键菜单
  - 在日志显示面板（LogViewer）中右键单击时，弹出上下文菜单，包含"标记"选项。
- 标记操作
  - 用户点击"标记"后，将当前行日志添加到当前标签页的标记面板（MarkPanel）。
  - 若该行已被标记，可提供"取消标记"选项。
# 伪代码示例
def on_logviewer_right_click(line_no):
    show_context_menu(["标记", "取消标记" if is_marked(line_no) else None])
def on_mark_action(line_no):
    MarkPanel.add_mark(line_no, log_content)
标记面板内容与排序
- 内容管理
  - 标记面板（MarkPanel）显示所有已标记日志，内容包括日志文本和其在完整日志中的行号。
- 排序规则
  - 标记面板中的日志始终按照其在完整日志中的行号升序排列，便于回溯和定位。
- 高亮显示
  - 标记面板中的日志同样需要对关键字进行高亮，保持与主日志面板一致。
# 伪代码示例
def add_mark(line_no, log_content):
    marks.append((line_no, log_content))
    marks.sort(key=lambda x: x[0])
    refresh_mark_panel()
标记面板双击跳转
- 操作说明
  - 用户在标记面板中双击某条日志时，日志显示面板（LogViewer）自动跳转到该日志在完整日志中的对应行。
  - 关键字高亮，光标居中显示（水平+垂直）。
# 伪代码示例
def on_mark_panel_double_click(line_no):
    LogViewer.scroll_to_line_center(line_no)
交互体验细节
- 标记面板应支持删除标记（右键或按钮）。
- 标记状态应随标签页切换而切换，每个标签页独立维护自己的标记列表。
- 标记面板可与过滤面并列或切换显示。
- 标记操作应有视觉反馈（如高亮、图标等）。

快捷键交互细节
Ctrl+O (Command+O): 打开文件
- 交互流程：
  1. 用户按下快捷键
  2. 弹出文件选择对话框
  3. 用户选择文件后，在新标签页中打开
  4. 如果文件已经打开，切换到对应标签页
- 使用场景：
  - 在任何界面都可以使用此快捷键
  - 即使在欢迎页面也可以使用
Ctrl+F (Command+F): 搜索
- 交互流程：
  1. 用户按下快捷键
  2. 自动显示筛选面板（如果当前隐藏）
  3. 将焦点设置到筛选输入框
  4. 如果有选中的文本，自动填充到筛选输入框
  5. 全选筛选输入框中的文本（方便直接替换）
- 使用场景：
  - 在查看日志文件时可用
  - 在筛选结果面板中也可用
  - 在标记面板中不可用
Ctrl+W (Command+W): 关闭当前标签页
- 交互流程：
  1. 用户按下快捷键
  2. 关闭当前活动的标签页
  3. 如果是最后一个标签页：
  - 显示欢迎页面
  - 隐藏筛选面板和关键字面板
  1. 如果有其他标签页：
  - 切换到最近的标签页
- 使用场景：
  - 在有打开的日志文件时可用
  - 在欢迎页面时不可用
Ctrl+T (Command+T): 保存当前关键字到选中的分组
- 交互流程：
  1. 用户按下快捷键
  2. 弹出分组选择对话框
  1. 保存成功后显示提示信息（可以是状态栏或小弹窗）
- 使用场景：
  - 在筛选输入框有内容时可用
通用交互原则：
1. 快捷键操作应该有视觉反馈
2. 在不可用时，应该有适当的提示（如状态栏提示或提示音）
3. 所有快捷键操作都应该可以通过菜单项完成
4. 快捷键操作应该考虑上下文，在不同场景下可能有不同行为
5. 对于可能造成数据丢失的操作（如关闭标签页），应该有确认机制

如果程序运行时，遍历已打开列表打开文件时，如果有不存在的文件。应该弹窗提示，确认后将该文件从已打开列表中删除，不打开该文件，继续遍历其他已打开文件，当从最近打开的文件中选择文件打开时，如果该文件不存在，应该弹窗提示，确认后将该文件从最近打开的文件列表中删除，不要更改我其他现有的逻辑，只在打开文件前检测文件是否存在，不存在则删除记录跳过打开步骤，弹窗只需要提醒和确认即可，不需要取消按钮，弹窗内容为，最近列表中打开时弹窗内容：文件不存在：\n{filepath}\n\n该文件将从最近打开的文件列表中移除。   已保存列表中打开时弹窗内容：文件不存在：\n{filepath}\n\n无法打开该标签页。