# 围棋游戏资源文件说明

## 目录结构

```
assets/
├── sounds/          # 音效文件
│   ├── place_stone.wav    # 落子音效
│   ├── capture.wav        # 吃子音效
│   ├── illegal.wav        # 非法落子音效
│   ├── game_start.wav     # 游戏开始音效
│   ├── game_end.wav       # 游戏结束音效
│   ├── clock_tick.wav     # 计时器音效
│   ├── time_warning.wav   # 时间警告音效
│   └── button_click.wav   # 按钮点击音效
│
├── icons/           # 图标文件
│   └── (应用图标，工具栏图标等)
│
├── themes/          # 主题配置
│   ├── wood.json          # 木纹主题
│   ├── modern.json        # 现代主题
│   └── dark.json          # 暗黑主题
│
├── config/          # 配置文件
│   ├── config.json        # 游戏配置
│   └── hotkeys.json       # 快捷键配置
│
├── data/            # 数据文件
│   └── statistics.json    # 统计信息
│
├── saves/           # 游戏存档
│   └── *.pkl             # 保存的游戏文件
│
├── sgf/             # SGF棋谱文件
│   └── *.sgf             # 标准SGF格式棋谱
│
├── joseki/          # 定式库
│   └── basic_joseki.json  # 基础定式数据
│
└── images/          # 图片资源
    └── (背景图片，纹理等)
```

## 文件格式说明

### 主题文件格式 (JSON)
- board: 棋盘相关颜色配置
- stones: 棋子样式配置
- markers: 标记和提示配置
- ui: 界面元素配置

### 配置文件格式 (JSON)
- 包含所有游戏设置选项
- 语言、音效、规则、AI等配置

### SGF文件格式
- 标准围棋棋谱格式
- 支持导入导出

### 音效要求
- WAV格式，22050Hz采样率
- 单声道，16位
- 时长控制在1秒以内

## 扩展说明

可以通过以下方式扩展资源：
1. 添加新的主题文件到themes目录
2. 添加新的音效到sounds目录
3. 扩展joseki数据库
4. 添加自定义图标和图片

## 注意事项

- 所有文本文件使用UTF-8编码
- 路径使用相对路径，便于打包
- 资源文件大小应适度，避免程序体积过大
