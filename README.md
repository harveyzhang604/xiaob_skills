# 🎯 AI Tool Keyword Hunter - Profit Hunter Ultimate

自动化蓝海关键词猎取系统，专注发现低竞争、高需求的AI工具关键词机会。

## 📌 版本选择

### 🚀 Lite 版（推荐，快速版）
**特点**：融合 [Yuanbao Skills](https://github.com/harveyzhang604/yuanbao_skills) 的优点
- ✅ **DuckDuckGo SERP** - 避免 Google 限频，速度快
- ✅ **GPTs Benchmark** - 用 "GPTs" 作为热度基准
- ✅ **加权意图评分** - 痛点+3分，工具+2分
- ✅ **简化决策矩阵** - BUILD NOW / WATCH / DROP
- ⏱️ **运行时间**：10-15分钟
- 📦 **文件**：`profit_hunter_lite.py`

### 🔬 Deep 版（深度版）
**特点**：我们的原创深度验证系统
- 🔍 **Reddit 痛点挖掘** - 搜索真实用户抱怨
- 📊 **Google SERP 分析** - 检测市场空白
- ✅ **综合需求验证** - 多维度评分（0-100分）
- ⏱️ **运行时间**：1小时
- 📦 **文件**：`profit_hunter_ultimate.py` + `profit_hunter_deep_validation.py`

## ✨ 核心功能

### V4.0 Lite (NEW) - 融合版
- 🚀 **DuckDuckGo SERP 分析** - 轻量级，不限频
- 📈 **GPTs Benchmark 对比** - 只保留热度 ≥5% GPTs 的词
- 🎯 **加权意图评分系统** - 痛点（+3分）> 工具（+2分）> 对比（+2分）
- 📏 **词长度限制** - 只保留 3-8 词的长尾词
- 🎨 **简化决策矩阵** - BUILD NOW / WATCH / DROP

### V3.0 Deep Validation - 深度版
- 🔍 **Reddit 痛点挖掘** - 搜索真实用户抱怨和需求
- 📊 **Google SERP 分析** - 检测市场空白（论坛多但工具少）
- ✅ **综合需求验证** - 多维度评分（0-100分）
- 🎯 **长尾词优先** - 筛选3-4词组合，避开竞争激烈的大词
- 🤖 **AI可解决筛选** - 排除实物产品，只保留软件工具需求

### 基础功能
- 📝 Google Autocomplete 关键词挖掘
- 📈 Google Trends 趋势分析
- 🏆 SERP 竞争分析
- ⏰ 定时自动运行

## 🚀 快速开始

### 选项 A: Lite 版（快速，推荐）


#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 准备种子词
编辑 `words.md`，添加你的种子关键词（如 calculator, converter, checker）

#### 3. 运行
```bash
# Windows
run_lite.bat

# Linux/Mac
python profit_hunter_lite.py
```

#### 4. 查看结果
打开 `data/reports/profit_hunter_lite_*.html`

---

### 选项 B: Deep 版（深度分析）

#### 1-2. 同上

#### 3. 运行
```bash
# Windows
run_deep_analysis.bat

# Linux/Mac
python profit_hunter_ultimate.py --trends --max 100
python profit_hunter_deep_validation.py --input data/ultimate_final_results.csv --max 30
```

#### 4. 查看结果
打开 `data/reports/deep_validation_report_*.html`

---

### 选项 C: 定时运行（每天4次）
```bash
python scheduler_deep.py
```

## 📊 版本对比

| 特性 | Lite 版 🚀 | Deep 版 🔬 |
|------|-----------|-----------|
| **运行时间** | 10-15分钟 | 1小时 |
| **SERP 分析** | DuckDuckGo（快速） | Playwright + Google（准确） |
| **需求验证** | GPTs Benchmark | Reddit + SERP 深度验证 |
| **评分系统** | 加权意图评分 | 综合验证评分（0-100） |
| **决策矩阵** | BUILD / WATCH / DROP | 多维度评分 + 决策建议 |
| **适用场景** | 快速测试、日常监控 | 深度研究、重要决策 |
| **推荐人群** | 快速迭代、初学者 | 深度分析、专业用户 |

## 📊 输出结果

### 文件结构
```
data/
├── ultimate_final_results.csv          # 基础挖掘结果（100个关键词）
├── validation/
│   └── deep_validation_*.csv           # 深度验证结果
└── reports/
    ├── profit_hunter_ultimate_report.html       # 基础报告
    └── deep_validation_report_*.html            # 深度验证报告
```

### 报告内容
- 📊 统计概览（验证总数、真实需求数、通过率）
- 🔥 验证通过的关键词详情
- 🔍 Reddit证据（讨论数、痛点信号、真实抱怨）
- 📈 SERP证据（市场空白、商业意图）
- 💡 判断理由

## ⚙️ 配置说明

### 运行时间表（定时模式）
| 时间 | 任务 | 预计耗时 |
|------|------|---------|
| 00:00 | 深度分析 | 1小时 |
| 06:00 | 深度分析 | 1小时 |
| 12:00 | 深度分析 | 1小时 |
| 18:00 | 深度分析 | 1小时 |

### 验证评分标准
- 🟢 **80+分**：极品！立即做
- 🟡 **60-80分**：优质机会，值得做
- 🔴 **<60分**：需求不足，放弃

验证分数 = Reddit分 × 50% + SERP分 × 30% + 商业意图 × 20%

## 📖 详细文档

查看 [DEEP_ANALYSIS_GUIDE.md](DEEP_ANALYSIS_GUIDE.md) 获取完整配置指南和使用说明。

## 🎯 使用示例

### 输入
种子词：calculator, converter, checker

### 过程
1. 挖掘100个相关关键词
2. 筛选长尾词（3-4词组合）
3. Reddit验证（搜索真实用户讨论）
4. SERP分析（检测市场空白）
5. 综合评分（多维度验证）

### 输出（示例）
```
✅ calculator with fractions (验证分数: 76/100)
   • Reddit讨论: 23条
   • 痛点信号: 8个
   • 市场空白: ✅ 是
   • 判断: 真实需求，值得开发

✅ converter 20 kb (验证分数: 72/100)
   • Reddit讨论: 15条
   • 痛点信号: 6个
   • 市场空白: ✅ 是
   • 判断: 真实需求，值得开发
```

## 🔧 高级配置

### 调整验证深度
编辑 `profit_hunter_deep_validation.py`:
```python
VALIDATION_CONFIG = {
    "REDDIT_SEARCH_LIMIT": 20,      # 每个词搜索的Reddit帖子数
    "GOOGLE_SERP_LIMIT": 10,        # 每个词搜索的Google结果数
    "VALIDATION_THRESHOLD": 3,      # 最少需要的真实需求验证数
}
```

### 调整运行频率
编辑 `scheduler_deep.py`:
```python
# 改为每天2次
schedule.every().day.at("06:00").do(run_ultimate_analysis)
schedule.every().day.at("18:00").do(run_ultimate_analysis)
```

## ⚠️ 注意事项

1. **Reddit API 限制**：免费版每分钟60次请求，建议礼貌延迟2-3秒
2. **Google 搜索限制**：直接爬取容易被封IP，建议使用代理
3. **法律合规**：遵守网站的 robots.txt，不要过于频繁请求

## 📝 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**Tip**: 第一次使用建议先运行 `run_deep_analysis.bat` 测试效果，确认无误后再启动定时任务。
