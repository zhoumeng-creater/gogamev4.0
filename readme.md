# 围棋大师 Go Master 2.0

一个功能完整的围棋游戏程序，支持人机对战、AI对战、棋谱分析、定式学习等功能。

## 功能特性

### 核心功能
- ✅ 完整的围棋规则实现（中国规则、日本规则、AGA规则）
- ✅ 多种棋盘大小（9x9, 13x13, 19x19）
- ✅ 完整的死活判定和数子系统
- ✅ 劫争检测（包括超级劫）
- ✅ 让子和贴目设置

### 游戏模式
- ✅ 人类对战
- ✅ 人机对战
- ✅ AI对战观战
- ✅ 复盘分析
- ✅ 教学模式
- ✅ 死活题练习

### AI系统
- ✅ 多级别AI（初学者到大师）
- ✅ 随机AI、贪心AI、极小极大AI
- ✅ 蒙特卡洛树搜索（MCTS）
- ✅ 定式AI、战术AI
- ✅ 神经网络AI框架（预留接口）

### 计时系统
- ✅ 包干时间
- ✅ 日本读秒
- ✅ 加拿大计时
- ✅ 费舍尔计时
- ✅ 布朗斯坦延时

### 用户界面
- ✅ 多语言支持（中文、英文、日文）
- ✅ 多种主题（木纹、现代、暗黑）
- ✅ 落子动画和吃子动画
- ✅ 坐标显示、手数显示
- ✅ 落子预览、提示功能
- ✅ 局面分析面板

### 存储功能
- ✅ 游戏存档（pickle/JSON格式）
- ✅ SGF棋谱导入导出
- ✅ 自动保存
- ✅ 云存储支持（预留接口）

### 分析功能
- ✅ 局面评估
- ✅ 胜率分析
- ✅ 最佳着法推荐
- ✅ 形势判断
- ✅ 地盘计算

### 学习功能
- ✅ 定式库（基础定式）
- ✅ 战术识别
- ✅ 死活题库
- ✅ 教学系统

### 统计功能
- ✅ 游戏统计
- ✅ 玩家统计
- ✅ 胜率分析
- ✅ 成就系统

## 项目结构

```
go_master/
├── main.py                 # 主程序入口
├── core/                   # 核心逻辑模块
│   ├── board.py           # 棋盘类
│   ├── rules.py           # 规则引擎
│   ├── game.py            # 游戏控制
│   ├── territory.py       # 地盘和死活判定
│   └── scoring.py         # 计分系统
├── ui/                     # 用户界面模块
│   ├── board_canvas.py    # 棋盘绘制
│   ├── panels.py          # 各种面板
│   ├── dialogs.py         # 对话框
│   ├── themes.py          # 主题管理
│   └── animations.py      # 动画效果
├── ai/                     # AI模块
│   ├── base.py            # AI基类
│   ├── simple_ai.py       # 简单AI
│   ├── search_ai.py       # 搜索AI
│   ├── pattern_ai.py      # 模式AI
│   └── neural_ai.py       # 神经网络AI
├── features/               # 功能模块
│   ├── replay.py          # 复盘系统
│   ├── analysis.py        # 分析引擎
│   ├── joseki.py          # 定式库
│   ├── teaching.py        # 教学系统
│   └── network.py         # 网络对战
├── utils/                  # 工具模块
│   ├── config.py          # 配置管理
│   ├── sound.py           # 音效管理
│   ├── sgf.py             # SGF处理
│   ├── timer.py           # 计时器
│   ├── translator.py      # 翻译系统
│   ├── storage.py         # 存储管理
│   └── statistics.py      # 统计系统
└── assets/                 # 资源文件
    ├── translations/       # 翻译文件
    ├── joseki/            # 定式数据
    ├── sounds/            # 音效文件
    └── themes/            # 主题文件
```

## 安装说明

### 环境要求
- Python 3.8+
- Tkinter（通常已包含在Python中）

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/yourusername/go_master.git
cd go_master
```

2. 创建虚拟环境（推荐）
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行程序
```bash
python main.py
```

## 使用说明

### 快捷键
- `Ctrl+N` - 新游戏
- `Ctrl+O` - 打开游戏
- `Ctrl+S` - 保存游戏
- `Ctrl+Z` - 悔棋
- `Ctrl+Y` - 重做
- `P` - 虚手
- `R` - 认输
- `H` - 提示
- `A` - 分析
- `S` - 数子
- `F11` - 全屏
- `Space` - 暂停

### 游戏规则
程序支持三种主要规则：
- **中国规则**：数子法，贴7.5目
- **日本规则**：数目法，贴6.5目
- **AGA规则**：混合规则，贴7.5目

### AI难度说明
- **初学者**：随机落子，适合初学者练习
- **简单**：贪心算法，有基本战术
- **中等**：加入局面评估，会简单定式
- **困难**：极小极大搜索，有深度计算
- **专家**：结合定式和战术，较强实力
- **大师**：MCTS算法，接近专业水平

## 开发说明

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 编写文档字符串
- 模块化设计

### 测试
```bash
pytest tests/
```

### 打包发布
```bash
pyinstaller main.spec
```

## 待完善功能

### 网络功能
- [ ] 在线对战
- [ ] 观战系统
- [ ] 棋谱分享
- [ ] 排行榜

### AI增强
- [ ] 深度学习模型集成
- [ ] 开局库扩充
- [ ] 自适应难度
- [ ] AI训练模式

### 分析功能
- [ ] 变化图显示
- [ ] 胜率曲线
- [ ] 关键手识别
- [ ] 对局评论

### 其他功能
- [ ] 语音识别落子
- [ ] 触屏支持
- [ ] 3D棋盘
- [ ] 自定义AI

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- 感谢所有贡献者
- 感谢开源社区的支持
- 特别感谢围棋爱好者的反馈

## 联系方式

- 项目主页：[https://github.com/yourusername/go_master](https://github.com/yourusername/go_master)
- 问题反馈：[Issues](https://github.com/yourusername/go_master/issues)
- 电子邮件：your.email@example.com

---
*享受围棋的乐趣！*