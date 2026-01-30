---
name: trend-breakout-hunter
description: "Daily Google Trends breakout keyword discovery for AI tool sites. Scans seed words against Google Trends Rising/Breakout queries, filters for tool-buildable opportunities, and outputs an actionable candidate list. Use when: 'find breakout keywords', 'today's trending terms', 'scan Google Trends', 'new tool opportunities', 'rising queries', or '/hunt-trends' command. Primary method: pytrends API. Fallback: browser automation."
license: MIT
---

# Trend Breakout Hunter

## SILENT EXECUTION PROTOCOL

```
╔════════════════════════════════════════════════════════════════╗
║  MANDATORY RULES - NO EXCEPTIONS                              ║
╠════════════════════════════════════════════════════════════════╣
║  1. DO NOT ask "Should I continue?" - just execute            ║
║  2. DO NOT ask for missing parameters - use defaults          ║
║  3. DO NOT output partial results - complete in one response  ║
║  4. If pytrends fails → switch to browser fallback silently   ║
║  5. If a seed word returns nothing → skip it, continue        ║
║  6. Generate FULL candidate list in ONE atomic response       ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Overview

This skill executes a daily workflow:

```
种子词表 (47 words.md)
       ↓
Google Trends → Related Queries → Rising/Breakout
       ↓
自动过滤（去噪声、去新闻、去人名）
       ↓
工具化判断（能否做成 calculator/generator/checker？）
       ↓
输出：AI 工具站候选词清单
```

---

## Execution Pipeline

### Step 0: Google Autocomplete Mining (Foundation Layer)

**核心原理**：从 words.md 的每个种子词出发，用 Google Suggest 接口挖掘真实用户搜索词组。

```
⚠️ 重要：Google Suggest ≠ Google Trends
   - Suggest = 实时用户输入行为信号（更早、更真实）
   - Trends = 统计后的搜索量趋势（有延迟）
   - 两者结合 = 既挖需求，又验热度
```

**API 接口（非官方但极稳）**：

```
https://suggestqueries.google.com/complete/search?client=firefox&q={query}&hl=en&gl=us
```

**返回格式**：
```json
[
  "calculator",
  ["calculator", "calculator app", "calculator online", "calculator scientific", "calculator date"]
]
```

**三种挖词模式（Alphabet Soup 技术）**：

| 模式 | 查询示例 | 挖掘目标 |
|------|----------|----------|
| **词在前** | `calculator` | 基础联想 |
| **词在前+空格** | `calculator ` | 后缀扩展 |
| **词在后（a-z枚举）** | `a calculator`, `b calculator`... | 前缀扩展 |
| **组合词** | `dating calculator` | 场景化扩展 |

**Google Suggest Code**：

```python
import requests
import time

def google_suggest(query, hl="en", gl="us"):
    """获取 Google 搜索联想词"""
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",
        "q": query,
        "hl": hl,
        "gl": gl
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()[1]
    except Exception as e:
        print(f"Suggest failed for '{query}': {e}")
        return []

def alphabet_soup_mining(seed_word, hl="en", gl="us"):
    """Alphabet Soup 全量挖词"""
    results = set()

    # 1️⃣ 基础查询：calculator
    results.update(google_suggest(seed_word, hl, gl))
    time.sleep(0.5)

    # 2️⃣ 后缀扩展：calculator _
    results.update(google_suggest(f"{seed_word} ", hl, gl))
    time.sleep(0.5)

    # 3️⃣ 前缀扩展：a-z + calculator
    for c in "abcdefghijklmnopqrstuvwxyz":
        suggestions = google_suggest(f"{c} {seed_word}", hl, gl)
        results.update(suggestions)
        time.sleep(0.3)  # 降低限频风险

    # 4️⃣ 数字前缀：0-9 + calculator
    for n in "0123456789":
        suggestions = google_suggest(f"{n} {seed_word}", hl, gl)
        results.update(suggestions)
        time.sleep(0.3)

    return list(results)

# 示例：挖掘 calculator 相关词
seed = "calculator"
all_suggestions = alphabet_soup_mining(seed)

# 过滤：只保留包含种子词的结果
tool_keywords = [s for s in all_suggestions if seed in s.lower()]
print(f"Found {len(tool_keywords)} tool keywords for '{seed}'")
for kw in sorted(tool_keywords):
    print(f"  - {kw}")
```

**批量处理所有种子词**：

```python
import pandas as pd

# 从 words.md 加载种子词
seed_words = [
    "calculator", "generator", "converter", "maker", "checker",
    "editor", "builder", "analyzer", "optimizer", "tracker"
    # ... 加载全部 47 个
]

all_keywords = []

for seed in seed_words:
    print(f"Mining: {seed}")
    suggestions = alphabet_soup_mining(seed)

    for s in suggestions:
        all_keywords.append({
            "seed": seed,
            "keyword": s,
            "word_count": len(s.split()),
            "source": "google_suggest"
        })

    time.sleep(2)  # 每个种子词之间暂停

# 保存结果
df = pd.DataFrame(all_keywords)
df.to_csv("suggest_keywords.csv", index=False)
print(f"Total keywords mined: {len(df)}")
```

**输出示例**：

| seed | keyword | word_count |
|------|---------|------------|
| calculator | age calculator | 2 |
| calculator | bmi calculator | 2 |
| calculator | love calculator | 2 |
| calculator | pregnancy due date calculator | 4 |
| generator | ai image generator | 3 |
| generator | qr code generator | 3 |

---

### Step 1: Harvest Rising/Breakout Terms

```python
from pytrends.request import TrendReq

pytrends = TrendReq(hl='en-US', tz=360)
pytrends.build_payload([seed_word], timeframe='now 7-d')
related = pytrends.related_queries()
rising_queries = related[seed_word]['rising']
# Look for: "Breakout" label OR growth > 100%
```

### Step 2: Benchmark Comparison (CRITICAL ⚠️)

**核心原理**：把每个新词和基准词 "GPTs" 放在**同一个 payload** 里对比。

```
⚠️ 重要：Google Trends 的数值是"相对值 0-100"
   - 同一个 payload 里的词共享同一个标尺，才能比较
   - 分开查询的数值不可比（标尺不同）
```

**Benchmark Code**:

```python
from pytrends.request import TrendReq
import pandas as pd
import time

pytrends = TrendReq(hl='en-US', tz=480, retries=2, backoff_factor=0.2)

def compare_to_gpts(term, timeframe="now 7-d", geo="", gprop=""):
    """Compare any term against 'GPTs' as benchmark"""
    kw_list = [term, "GPTs"]  # 关键：同一个 payload 里对比
    pytrends.build_payload(kw_list, timeframe=timeframe, geo=geo, gprop=gprop)

    df = pytrends.interest_over_time()
    if df is None or df.empty:
        return None

    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])

    term_series = df[term]
    gpts_series = df["GPTs"]

    term_avg = float(term_series.mean())
    gpts_avg = float(gpts_series.mean())

    # 热度比值（核心指标）
    ratio = (term_avg / gpts_avg) if gpts_avg > 0 else None

    # 增长速度（首尾差）
    term_growth = float(term_series.iloc[-1] - term_series.iloc[0])
    gpts_growth = float(gpts_series.iloc[-1] - gpts_series.iloc[0])
    growth_ratio = (term_growth / gpts_growth) if gpts_growth != 0 else None

    return {
        "term": term,
        "term_avg": term_avg,
        "gpts_avg": gpts_avg,
        "avg_ratio": ratio,           # term热度 / GPTs热度
        "term_growth": term_growth,
        "gpts_growth": gpts_growth,
        "growth_ratio": growth_ratio, # term增速 / GPTs增速
    }

# 批量对比
terms = ["aura calculator", "heic converter", "prompt optimizer"]
results = []
for t in terms:
    r = compare_to_gpts(t, timeframe="now 7-d")
    if r:
        results.append(r)
    time.sleep(4)  # 降低限频风险

out = pd.DataFrame(results).sort_values("avg_ratio", ascending=False)
print(out)
```

---

## Benchmark Decision Thresholds

| avg_ratio | term_growth | Decision | Meaning |
|-----------|-------------|----------|---------|
| **≥ 0.3** | > 0 | 🔴 **立即做** | 热度接近 GPTs，且在涨 |
| **0.1 - 0.3** | > 0 | 🟡 **重点观察** | 中等热度，有增长势头 |
| **0.05 - 0.1** | > 5 | 🟢 **早期红利** | 小众但涨速快，抢先机 |
| **< 0.05** | ≤ 0 | ❌ **丢弃** | 既不热也不涨 |

**简化规则**：
```
IF avg_ratio >= 0.3 AND term_growth > 0 → ✅ BUILD
IF avg_ratio >= 0.05 AND term_growth > 5 → 👀 WATCH
ELSE → ❌ DROP
```

---

## Fallback: Browser Automation (Detailed)

When pytrends fails (rate limit, 429 error, empty response), **silently switch** to browser automation.

### Trigger Conditions

```
Switch to browser fallback when:
- pytrends returns None or empty DataFrame
- HTTP 429 (Too Many Requests)
- Connection timeout after 2 retries
- "ResponseError" or "TooManyRequestsError"
```

### Browser Automation Workflow

**Step 1: Navigate to Google Trends**

```
URL Pattern: https://trends.google.com/trends/explore?q={seed_word}&date=now%207-d&geo=US

Example:
https://trends.google.com/trends/explore?q=calculator&date=now%207-d&geo=US
```

**Step 2: Wait for Page Load**

```
Wait for selector: div[class*="related-queries"]
Timeout: 10 seconds
If timeout → log error, skip this seed word, continue
```

**Step 3: Switch to "Rising" Tab**

```
Click selector: button[aria-label="Rising"]
   OR: div[class*="rising"]
   OR: text="Rising"

Wait 2 seconds for data refresh
```

**Step 4: Extract Rising Queries Table**

```
Target table: div[class*="related-queries"] table

For each row:
  - Column 1: Query text (the keyword)
  - Column 2: Growth value ("Breakout" or "+X%")

Store as:
{
  "query": "aura calculator",
  "growth": "Breakout",  // or "+450%"
  "seed": "calculator"
}
```

**Step 5: Screenshot for Verification (Optional)**

```
Save screenshot to: ./screenshots/{seed_word}_{YYYYMMDD}.png
Purpose: Debug validation, historical record
```

**Step 6: Benchmark Comparison (Same as pytrends)**

```
For each extracted query:
  Navigate to: https://trends.google.com/trends/explore?q={query},GPTs&date=now%207-d

  Extract both trend lines
  Calculate avg_ratio = query_avg / gpts_avg
  Apply same decision thresholds
```

### Browser Automation Code Example

```python
# Using Playwright (recommended for agent-browser)
from playwright.sync_api import sync_playwright
import time

def browser_harvest_rising(seed_word, headless=True):
    """Fallback: Extract rising queries via browser automation"""

    results = []
    url = f"https://trends.google.com/trends/explore?q={seed_word}&date=now%207-d&geo=US"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        try:
            # Step 1: Navigate
            page.goto(url, timeout=15000)

            # Step 2: Wait for related queries section
            page.wait_for_selector('div[class*="related-queries"]', timeout=10000)
            time.sleep(2)  # Let JS render

            # Step 3: Click "Rising" tab
            rising_btn = page.query_selector('button:has-text("Rising")')
            if rising_btn:
                rising_btn.click()
                time.sleep(2)

            # Step 4: Extract table rows
            rows = page.query_selector_all('div[class*="related-queries"] table tr')

            for row in rows[1:]:  # Skip header
                cells = row.query_selector_all('td')
                if len(cells) >= 2:
                    query = cells[0].inner_text().strip()
                    growth = cells[1].inner_text().strip()

                    results.append({
                        "query": query,
                        "growth": growth,
                        "seed": seed_word,
                        "source": "browser"
                    })

            # Step 5: Screenshot (optional)
            page.screenshot(path=f"./screenshots/{seed_word}_{time.strftime('%Y%m%d')}.png")

        except Exception as e:
            print(f"Browser fallback failed for {seed_word}: {e}")

        finally:
            browser.close()

    return results

def browser_compare_to_gpts(term, headless=True):
    """Fallback: Compare term vs GPTs via browser"""

    url = f"https://trends.google.com/trends/explore?q={term},GPTs&date=now%207-d&geo=US"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        try:
            page.goto(url, timeout=15000)
            page.wait_for_selector('div[class*="interest-over-time"]', timeout=10000)
            time.sleep(3)

            # Extract trend values from chart (simplified)
            # In practice, you'd parse the SVG or use accessibility labels

            # Screenshot for manual verification
            page.screenshot(path=f"./screenshots/compare_{term}_vs_GPTs.png")

            # Return placeholder - real impl would parse chart data
            return {
                "term": term,
                "comparison_screenshot": f"./screenshots/compare_{term}_vs_GPTs.png",
                "source": "browser"
            }

        except Exception as e:
            print(f"Browser comparison failed for {term}: {e}")
            return None

        finally:
            browser.close()
```

### Error Handling Matrix

| Error | Action | Log |
|-------|--------|-----|
| Page timeout | Skip seed, continue | `⚠️ {seed}: page timeout` |
| No rising tab | Use "Top" queries instead | `ℹ️ {seed}: no rising, using top` |
| Empty table | Skip seed, continue | `⚠️ {seed}: no rising queries` |
| CAPTCHA detected | Pause 60s, retry once | `🔄 {seed}: captcha, retrying` |
| Browser crash | Restart browser, continue | `🔄 Browser restarted` |

### Rate Limiting Best Practices

```
Browser automation rate limits:
- Wait 5-10 seconds between seed words
- Max 20 queries per session
- Rotate user agents if needed
- Use residential proxy for scale

Example pacing:
for seed in seed_words:
    results = browser_harvest_rising(seed)
    time.sleep(random.uniform(5, 10))  # Random delay
```

### When to Use Browser vs pytrends

| Scenario | Use |
|----------|-----|
| Daily batch (10-50 seeds) | pytrends first |
| pytrends 429 error | Switch to browser |
| Need visual verification | Browser + screenshot |
| Debugging discrepancies | Browser to confirm |
| pytrends data looks wrong | Browser as ground truth |

---

## Auto-Update words.md (New Root Words)

**每次运行后，自动将新发现的词根添加到 words.md**

```python
import re
from datetime import datetime

def extract_new_roots(candidates):
    """从候选词中识别新词根"""
    # 已知词根列表（从 words.md 加载）
    known_roots = load_known_roots()

    # 潜在新词根模式
    root_patterns = [
        r'(\w+er)$',      # cloner, humanizer, upscaler
        r'(\w+or)$',      # predictor, generator
        r'(\w+izer)$',    # summarizer, optimizer
        r'(\w+ator)$',    # calculator, translator
    ]

    new_roots = {}

    for c in candidates:
        keyword = c.get('keyword', '').lower()
        words = keyword.split()

        for word in words:
            for pattern in root_patterns:
                match = re.search(pattern, word)
                if match:
                    potential_root = word.capitalize()
                    # 检查是否是新词根
                    if potential_root.lower() not in [r.lower() for r in known_roots]:
                        if potential_root not in new_roots:
                            new_roots[potential_root] = {
                                "example": keyword,
                                "count": 1
                            }
                        else:
                            new_roots[potential_root]["count"] += 1

    # 只保留出现 2 次以上的新词根
    return {k: v for k, v in new_roots.items() if v["count"] >= 2}

def load_known_roots():
    """从 words.md 加载已知词根"""
    known_roots = []
    try:
        with open("words.md", "r", encoding="utf-8") as f:
            for line in f:
                # 提取第二列（名称）
                parts = line.strip().split("\t")
                if len(parts) >= 2 and parts[0].isdigit():
                    # 提取词根名（去掉中文注释）
                    root_name = parts[1].split("（")[0].strip()
                    known_roots.append(root_name)
    except FileNotFoundError:
        pass
    return known_roots

def append_new_roots_to_words_md(new_roots):
    """将新词根自动追加到 words.md"""
    if not new_roots:
        print("ℹ️ No new roots to add")
        return []

    added_roots = []

    # 读取现有内容，获取最大序号
    try:
        with open("words.md", "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 找到最大序号
        max_num = 0
        for line in lines:
            parts = line.strip().split("\t")
            if parts and parts[0].isdigit():
                max_num = max(max_num, int(parts[0]))
    except FileNotFoundError:
        lines = ["序号\t名称\t用户需求\t常见搭配\n"]
        max_num = 0

    # 追加新词根
    with open("words.md", "a", encoding="utf-8") as f:
        for root, info in new_roots.items():
            max_num += 1
            # 生成用户需求描述
            need_desc = f"用户搜索 {root} 相关工具或功能。"
            # 生成常见搭配
            example = info["example"]
            common_use = f"AI {root}, Online {root}, Free {root}"

            new_line = f"{max_num}\t{root}（{root.lower()}）\t{need_desc}\t{common_use}\n"
            f.write(new_line)
            added_roots.append(root)
            print(f"✅ Added new root: {root} (example: {example})")

    return added_roots

def run_daily_hunt_with_auto_update():
    """每日猎词主流程（含自动更新 words.md）"""

    # ... 前面的步骤保持不变 ...

    # Step 0-4: 执行关键词猎取
    qualified = execute_hunt_pipeline()

    # Step 5: 生成 HTML 报告
    report_file = generate_html_report(qualified, stats, execution_notes)

    # Step 6: 自动更新 words.md ⬅️ 新增
    new_roots = extract_new_roots(qualified)
    if new_roots:
        added = append_new_roots_to_words_md(new_roots)
        print(f"\n📝 Auto-added {len(added)} new roots to words.md:")
        for root in added:
            print(f"   - {root}")

    return report_file, qualified, new_roots
```

**新词根识别规则**：

| 模式 | 示例 | 说明 |
|------|------|------|
| `*er` | Cloner, Upscaler | 动作执行者 |
| `*or` | Predictor, Processor | 执行器类 |
| `*izer` | Summarizer, Humanizer | 转化工具 |
| `*ator` | Calculator, Translator | 计算/翻译类 |

**添加条件**：
```
1. 匹配词根模式（*er, *or, *izer, *ator）
2. 在候选词中出现 ≥ 2 次
3. 不在现有 words.md 中
```

**words.md 更新示例**：

```
# 自动追加的新词根（2025-01-28）
48	Cloner（cloner）	用户搜索 Cloner 相关工具或功能。	AI Cloner, Online Cloner, Free Cloner
49	Humanizer（humanizer）	用户搜索 Humanizer 相关工具或功能。	AI Humanizer, Online Humanizer, Free Humanizer
50	Upscaler（upscaler）	用户搜索 Upscaler 相关工具或功能。	AI Upscaler, Online Upscaler, Free Upscaler
51	Predictor（predictor）	用户搜索 Predictor 相关工具或功能。	AI Predictor, Online Predictor, Free Predictor
52	Summarizer（summarizer）	用户搜索 Summarizer 相关工具或功能。	AI Summarizer, Online Summarizer, Free Summarizer
```

---

## Seed Word Categories

Load from `words.md` (47 root words):

| Category | Words | Tool Potential |
|----------|-------|----------------|
| **Generators** | Generator, Maker, Creator, Builder | ⭐⭐⭐⭐⭐ |
| **Converters** | Converter, Convert, Translator, Format | ⭐⭐⭐⭐⭐ |
| **Calculators** | Calculator, Estimator, Evaluator | ⭐⭐⭐⭐⭐ |
| **Checkers** | Checker, Detector, Verifier, Analyzer | ⭐⭐⭐⭐ |
| **Editors** | Editor, Processor, Optimizer | ⭐⭐⭐⭐ |
| **Managers** | Manager, Planner, Scheduler, Tracker | ⭐⭐⭐ |
| **Viewers** | Viewer, Explorer, Monitor, Dashboard | ⭐⭐⭐ |
| **Others** | Downloader, Uploader, Extractor, Scraper | ⭐⭐⭐ |

---

## Auto-Filter Rules (Critical)

### ✅ KEEP - High Value Signals

```
Contains ANY of:
  - calculator, generator, maker, converter, checker
  - ai, tool, online, free
  - how to, best, vs

AND meets:
  - Growth: "Breakout" OR > 100%
  - Word count: 2-5 words (not too short, not too long)
  - Has clear noun (not just adjectives)
```

### ❌ DROP - Noise Signals

```
Auto-reject if:
  - Person name (celebrity, politician, athlete)
  - Geographic name only (city, country)
  - News event (election, disaster, scandal)
  - Single word with no context
  - Contains: death, scandal, lawsuit, arrest
  - Entertainment only: movie, song, album, episode
```

### ⚠️ REVIEW - Edge Cases

```
Flag for human review if:
  - Gaming terms (could be simulator opportunity)
  - Brand names (could be "X alternative" opportunity)
  - Ambiguous intent
```

---

## Tool-Buildability Assessment

For each surviving keyword, score 1-5:

| Score | Criteria | Example |
|-------|----------|---------|
| 5 | Direct tool match (X + root word) | "aura calculator" |
| 4 | Implied tool need (how to X) | "how to convert heic" |
| 3 | Possible tool (needs validation) | "ai voice clone" |
| 2 | Weak tool signal | "best ai apps" |
| 1 | No tool intent | "what is chatgpt" |

**Threshold**: Only include score ≥ 3

---

## SERP Competition Quick Check

For high-potential keywords, assess SERP:

| SERP Pattern | Competition | Action |
|--------------|-------------|--------|
| All blogs/articles | 🟢 Low | Build immediately |
| Mix of tools + blogs | 🟡 Medium | Build with differentiation |
| Big tech tools dominate | 🔴 High | Skip or niche down |
| Empty/thin results | 🟢 Very Low | First mover advantage |

---

## Output Format

### HTML Report Generation (MANDATORY)

**每次运行必须生成 HTML 报告，保存到 `data/` 文件夹**

```
文件命名规则：
data/keyword_report_{YYYYMMDD}_{HHMMSS}.html

示例：
data/keyword_report_20250128_143052.html
```

**HTML 报告生成代码**：

```python
import os
from datetime import datetime

def generate_html_report(candidates, stats, execution_notes):
    """生成 HTML 分析报告"""

    # 确保 data 文件夹存在
    os.makedirs("data", exist_ok=True)

    # 生成文件名（含日期时间）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/keyword_report_{timestamp}.html"

    # 构建 HTML 内容
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Trend Breakout Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        .stat-card .number {{ font-size: 2.5rem; font-weight: bold; color: #00d9ff; }}
        .stat-card .label {{ color: #aaa; margin-top: 0.5rem; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 2rem 0;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            overflow: hidden;
        }}
        th, td {{ padding: 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ background: rgba(0,217,255,0.2); font-weight: 600; }}
        tr:hover {{ background: rgba(255,255,255,0.05); }}
        .priority-high {{ color: #ff6b6b; font-weight: bold; }}
        .priority-medium {{ color: #ffd93d; }}
        .priority-low {{ color: #6bcb77; }}
        .growth-breakout {{
            background: linear-gradient(90deg, #ff6b6b, #ff8e53);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
        }}
        .section {{ margin: 3rem 0; }}
        .section h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(0,217,255,0.3);
        }}
        .top-actions {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
        }}
        .action-card {{
            background: linear-gradient(135deg, rgba(0,217,255,0.2), rgba(0,255,136,0.1));
            border-radius: 12px;
            padding: 1.5rem;
            border-left: 4px solid #00d9ff;
        }}
        .action-card h3 {{ color: #00d9ff; margin-bottom: 0.5rem; }}
        .notes {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1.5rem;
            font-family: monospace;
        }}
        .footer {{
            text-align: center;
            margin-top: 3rem;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Trend Breakout Report</h1>
        <p style="color:#aaa;">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <!-- Stats Cards -->
        <div class="stats">
            <div class="stat-card">
                <div class="number">{stats['seeds_scanned']}</div>
                <div class="label">Seeds Scanned</div>
            </div>
            <div class="stat-card">
                <div class="number">{stats['rising_found']}</div>
                <div class="label">Rising Terms Found</div>
            </div>
            <div class="stat-card">
                <div class="number">{stats['after_filter']}</div>
                <div class="label">After Filtering</div>
            </div>
            <div class="stat-card">
                <div class="number">{stats['qualified']}</div>
                <div class="label">Qualified Candidates</div>
            </div>
        </div>

        <!-- Main Table -->
        <div class="section">
            <h2>📊 AI Tool Site Candidates</h2>
            <table>
                <thead>
                    <tr>
                        <th>Keyword</th>
                        <th>Seed</th>
                        <th>Growth</th>
                        <th>GPTs Ratio</th>
                        <th>Tool Type</th>
                        <th>Buildability</th>
                        <th>Competition</th>
                        <th>Decision</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(generate_table_rows(candidates))}
                </tbody>
            </table>
        </div>

        <!-- Top 5 Actions -->
        <div class="section">
            <h2>🔥 Top 5 Immediate Actions</h2>
            <div class="top-actions">
                {"".join(generate_action_cards(candidates[:5]))}
            </div>
        </div>

        <!-- Execution Notes -->
        <div class="section">
            <h2>⚠️ Execution Notes</h2>
            <div class="notes">
                <p><strong>Method:</strong> {execution_notes['method']}</p>
                <p><strong>Seeds Skipped:</strong> {execution_notes.get('skipped', 'None')}</p>
                <p><strong>Errors:</strong> {execution_notes.get('errors', 'None')}</p>
            </div>
        </div>

        <div class="footer">
            Generated by Trend Breakout Hunter Skill | {datetime.now().strftime("%Y-%m-%d")}
        </div>
    </div>
</body>
</html>"""

    # 保存文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Report saved: {filename}")
    return filename

def generate_table_rows(candidates):
    """生成表格行 HTML"""
    rows = []
    for c in candidates:
        growth_class = "growth-breakout" if "Breakout" in str(c.get('growth', '')) else ""
        priority_class = {
            "Build": "priority-high",
            "Watch": "priority-medium",
            "Drop": "priority-low"
        }.get(c.get('decision', '').replace('✅', '').replace('👀', '').replace('❌', '').strip(), "")

        rows.append(f"""
            <tr>
                <td><strong>{c.get('keyword', '')}</strong></td>
                <td>{c.get('seed', '')}</td>
                <td><span class="{growth_class}">{c.get('growth', 'N/A')}</span></td>
                <td>{c.get('avg_ratio', 'N/A')}</td>
                <td>{c.get('tool_type', '')}</td>
                <td>{c.get('buildability', '')}/5</td>
                <td>{c.get('competition', '')}</td>
                <td class="{priority_class}">{c.get('decision', '')}</td>
            </tr>
        """)
    return rows

def generate_action_cards(top_candidates):
    """生成 Top Actions 卡片 HTML"""
    cards = []
    for i, c in enumerate(top_candidates, 1):
        cards.append(f"""
            <div class="action-card">
                <h3>#{i} {c.get('keyword', '')}</h3>
                <p><strong>Growth:</strong> {c.get('growth', 'N/A')}</p>
                <p><strong>Ratio vs GPTs:</strong> {c.get('avg_ratio', 'N/A')}</p>
                <p><strong>Why:</strong> {c.get('reason', 'High potential opportunity')}</p>
            </div>
        """)
    return cards
```

**完整执行流程（含报告生成）**：

```python
def run_daily_hunt():
    """每日关键词猎取主流程"""
    from datetime import datetime

    # Step 0: Google Suggest 挖词
    all_suggestions = []
    for seed in seed_words:
        suggestions = alphabet_soup_mining(seed)
        all_suggestions.extend(suggestions)

    # Step 1: Google Trends Rising/Breakout
    rising_terms = harvest_rising_terms(seed_words)

    # Step 2: GPTs Benchmark 对比
    candidates = []
    for term in rising_terms:
        result = compare_to_gpts(term['query'])
        if result:
            candidates.append({**term, **result})

    # Step 3: 过滤 + 评分
    qualified = filter_and_score(candidates)

    # Step 4: 排序（按优先级）
    qualified.sort(key=lambda x: (
        x.get('decision', '') == '✅Build',
        x.get('avg_ratio', 0)
    ), reverse=True)

    # Step 5: 生成 HTML 报告 ⬅️ 必须执行
    stats = {
        "seeds_scanned": len(seed_words),
        "rising_found": len(rising_terms),
        "after_filter": len(candidates),
        "qualified": len(qualified)
    }
    execution_notes = {
        "method": "pytrends (primary)",
        "skipped": "None",
        "errors": "None"
    }

    report_file = generate_html_report(qualified, stats, execution_notes)

    # 同时输出 Markdown 到控制台
    print_markdown_summary(qualified)

    return report_file, qualified

# 运行
if __name__ == "__main__":
    report_file, results = run_daily_hunt()
    print(f"\n🎉 Done! Report: {report_file}")
```

**报告文件结构**：

```
data/
├── keyword_report_20250128_143052.html
├── keyword_report_20250129_091530.html
├── keyword_report_20250130_083015.html
└── ...
```

---

### Candidate List Table

```markdown
# 🎯 Trend Breakout Report

> **Date**: {YYYY-MM-DD}
> **Seeds Scanned**: {count}/47
> **Rising Terms Found**: {count}
> **After Filtering**: {count}
> **Qualified Candidates**: {count}

---

## 📊 AI Tool Site Candidates

| Keyword | Seed | Growth | Tool Type | Buildability | Competition | Decision |
|---------|------|--------|-----------|--------------|-------------|----------|
| {term} | {root} | 🚀Breakout / +X% | calc/gen/check/conv | 1-5 | Low/Med/High | ✅Build / 👀Watch / ❌Drop |

---

## 🔥 Top 5 Immediate Actions

1. **{keyword}** - {reason why it's #1}
2. ...

---

## 📝 New Root Words Discovered

| New Root | Example Usage | Add to words.md? |
|----------|---------------|------------------|
| {word} | {example} | Yes/No |

---

## ⚠️ Execution Notes

- Method used: pytrends / browser fallback
- Seeds skipped: {list if any}
- Errors encountered: {list if any}
```

---

## Database Schema (For Long-term Storage)

Store results for historical tracking:

```sql
CREATE TABLE trend_candidates (
  id INTEGER PRIMARY KEY,
  date DATE NOT NULL,
  seed_term VARCHAR(50),
  trend_term VARCHAR(100),
  growth_type VARCHAR(20),  -- 'breakout' or percentage
  growth_value INTEGER,     -- null for breakout, number for %
  tool_type VARCHAR(20),    -- calculator/generator/checker/converter/other
  buildability_score INTEGER CHECK (buildability_score BETWEEN 1 AND 5),
  competition VARCHAR(10),  -- low/medium/high
  decision VARCHAR(10),     -- build/watch/drop
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Recommended**: Export to CSV daily, import to Notion/Airtable weekly

---

## Example Execution

### Input
```
User: 帮我跑一下今天的趋势词
```

### Correct Output (Abbreviated)

```markdown
# 🎯 Trend Breakout Report

> **Date**: 2025-01-28
> **Seeds Scanned**: 47/47
> **Rising Terms Found**: 312
> **After Filtering**: 89
> **Qualified Candidates**: 23

---

## 📊 AI Tool Site Candidates

| Keyword | Seed | Growth | Tool Type | Buildability | Competition | Decision |
|---------|------|--------|-----------|--------------|-------------|----------|
| aura points calculator | Calculator | 🚀Breakout | calculator | 5 | Low | ✅Build |
| heic to jpg converter | Converter | +450% | converter | 5 | Medium | ✅Build |
| ai voice generator free | Generator | +280% | generator | 5 | High | 👀Watch |
| prompt optimizer tool | Optimizer | +190% | optimizer | 4 | Low | ✅Build |
| deepseek vs chatgpt | Comparator | 🚀Breakout | comparator | 4 | Medium | ✅Build |

---

## 🔥 Top 5 Immediate Actions

1. **aura points calculator** - TikTok viral, zero competition, simple build
2. **heic to jpg converter** - Evergreen need, existing tools are clunky
3. **prompt optimizer tool** - AI workflow essential, low competition
4. **deepseek vs chatgpt** - Hot topic, comparison page opportunity
5. **n8n template generator** - Automation trend, developer audience

---

## 📝 New Root Words Discovered

| New Root | Example Usage | Add to words.md? |
|----------|---------------|------------------|
| Cloner | voice cloner, style cloner | Yes |
| Humanizer | ai humanizer, text humanizer | Yes |

---

## ⚠️ Execution Notes

- Method used: pytrends (primary)
- Seeds skipped: None
- Errors encountered: None
```

---

## Anti-Patterns (FORBIDDEN)

```
❌ "我找到了一些词，你想看哪些？"
   → 必须一次性输出全部

❌ "pytrends 报错了，怎么办？"
   → 静默切换到 browser fallback

❌ "这个词我不确定，你觉得呢？"
   → 用评分系统自动判断，不要问

❌ "需要我继续扫描剩下的种子词吗？"
   → 必须扫描全部，一次完成

❌ "输出太长了，要分批吗？"
   → 不分批，完整输出
```

---

## Integration with Other Skills

After running this skill:

| Next Step | Use Skill | Purpose |
|-----------|-----------|---------|
| Validate content angle | `content-strategy` | Confirm topic worth writing |
| Scale to multiple pages | `programmatic-seo` | Template-based page generation |
| Build comparison pages | `competitor-alternatives` | "X vs Y" or "X alternative" pages |
| Add structured data | `schema-markup` | Rich snippets for SERP |
| Track performance | `analytics-tracking` | Monitor organic traffic |

---

## Limitations

- pytrends is unofficial; may hit rate limits (solution: add delays, use proxies)
- "Breakout" threshold is Google's black box (solution: also track high % growth)
- Some trends are noise (solution: auto-filter rules above)
- SERP check is manual (solution: integrate SerpAPI for automation)

---

## Quick Commands

| Command | Action |
|---------|--------|
| `/hunt-trends` | Run full scan with all 47 seeds |
| `/hunt-trends calculator` | Scan only "calculator" related |
| `/hunt-trends --top10` | Output only top 10 candidates |
| `/hunt-trends --export csv` | Output in CSV format |
