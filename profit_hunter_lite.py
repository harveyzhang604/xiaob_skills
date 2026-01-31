#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 Profit Hunter LITE - 轻量级快速版
=====================================

融合 Yuanbao Skills 的优点：
1. ✅ DuckDuckGo SERP 分析（避免 Google 限频）
2. ✅ 加权意图评分系统（痛点+3，工具+2，对比+2）
3. ✅ GPTs Benchmark 基准对比
4. ✅ 简化决策矩阵（BUILD/WATCH/DROP）
5. ✅ 词长度限制（3-8词）
6. ✅ 极简设计（单文件，快速执行）

+ 我们的优势：
7. ✅ 长尾词优先
8. ✅ AI可解决筛选
9. ✅ 精美HTML报告

运行时间：约10-15分钟（vs 1小时深度版）
适用场景：快速测试、日常监控

作者：AI Profit Hunter Team
版本：4.0 Lite (融合版)
日期：2026-01-31
"""

import os
import sys
import time
import re
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Set
from pytrends.request import TrendReq
import warnings
warnings.filterwarnings('ignore')

# ==================== 配置区 ====================

SEED_WORDS_FILE = "words.md"
DATA_DIR = "data"
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

# Benchmark 基准关键词（来自 Yuanbao）
BENCHMARK_KEYWORD = "GPTs"
MIN_RATIO = 0.05  # 最低热度比值：5%
TIMEFRAME = "now 7-d"

# 词长度限制（来自 Yuanbao）
MIN_WORDS = 3
MAX_WORDS = 8

# 弱竞争对手域名（来自 Yuanbao，扩展版）
WEAK_COMPETITORS = [
    'reddit.com', 'quora.com', 'medium.com', 'stackoverflow.com',
    'github.com', 'dev.to', 'indiehackers.com', 'linkedin.com',
    'twitter.com', 'facebook.com', 'pinterest.com'
]

# 意图评分权重（来自 Yuanbao）
INTENT_WEIGHTS = {
    "pain": 3,        # 痛点信号权重最高
    "tool": 2,        # 商业工具意图
    "comparison": 2   # 竞争对比
}

# 痛点信号词库（扩展版）
PAIN_TRIGGERS = [
    "struggling with", "can't", "cannot", "fix", "solve", "error",
    "slow", "manual", "tedious", "hard to", "alternative to",
    "how to", "problem", "issue", "help", "need", "frustrated",
    "annoying", "difficult", "broken", "not working"
]

# 商业工具信号（扩展版）
COMMERCIAL_TRIGGERS = [
    "tool", "app", "generator", "calculator", "converter",
    "maker", "builder", "checker", "editor", "analyzer",
    "tracker", "finder", "downloader", "optimizer", "creator"
]

# ==================== 工具函数 ====================

def log_execution(message: str, level: str = "INFO"):
    """日志记录"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def ensure_dirs():
    """确保目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

def load_seed_words(filepath: str = SEED_WORDS_FILE) -> List[str]:
    """加载种子词"""
    if not os.path.exists(filepath):
        log_execution(f"⚠️ {filepath} 不存在，使用默认种子词", "WARNING")
        return ["calculator", "generator", "converter"]
    
    seeds = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('序号'):
                continue
            
            # 提取关键词
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    word = parts[1].strip()
                    match = re.match(r'([A-Za-z]+)', word)
                    if match:
                        seeds.append(match.group(1).lower())
    
    seeds = list(dict.fromkeys(seeds))
    log_execution(f"✅ 加载了 {len(seeds)} 个种子词")
    return seeds[:5]  # 限制为5个种子词（快速模式）

# ==================== Step 1: Google Autocomplete 挖掘 ====================

def google_suggest(query: str, gl: str = "us") -> List[str]:
    """调用 Google Autocomplete API"""
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",
        "q": query,
        "hl": "en",
        "gl": gl
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data[1] if len(data) > 1 else []
    except Exception as e:
        log_execution(f"Suggest 失败 '{query}': {str(e)[:50]}", "WARNING")
        return []

def mine_keywords(seeds: List[str]) -> List[str]:
    """挖掘关键词（Alphabet Soup 策略）"""
    log_execution(f"🔍 Step 1: 挖掘关键词（{len(seeds)} 个种子词）")
    
    all_keywords = set()
    
    for idx, seed in enumerate(seeds, 1):
        log_execution(f"  [{idx}/{len(seeds)}] 挖掘: {seed}")
        
        # 基础查询
        all_keywords.update(google_suggest(seed))
        time.sleep(0.5)
        
        # 后缀空格
        all_keywords.update(google_suggest(f"{seed} "))
        time.sleep(0.5)
        
        # Alphabet Soup（采样：每隔一个字母）
        for char in "abcdefghijklmnopqrstuvwxyz"[::2]:
            all_keywords.update(google_suggest(f"{seed} {char}"))
            time.sleep(0.3)
        
        log_execution(f"  ✅ {seed}: 累计 {len(all_keywords)} 个候选词")
    
    return list(all_keywords)

# ==================== Step 2: 意图评分与筛选 ====================

def calculate_intent_score(keyword: str) -> Dict:
    """
    计算意图评分（借鉴 Yuanbao 的加权系统）
    
    评分规则：
    - 痛点信号：+3分
    - 商业工具：+2分
    - 竞争对比：+2分
    
    通过标准：≥2分
    """
    kw_lower = keyword.lower()
    intent_score = 0
    signals = []
    
    # 痛点信号（权重最高）
    if any(p in kw_lower for p in PAIN_TRIGGERS):
        intent_score += INTENT_WEIGHTS["pain"]
        signals.append("Pain")
    
    # 商业工具意图
    if any(c in kw_lower for c in COMMERCIAL_TRIGGERS):
        intent_score += INTENT_WEIGHTS["tool"]
        signals.append("Tool")
    
    # 竞争对比意图
    if " vs " in kw_lower or "alternative" in kw_lower or "instead of" in kw_lower:
        intent_score += INTENT_WEIGHTS["comparison"]
        signals.append("Comparison")
    
    return {
        "intent_score": intent_score,
        "signals": signals,
        "is_high_intent": intent_score >= 2
    }

def filter_candidates(keywords: List[str]) -> List[Dict]:
    """
    筛选候选词
    
    筛选条件：
    1. 词长度：3-8 词（来自 Yuanbao）
    2. 意图评分：≥2分
    3. 长尾词优先
    4. AI可解决（非实物产品）
    """
    log_execution(f"🔍 Step 2: 筛选候选词（从 {len(keywords)} 个中筛选）")
    
    candidates = []
    
    # 排除实物产品的关键词
    physical_products = [
        "maker 20", "ice maker", "coffee maker", "bread maker",
        "generator 20", "diesel generator", "honda generator",
        "phone", "laptop", "camera", "printer", "tablet"
    ]
    
    for kw in keywords:
        kw_lower = kw.lower()
        words = kw_lower.split()
        
        # 条件1: 词长度限制（3-8词）
        if not (MIN_WORDS <= len(words) <= MAX_WORDS):
            continue
        
        # 条件2: 排除实物产品
        if any(pp in kw_lower for pp in physical_products):
            continue
        
        # 条件3: 计算意图评分
        intent_data = calculate_intent_score(kw)
        
        if intent_data["is_high_intent"]:
            candidates.append({
                "keyword": kw,
                "word_count": len(words),
                "intent_score": intent_data["intent_score"],
                "signals": ", ".join(intent_data["signals"])
            })
    
    # 按意图评分排序
    candidates.sort(key=lambda x: x["intent_score"], reverse=True)
    
    log_execution(f"✅ 筛选出 {len(candidates)} 个高意图候选词")
    return candidates

# ==================== Step 3: GPTs Benchmark 对比 ====================

def benchmark_against_gpts(candidates: List[Dict], max_check: int = 20) -> List[Dict]:
    """
    用 "GPTs" 作为基准，对比关键词热度（来自 Yuanbao）
    
    只保留热度 ≥ 5% GPTs 的词
    """
    log_execution(f"🔍 Step 3: GPTs Benchmark 对比（检查 Top {max_check} 个）")
    
    verified = []
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, retries=2, backoff_factor=0.5)
    except Exception as e:
        log_execution(f"⚠️ Trends 初始化失败: {e}", "WARNING")
        return candidates[:max_check]
    
    for idx, item in enumerate(candidates[:max_check], 1):
        kw = item["keyword"]
        log_execution(f"  [{idx}/{max_check}] 检查: {kw}")
        
        try:
            pytrends.build_payload([BENCHMARK_KEYWORD, kw], timeframe=TIMEFRAME)
            df = pytrends.interest_over_time()
            
            if not df.empty and BENCHMARK_KEYWORD in df.columns and kw in df.columns:
                avg_gpts = df[BENCHMARK_KEYWORD].mean()
                avg_kw = df[kw].mean()
                ratio = avg_kw / avg_gpts if avg_gpts > 0 else 0
                
                item["avg_gpts"] = avg_gpts
                item["avg_kw"] = avg_kw
                item["ratio"] = ratio
                item["ratio_pct"] = f"{ratio*100:.1f}%"
                
                # 只保留 ratio ≥ 5% 的词
                if ratio >= MIN_RATIO:
                    verified.append(item)
                    log_execution(f"    ✅ 通过：{ratio*100:.1f}% vs GPTs")
                else:
                    log_execution(f"    ❌ 过滤：{ratio*100:.1f}% < 5%")
            
            time.sleep(2)  # 礼貌延迟
            
        except Exception as e:
            log_execution(f"    ⚠️ 错误: {str(e)[:50]}", "WARNING")
    
    log_execution(f"✅ {len(verified)} 个关键词通过 GPTs Benchmark")
    return verified

# ==================== Step 4: DuckDuckGo SERP 分析 ====================

def analyze_serp_ddg(keyword: str) -> Dict:
    """
    用 DuckDuckGo 分析 SERP（来自 Yuanbao，轻量级）
    
    优点：
    - 不需要 Playwright
    - 不会被 Google 限频
    - 速度快（1-2秒/词）
    """
    url = f"https://html.duckduckgo.com/html/?q={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            # 用 Regex 提取结果链接
            links = re.findall(r'class="result__a" href="([^"]+)"', r.text)
            
            domains = []
            for link in links[:5]:  # 只检查 Top 5
                try:
                    domain = link.split("/")[2].replace("www.", "")
                    domains.append(domain)
                except:
                    pass
            
            # 检测弱竞争对手
            weak_spots = sum(1 for d in domains if any(w in d for w in WEAK_COMPETITORS))
            
            # 决策矩阵（来自 Yuanbao）
            if weak_spots >= 2:
                competition = "🟢 LOW"
                decision = "BUILD NOW"
            elif weak_spots == 1:
                competition = "🟡 MED"
                decision = "WATCH"
            else:
                competition = "🔴 HIGH"
                decision = "DROP"
            
            return {
                "top_domains": domains,
                "weak_spots": weak_spots,
                "competition": competition,
                "decision": decision,
                "has_gap": weak_spots >= 2
            }
        else:
            return {"error": f"HTTP {r.status_code}"}
            
    except Exception as e:
        return {"error": str(e)}

def analyze_serp_batch(candidates: List[Dict]) -> List[Dict]:
    """批量 SERP 分析"""
    log_execution(f"🔍 Step 4: SERP 竞争分析（{len(candidates)} 个关键词）")
    
    for idx, item in enumerate(candidates, 1):
        kw = item["keyword"]
        log_execution(f"  [{idx}/{len(candidates)}] 分析: {kw}")
        
        serp_data = analyze_serp_ddg(kw)
        
        if "error" not in serp_data:
            item.update(serp_data)
            log_execution(f"    {serp_data['competition']} - {serp_data['decision']}")
        else:
            item["competition"] = "⚪ UNKNOWN"
            item["decision"] = "SKIP"
            log_execution(f"    ⚠️ 错误: {serp_data['error'][:30]}", "WARNING")
        
        time.sleep(1.5)  # 礼貌延迟
    
    return candidates

# ==================== Step 5: 生成报告 ====================

def generate_html_report(results: List[Dict]) -> str:
    """生成精美的HTML报告"""
    # 按决策排序：BUILD NOW > WATCH > DROP
    results.sort(key=lambda x: (
        x.get("decision") == "BUILD NOW",
        x.get("decision") == "WATCH",
        x.get("ratio", 0)
    ), reverse=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(REPORTS_DIR, f"profit_hunter_lite_{timestamp}.html")
    
    # 统计
    build_now = sum(1 for r in results if r.get("decision") == "BUILD NOW")
    watch = sum(1 for r in results if r.get("decision") == "WATCH")
    drop = sum(1 for r in results if r.get("decision") == "DROP")
    avg_ratio = sum(r.get("ratio", 0) for r in results) / len(results) if results else 0
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Profit Hunter Lite Report - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .content {{
            padding: 40px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        .result-item {{
            background: #f8f9fa;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }}
        .keyword {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .build-now {{ border-left-color: #28a745; }}
        .watch {{ border-left-color: #ffc107; }}
        .drop {{ border-left-color: #dc3545; }}
        .tag {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-right: 8px;
            margin-bottom: 5px;
        }}
        .tag-build {{ background: #28a745; color: white; }}
        .tag-watch {{ background: #ffc107; color: #333; }}
        .tag-drop {{ background: #dc3545; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Profit Hunter Lite Report</h1>
            <p>轻量级快速版 - 融合 Yuanbao Skills 优点</p>
            <p style="opacity: 0.8; margin-top: 10px;">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="content">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(results)}</div>
                    <div>总候选词</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{build_now}</div>
                    <div>🟢 BUILD NOW</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{watch}</div>
                    <div>🟡 WATCH</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{drop}</div>
                    <div>🔴 DROP</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{avg_ratio*100:.1f}%</div>
                    <div>平均热度 vs GPTs</div>
                </div>
            </div>
            
            <h2 style="margin-bottom: 20px; border-bottom: 3px solid #667eea; padding-bottom: 10px;">
                📊 分析结果
            </h2>
"""
    
    for idx, item in enumerate(results, 1):
        decision = item.get("decision", "SKIP")
        css_class = "build-now" if "BUILD" in decision else ("watch" if "WATCH" in decision else "drop")
        tag_class = "tag-build" if "BUILD" in decision else ("tag-watch" if "WATCH" in decision else "tag-drop")
        
        html_content += f"""
            <div class="result-item {css_class}">
                <div class="keyword">{idx}. {item['keyword']}</div>
                <div>
                    <span class="tag {tag_class}">{decision}</span>
                    <span class="tag" style="background: #e9ecef; color: #333;">{item.get('competition', 'N/A')}</span>
                    <span class="tag" style="background: #e7f3ff; color: #2196F3;">
                        热度: {item.get('ratio_pct', 'N/A')}
                    </span>
                    <span class="tag" style="background: #fff3cd; color: #856404;">
                        意图分: {item['intent_score']}分
                    </span>
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    <strong>信号:</strong> {item['signals']} | 
                    <strong>弱竞争对手:</strong> {item.get('weak_spots', 0)} | 
                    <strong>Top域名:</strong> {', '.join(item.get('top_domains', [])[:3])}
                </div>
            </div>
"""
    
    html_content += """
        </div>
    </div>
</body>
</html>
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    log_execution(f"📄 HTML报告已生成: {filename}")
    return filename

# ==================== 主函数 ====================

def main():
    """主函数"""
    ensure_dirs()
    
    log_execution("\n" + "="*60)
    log_execution("🚀 Profit Hunter LITE - 轻量级快速版")
    log_execution("融合 Yuanbao Skills + 我们的优势")
    log_execution("="*60 + "\n")
    
    # Step 1: 加载种子词
    seeds = load_seed_words()
    
    # Step 2: 挖掘关键词
    raw_keywords = mine_keywords(seeds)
    log_execution(f"✅ Step 1 完成：挖掘了 {len(raw_keywords)} 个关键词")
    
    # Step 3: 筛选候选词
    candidates = filter_candidates(raw_keywords)
    log_execution(f"✅ Step 2 完成：筛选出 {len(candidates)} 个候选词")
    
    # Step 4: GPTs Benchmark 对比
    verified = benchmark_against_gpts(candidates, max_check=20)
    log_execution(f"✅ Step 3 完成：{len(verified)} 个通过 Benchmark")
    
    # Step 5: SERP 竞争分析
    final_results = analyze_serp_batch(verified)
    log_execution(f"✅ Step 4 完成：SERP 分析完成")
    
    # Step 6: 生成报告
    report_path = generate_html_report(final_results)
    
    # 输出结果
    log_execution("\n" + "="*60)
    log_execution("🏁 运行完成！")
    log_execution("="*60)
    
    print("\n📊 Top 10 结果：")
    for idx, item in enumerate(final_results[:10], 1):
        print(f"\n{idx}. {item['keyword']}")
        print(f"   决策: {item.get('decision', 'N/A')}")
        print(f"   竞争: {item.get('competition', 'N/A')}")
        print(f"   热度: {item.get('ratio_pct', 'N/A')} vs GPTs")
        print(f"   意图: {item['signals']}")
    
    print(f"\n📄 完整报告: {report_path}")

if __name__ == "__main__":
    main()
