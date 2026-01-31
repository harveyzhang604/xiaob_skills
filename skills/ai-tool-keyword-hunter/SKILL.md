---
name: profit-hunter-ultimate
description: "终极版蓝海关键词自动猎取系统。整合 Google Autocomplete (Alphabet Soup)、Google Trends 二级深挖、GPTs 基准对比、用户意图深挖、Playwright SERP 降维打击分析。自动识别竞争度、痛点强度、用户真正意图、商业价值。每 6 小时自动运行，输出高质量'立即做'机会清单。核心升级：降维打击检测（前3名有论坛=机会）、用户意图分析（不只看信号，还看用户真正想做什么）、显示 GPTs 热度比、列全关键词（不采样）。Use when: 'find profitable keywords', 'blue ocean opportunities', 'serp analysis', 'user intent mining', '/hunt-ultimate' command."
license: MIT
---

# 💎 Profit Hunter ULTIMATE - 终极版蓝海关键词猎取系统

## 🎯 核心理念

```
降维打击 > 正面竞争
小而美 > 大而全
真需求 > 伪需求
自动化 > 手动
```

**唯一目标**：找到那些**前3名是论坛/博客**的关键词，做一个工具站轻松占据首页。

---

## 🚀 核心升级（v3.0 ULTIMATE）

### 1. **用户意图深挖（NEW！）**

```python
不只检测信号（tool, calculator），
还要分析用户真正想做什么：

- calculate: 用户想计算某个数值
- convert: 用户想转换单位/格式
- generate: 用户想自动生成内容
- check: 用户想验证/检查某事
- ...
```

**输出字段：**
- `user_intent`: 意图类型（如 "calculate, convert"）
- `user_goal`: 用户真正想做什么（如 "复合需求：calculate + convert"）
- `intent_clarity`: 意图清晰度（高/中/低）

### 2. **GPTs 热度比显示（NEW！）**

```
旧版：只有内部计算
新版：CSV 和终端都显示 avg_ratio

例如：
- avg_ratio = 17.2% → 候选词达到 GPTs 的 17.2% 热度
- avg_ratio = 3.5%  → 刚好达到入围线
```

### 3. **列全关键词（NEW！）**

```
旧版：只采样 30 个
新版：全部种子词 + 全部挖掘结果（500+）

max_candidates 参数可调整（默认 500）
```

### 4. **SERP 降维打击检测（v2.0）**

```python
if Google 前3名有 Reddit/Quora：
    → 🟢 WEAK (降维打击机会！)
    → Competition Score = 100 分
    → 🔴 BUILD NOW
```

**实现方式：**
- **Playwright 自动化**：真实浏览器访问 Google
- **域名识别**：检测前3名是否为论坛/博客
- **降维打击判断**：自动标记机会

### 5. **二级 Related Queries 深挖（v2.0）**

```
Step 1: 找飙升词（Rising Queries）
Step 2: 对每个飙升词，再找它的飙升词
        ↓
     发现隐藏更深的机会
```

---

## 📋 完整工作流程

```
Step 0: Google Autocomplete 海量挖词（Alphabet Soup）
        ↓
Step 1: Google Trends 飙升词捕捉 + 二级深挖 ⭐
        ↓
Step 2: GPTs 基准对比（热度验证）✅ 必选
        ↓
Step 3: SERP 竞争分析（Playwright 降维打击检测）⭐
        ↓
Step 4: 需求意图评分（Pain Points Detection）
        ↓
Step 4.5: 用户意图深挖（User Intent Mining）🆕
        ↓
Step 5: 终极评分（优化算法）⭐
        ↓
Step 6: 输出决策（BUILD/WATCH/DROP）
```

---

## 🔥 降维打击原理

### 什么是"降维打击"？

```
场景：Google 首页前3名是 Reddit、Quora、Medium

原因：用户有需求，但没有好工具

机会：做一个简单的工具站
      ↓
    轻松占据首页
      ↓
    流量 → 广告收入 💰
```

### 检测逻辑

```python
SERP_WEAK_COMPETITORS = [
    "reddit.com", "quora.com", "stackoverflow.com",
    "medium.com", "dev.to", "blogger.com", "wordpress.com"
]

SERP_GIANTS = [
    "google.com", "microsoft.com", "adobe.com",
    "canva.com", "figma.com", "notion.so"
]

if 前3名有 WEAK_COMPETITORS and 没有 GIANTS:
    → 降维打击机会！
```

### 真实案例

**关键词：** `aura calculator`

```
2024年12月 TikTok 开始流行
    ↓
Google 搜索量飙升
    ↓
首页全是 Reddit/Medium 博客文章
    ↓
开发者快速做了工具站
    ↓
占据首页第1名
    ↓
月入 $500-2000（广告）
```

---

## 🎯 评分算法详解

### 最终评分公式

```
Final Score = (
    Trend Score × 25% +        # GPTs 对比热度
    Intent Score × 35% +       # 需求强度（⬆️提高权重）
    Competition Score × 25% +   # 竞争度（降维打击加成）
    Buildability Score × 15%    # 可实现性
)
```

### Trend Score（热度评分）

| GPTs Ratio | Growth | Score | 判断 |
|-----------|--------|-------|------|
| ≥ 20% | > 0 | 100 | 极品词 |
| ≥ 10% | > 5 | 85 | 优质词 |
| ≥ 3% | 任意 | 70 | 合格词 |
| < 3% | 任意 | 50 | 基础分 |

### Intent Score（需求强度）

| 信号类型 | 关键词模式 | 加分 |
|---------|-----------|------|
| **强痛点** | struggling with, how to fix, error | +40 |
| **工具** | calculator, generator, converter | +30 |
| **对比** | vs, alternative, better than | +25 |
| **B2B** | bulk, api, export, team | +25 |
| **速度** | fast, quick, instant, auto | +20 |
| **长尾** | 2-4 个词 | +15 |

### Competition Score（竞争度）

| SERP 特征 | Score | 降维打击 |
|----------|-------|---------|
| **前3名有论坛** | 100 | ✅ |
| 🟢 LOW/WEAK | 90 | ✅ |
| 🟡 MEDIUM | 60 | ❌ |
| 🔴 GIANT（大厂） | 30 | ❌ |

### Buildability Score（可实现性）

| 关键词类型 | Score |
|----------|-------|
| 直接工具词（calculator, generator） | 100 |
| 在线/免费（online, free） | 85 |
| 其他 | 70 |

### 决策阈值（优化后）

| 评分范围 | 决策 | 行动 |
|---------|------|------|
| **≥ 65** | 🔴 BUILD NOW | 立即开发 |
| **45-65** | 🟡 WATCH | 观察或测试 |
| **< 45** | ❌ DROP | 放弃 |

---

## 🚀 使用方法

### 快速测试

```bash
python test_ultimate.py
```

**预期结果：**
- 挖掘 30 个关键词
- 发现 20-29 个"立即做"
- 耗时 3-5 分钟

### 完整运行

```bash
# 基础版（推荐日常使用）
python profit_hunter_ultimate.py

# 包含 Trends 深度挖掘
python profit_hunter_ultimate.py --trends

# 终极版（包含 Playwright）
python profit_hunter_ultimate.py --trends --playwright --max 50
```

### 定时任务

```bash
# 启动定时调度器（每 6 小时）
python scheduler.py
```

**Windows 后台运行：**
```cmd
start /B python scheduler.py
```

**Linux/Mac 后台运行：**
```bash
nohup python scheduler.py > scheduler.log 2>&1 &
```

---

## 📊 输出说明

### CSV 文件

```
data/
├── ultimate_final_results.csv  # 最终结果（⭐ 最重要）
├── step0_suggest_keywords.csv  # Google Suggest 原始数据
├── step1_trends_deep.csv       # Trends 飙升词（含二级）
├── step2_gpts_comparison.csv   # GPTs 对比数据
└── step3_serp_analysis.csv     # SERP 竞争分析
```

### 关键字段

| 字段 | 含义 | 示例 |
|------|------|------|
| `keyword` | 关键词 | calculator online |
| `final_score` | 最终评分 | 80.8 |
| `decision` | 决策 | 🔴 BUILD NOW |
| `avg_ratio` | vs GPTs 热度比 | 17.2% (达到 GPTs 的 17.2%热度) |
| `user_intent` | 用户意图类型 | calculate, convert |
| `user_goal` | 用户真正想做什么 | 复合需求：calculate + convert |
| `intent_clarity` | 意图清晰度 | 高/中/低 |
| `competition` | 竞争度 | 🟢 ZERO / 🟡 MEDIUM / 🔴 HIGH |
| `降维打击` | 是否有降维打击机会 | True/False |
| `intent_score` | 意图评分 | 45-100 |
| `signals` | 信号词 | 工具:calculator, 长尾:2词 |

---

## 🔧 安装依赖

### 必须安装

```bash
pip install requests pandas pytrends schedule
```

### 可选安装（强烈推荐）

```bash
# Playwright（用于 SERP 降维打击分析）
pip install playwright
playwright install chromium
```

### 验证安装

```bash
python -c "import requests, pandas, pytrends, schedule; print('✅ 基础依赖 OK')"
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright OK')"
```

---

## 💡 实战策略

### Strategy 1：降维打击（推荐）

```
1. 运行 ULTIMATE 版本（启用 Playwright）
2. 筛选 "降维打击=True" 的词
3. 选择评分最高的前 3 个
4. 快速做工具（Next.js + Vercel）
5. 提交到 Google Search Console
6. 等待 7-14 天
7. 观察流量和排名
```

### Strategy 2：热度验证（稳健）

```
1. 运行基础版（包含 Trends）
2. 筛选 avg_ratio ≥ 0.1 的词
3. 看 Google Trends 曲线（是否上升）
4. 选择增长最快的词
5. 做工具 + SEO 优化
```

### Strategy 3：工具矩阵（进阶）

```
1. 找到一个优质词根（如 calculator）
2. 做 20-50 个细分计算器
3. 每个都是独立页面
4. SEO 互相导流
5. 形成"计算器矩阵"
```

---

## 🆚 版本对比

| 特性 | Pro 版 | ⭐ ULTIMATE 版 |
|-----|-------|---------------|
| Alphabet Soup | ✅ | ✅ 优化 |
| Google Trends | 可选 | **必选 + 二级深挖** |
| GPTs 对比 | 可选（跳过） | **必选** ✅ |
| SERP 分析 | 简单规则 | **Playwright 降维打击** ⭐ |
| 评分阈值 | 75 分 | **65 分** ✅ |
| 立即做的词 | 0 个 | **29 个** ✅ |
| 定时任务 | apscheduler | **schedule（6小时）** |
| 耗时 | 3 分钟 | 5-10 分钟 |

---

## ⚙️ 高级配置

### 调整评分阈值

编辑 `profit_hunter_ultimate.py`：

```python
THRESHOLDS = {
    "BUILD_NOW": 65,     # 立即做阈值（降低 = 更多推荐）
    "WATCH": 45,         # 观察阈值
    "MIN_GPTS_RATIO": 0.03,  # 最低 GPTs 比值（降低 = 更宽松）
}
```

### 定制痛点词库

```python
PAIN_TRIGGERS = {
    "strong": [
        "struggling with", "how to fix",
        # 添加你发现的新痛点词
        "cannot", "doesn't work"
    ],
    # ...
}
```

### 调整定时频率

编辑 `scheduler.py`：

```python
# 每 6 小时
schedule.every(6).hours.do(job)

# 或改为每天固定时间
schedule.every().day.at("09:00").do(job)
```

---

## 🐛 故障排查

### 问题 1：没有"立即做"的词

**原因：** 种子词质量差 或 GPTs 对比失败

**解决：**
1. 检查 `data/step2_gpts_comparison.csv` 是否有数据
2. 降低 `BUILD_NOW` 阈值（如改为 60）
3. 更换种子词

### 问题 2：Google Trends 限频

**现象：** 大量 "对比失败" 警告

**解决：**
1. 减少种子词数量（`words.md` 只保留 5-10 个）
2. 增加延迟（编辑脚本中的 `time.sleep(3)` → `time.sleep(10)`）
3. 使用代理（编辑 `TrendReq` 初始化）

### 问题 3：Playwright 安装失败

**解决：**
```bash
# 方案1：手动安装
pip install playwright
playwright install chromium

# 方案2：不使用 Playwright
python profit_hunter_ultimate.py  # 不加 --playwright 参数
```

---

## 📈 成功指标

### 短期（7天）

- [ ] 发现 ≥ 5 个"立即做"的词
- [ ] 选择 1 个开始实现
- [ ] 工具上线并提交 GSC

### 中期（30天）

- [ ] 工具进入 Google 前 10 名
- [ ] 获得首批自然流量
- [ ] 设置好定时任务

### 长期（90天）

- [ ] 工具矩阵（3-5 个工具）
- [ ] 月自然流量 > 1000
- [ ] 月广告收入 > $500

---

## 💰 核心理念（再次强调）

```
不做大词！不做大词！不做大词！

大词 = calculator, converter
     ↓
   竞争激烈 ❌

小词 + 降维打击 = aura calculator (前3名是 Reddit)
     ↓
   轻松占据首页 ✅
     ↓
   流量 → 广告收入 💰💰💰
```

---

## 🎁 下一步行动

### Today

```bash
python test_ultimate.py
```

查看能找到哪些"立即做"的机会。

### This Week

1. 运行完整版（包含 Trends 和 Playwright）
2. 选择 Top 1 的词
3. 快速做一个工具（Next.js + Vercel）

### This Month

```bash
python scheduler.py
```

启动定时任务，持续监控新机会。

---

**开始行动！💎🚀💰**
