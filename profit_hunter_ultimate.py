#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 Profit Hunter ULTIMATE - 终极版蓝海关键词自动猎取系统
=========================================================

核心升级：
1. ✅ Playwright SERP 竞争分析（降维打击检测）
2. ✅ 二级 Related Queries 深挖（飙升词的飙升词）
3. ✅ 优化评分算法（更容易出现"立即做"的词）
4. ✅ 每 6 小时自动运行
5. ✅ GPTs 基准对比（必选，不再是可选）

作者：AI Profit Hunter Team
版本：2.0 Ultimate
日期：2026-01-30
"""

import os
import sys
import time
import json
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import quote
from typing import List, Dict, Optional, Set
import warnings
warnings.filterwarnings('ignore')

# ==================== 配置区 ====================

SEED_WORDS_FILE = "words.md"
DATA_DIR = "data"
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "screenshots")

# Google Trends 请求频率控制（极保守配置！避免限频）
TRENDS_CONFIG = {
    "BATCH_SIZE": 2,           # 每批词数（极保守：2 个）
    "DELAY_PER_REQUEST": 8,    # 每次请求后延迟秒数（极保守：8 秒）
    "DELAY_BETWEEN_BATCHES": 20,  # 批次间延迟秒数（极保守：20 秒）
    "MAX_RETRIES": 3,          # 最大重试次数
    "TIMEOUT": (15, 30),       # 请求超时（连接, 读取）
}

# 评分阈值（优化后更容易达到"立即做"）
THRESHOLDS = {
    "BUILD_NOW": 65,     # 降低从 75 → 65
    "WATCH": 45,         # 降低从 50 → 45
    "MIN_GPTS_RATIO": 0.03,  # GPTs 最低比值：3%（原来是 5%）
    "GOOD_GPTS_RATIO": 0.1,  # 优质比值：10%
    "GREAT_GPTS_RATIO": 0.2  # 极品比值：20%
}

# 痛点信号词库（扩展版）
PAIN_TRIGGERS = {
    "strong": [
        "struggling with", "how to fix", "error", "broken", "not working",
        "failed", "manual", "tedious", "time consuming", "slow", "cannot",
        "doesn't work", "help with", "problem with", "issue with"
    ],
    "tool": [
        "calculator", "generator", "converter", "maker", "checker",
        "editor", "builder", "tool", "app", "software", "online", "free",
        "downloader", "analyzer", "optimizer", "tracker", "detector"
    ],
    "comparison": [
        "vs", "versus", "alternative", "better than", "instead of", "replace",
        "compare", "difference between"
    ],
    "b2b": [
        "bulk", "batch", "api", "export", "team", "enterprise", "multiple",
        "mass", "auto", "automatic", "automation"
    ],
    "speed": [
        "fast", "quick", "instant", "real-time", "live", "automatic", "auto"
    ]
}

# 用户意图分类（新增）
USER_INTENT_PATTERNS = {
    "calculate": ["calculator", "calculate", "compute", "formula"],
    "convert": ["converter", "convert", "to", "from"],
    "generate": ["generator", "generate", "create", "maker"],
    "check": ["checker", "check", "verify", "validate", "test"],
    "compare": ["vs", "versus", "compare", "difference"],
    "download": ["download", "downloader", "get", "save"],
    "edit": ["editor", "edit", "modify", "change"],
    "analyze": ["analyzer", "analyze", "analytics", "report"],
    "track": ["tracker", "track", "monitor", "follow"],
    "search": ["finder", "search", "find", "lookup"],
}

# SERP 竞争对手数据库（大厂 vs 弱鸡）
SERP_GIANTS = [
    "google.com", "microsoft.com", "adobe.com", "apple.com", "amazon.com",
    "canva.com", "figma.com", "notion.so", "airtable.com"
]

SERP_WEAK_COMPETITORS = [
    "reddit.com", "quora.com", "stackoverflow.com", "medium.com",
    "dev.to", "hashnode.com", "blogger.com", "wordpress.com"
]

# ==================== 工具函数 ====================

def ensure_dirs():
    """确保所有必要的目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def log_execution(message: str, level: str = "INFO"):
    """执行日志记录"""
    import sys
    
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            message = message.encode('ascii', 'ignore').decode('ascii')
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}")
    except UnicodeEncodeError:
        message_ascii = message.encode('ascii', 'ignore').decode('ascii')
        print(f"[{timestamp}] [{level}] {message_ascii}")

def load_seed_words(filepath: str = SEED_WORDS_FILE) -> List[str]:
    """从 words.md 加载种子词"""
    if not os.path.exists(filepath):
        log_execution(f"⚠️ {filepath} 不存在，使用默认种子词", "WARNING")
        return ["calculator", "generator", "converter"]
    
    seeds = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('序号'):
                continue
            
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    word = parts[1].strip()
                    import re
                    match = re.match(r'([A-Za-z]+)', word)
                    if match:
                        seeds.append(match.group(1).lower())
            elif ',' in line:
                word = line.split(',')[0].strip()
                if word and word.isalpha():
                    seeds.append(word.lower())
            elif line.isalpha():
                seeds.append(line.lower())
    
    seeds = list(dict.fromkeys(seeds))
    log_execution(f"✅ 加载了 {len(seeds)} 个种子词")
    return seeds

# ==================== Step 0: Google Autocomplete Mining ====================

def google_suggest(query: str, gl: str = "us") -> List[str]:
    """调用 Google Autocomplete API"""
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",
        "q": quote(query),
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

def alphabet_soup_mining(seed_word: str, gl: str = "us") -> List[str]:
    """Alphabet Soup 全量挖词"""
    results = set()
    
    log_execution(f"🔍 挖掘: {seed_word}")
    
    # 基础查询
    results.update(google_suggest(seed_word, gl))
    time.sleep(0.5)
    
    # 后缀空格
    results.update(google_suggest(f"{seed_word} ", gl))
    time.sleep(0.5)
    
    # 前缀 A-Z（采样，加快速度）
    for c in "abcdefghijklmnopqrstuvwxyz"[::2]:  # 每隔一个字母
        suggestions = google_suggest(f"{c} {seed_word}", gl)
        results.update(suggestions)
        time.sleep(0.2)
    
    # 后缀 A-Z（采样）
    for c in "abcdefghijklmnopqrstuvwxyz"[::2]:
        suggestions = google_suggest(f"{seed_word} {c}", gl)
        results.update(suggestions)
        time.sleep(0.2)
    
    filtered = [s for s in results if seed_word.lower() in s.lower()]
    log_execution(f"✅ 发现 {len(filtered)} 个关键词")
    return filtered

def batch_mine_all_seeds(seed_words: List[str], max_seeds: int = None) -> pd.DataFrame:
    """批量挖掘（不再限制数量）"""
    all_keywords = []
    
    # 默认跑全部种子词
    if max_seeds is None:
        max_seeds = len(seed_words)
    
    log_execution(f"🔍 开始挖掘 {max_seeds} 个种子词...")
    
    for idx, seed in enumerate(seed_words[:max_seeds], 1):
        log_execution(f"[{idx}/{max_seeds}] 挖掘: {seed}")
        suggestions = alphabet_soup_mining(seed)
        
        for s in suggestions:
            all_keywords.append({
                "seed": seed,
                "keyword": s,
                "word_count": len(s.split()),
                "source": "google_suggest"
            })
        
        time.sleep(1)
    
    df = pd.DataFrame(all_keywords)
    df = df.drop_duplicates(subset=['keyword'])
    
    csv_path = os.path.join(DATA_DIR, "step0_suggest_keywords.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    log_execution(f"📊 Step 0 完成：{len(df)} 个关键词（来自 {max_seeds} 个种子）")
    return df

# ==================== Step 1: Google Trends + Related Queries ====================

def harvest_trends_deep(seed_word: str, geo: str = "US") -> pd.DataFrame:
    """深度挖掘 Trends（包括二级 Related Queries）"""
    try:
        from pytrends.request import TrendReq
        
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([seed_word], timeframe='now 7-d', geo=geo)
        
        related = pytrends.related_queries()
        
        all_queries = []
        
        if seed_word in related:
            # 一级 Rising
            if related[seed_word]['rising'] is not None:
                rising_df = related[seed_word]['rising']
                for _, row in rising_df.iterrows():
                    all_queries.append({
                        "keyword": row['query'],
                        "value": row['value'],
                        "seed": seed_word,
                        "level": "1st",
                        "source": "trends_rising"
                    })
                    
                    # 🔥 二级深挖：对每个飙升词再查一次
                    if len(all_queries) < 20:  # 限制深挖数量
                        try:
                            pytrends.build_payload([row['query']], timeframe='now 7-d', geo=geo)
                            sub_related = pytrends.related_queries()
                            
                            if row['query'] in sub_related and sub_related[row['query']]['rising'] is not None:
                                sub_rising = sub_related[row['query']]['rising']
                                for _, sub_row in sub_rising.head(5).iterrows():
                                    all_queries.append({
                                        "keyword": sub_row['query'],
                                        "value": sub_row['value'],
                                        "seed": seed_word,
                                        "level": "2nd",
                                        "source": "trends_rising_deep"
                                    })
                            
                            time.sleep(2)
                        except:
                            pass
        
        return pd.DataFrame(all_queries) if all_queries else pd.DataFrame()
        
    except ImportError:
        log_execution("❌ pytrends 未安装", "ERROR")
        return pd.DataFrame()
    except Exception as e:
        log_execution(f"❌ Trends 失败: {str(e)[:50]}", "ERROR")
        return pd.DataFrame()

def batch_harvest_trends(seed_words: List[str]) -> pd.DataFrame:
    """批量获取 Trends"""
    all_rising = []
    
    for seed in seed_words[:5]:  # 限制数量
        log_execution(f"🔥 Trends: {seed}")
        df = harvest_trends_deep(seed)
        if not df.empty:
            all_rising.append(df)
        time.sleep(4)
    
    if all_rising:
        combined = pd.concat(all_rising, ignore_index=True)
        csv_path = os.path.join(DATA_DIR, "step1_trends_deep.csv")
        combined.to_csv(csv_path, index=False, encoding='utf-8-sig')
        log_execution(f"📊 Step 1 完成：{len(combined)} 个飙升词（含二级）")
        return combined
    
    return pd.DataFrame()

# ==================== Step 2: GPTs Benchmark (必选) ====================

def compare_to_gpts_batch(keywords: List[str], batch_size: int = 3, max_retries: int = 3, delay: int = 6) -> pd.DataFrame:
    """批量对比 GPTs（保守优化版 - 避免限频）
    
    参数：
        batch_size: 每批数量（默认 3，非常保守）
        max_retries: 最大重试次数（默认 3）
        delay: 每次请求后延迟秒数（默认 6 秒，非常保守）
    """
    try:
        from pytrends.request import TrendReq
        
        results = []
        failed_keywords = []
        
        log_execution(f"⚖️ 开始 GPTs 对比：{len(keywords)} 个词")
        log_execution(f"⏱️ 预计耗时：{len(keywords) * delay / 60:.1f} 分钟（每词 {delay} 秒）")
        
        # 分批处理（每批很小，避免限频）
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(keywords) + batch_size - 1) // batch_size
            
            log_execution(f"\n📦 批次 {batch_num}/{total_batches}：{len(batch)} 个词")
            
            # 每批重新创建 TrendReq 实例（避免 session 问题）
            pytrends = TrendReq(
                hl='en-US', 
                tz=360, 
                timeout=TRENDS_CONFIG["TIMEOUT"], 
                retries=2, 
                backoff_factor=1.0
            )
            
            for idx, kw in enumerate(batch, 1):
                log_execution(f"  [{i+idx}/{len(keywords)}] 对比: {kw}")
                
                success = False
                for attempt in range(max_retries):
                    try:
                        kw_list = [kw, "GPTs"]
                        pytrends.build_payload(kw_list, timeframe='now 7-d', geo='US')
                        df = pytrends.interest_over_time()
                        
                        if df is not None and not df.empty:
                            if "isPartial" in df.columns:
                                df = df.drop(columns=["isPartial"])
                            
                            kw_avg = float(df[kw].mean())
                            gpts_avg = float(df["GPTs"].mean())
                            
                            ratio = (kw_avg / gpts_avg) if gpts_avg > 0 else 0
                            growth = float(df[kw].iloc[-1] - df[kw].iloc[0])
                            
                            results.append({
                                "keyword": kw,
                                "kw_avg": round(kw_avg, 2),
                                "gpts_avg": round(gpts_avg, 2),
                                "avg_ratio": round(ratio, 3),
                                "growth": round(growth, 2),
                                "is_rising": growth > 0
                            })
                            success = True
                            log_execution(f"    ✅ 成功 (比率: {ratio:.1%})")
                            break
                        
                    except Exception as e:
                        if attempt < max_retries - 1:
                            wait_time = 8 * (attempt + 1)  # 更长的重试等待
                            log_execution(f"    ⚠️ 重试 {attempt+1}/{max_retries}，等待 {wait_time}s...", "WARNING")
                            time.sleep(wait_time)
                        else:
                            log_execution(f"    ❌ 失败: {str(e)[:40]}", "WARNING")
                            failed_keywords.append(kw)
                
                if success:
                    # 每次成功后等待（保守策略）
                    time.sleep(delay)
            
            # 批次间等待更长时间（避免限频）
            if i + batch_size < len(keywords):
                wait_time = TRENDS_CONFIG["DELAY_BETWEEN_BATCHES"]
                log_execution(f"  ⏸️ 批次完成，等待 {wait_time} 秒避免限频...")
                time.sleep(wait_time)
        
        # 输出失败统计
        if failed_keywords:
            log_execution(f"⚠️ {len(failed_keywords)} 个词对比失败", "WARNING")
        
        df_result = pd.DataFrame(results)
        if not df_result.empty:
            csv_path = os.path.join(DATA_DIR, "step2_gpts_comparison.csv")
            df_result.to_csv(csv_path, index=False, encoding='utf-8-sig')
            log_execution(f"📊 Step 2 完成：对比了 {len(df_result)}/{len(keywords)} 个词")
        
        return df_result
        
    except Exception as e:
        log_execution(f"❌ GPTs 对比失败: {e}", "ERROR")
        return pd.DataFrame()

# ==================== Step 3: SERP Competition Analysis (Playwright) ====================

def analyze_serp_with_playwright(keyword: str, headless: bool = True) -> Dict:
    """🔥 核心升级：使用 Playwright 分析 SERP 竞争度"""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            url = f"https://www.google.com/search?q={quote(keyword)}&num=10"
            page.goto(url, timeout=15000)
            time.sleep(2)
            
            # 提取前 10 个自然搜索结果
            results = page.query_selector_all('div.g')
            
            if not results:
                browser.close()
                return {"competition": "🟢 ZERO", "reason": "无搜索结果", "top3": []}
            
            top_domains = []
            for result in results[:3]:  # 只看前 3 名
                link_el = result.query_selector('a')
                if link_el:
                    href = link_el.get_attribute('href') or ""
                    # 提取域名
                    import re
                    match = re.search(r'https?://([^/]+)', href)
                    if match:
                        domain = match.group(1).replace('www.', '')
                        top_domains.append(domain)
            
            browser.close()
            
            # 🎯 降维打击分析
            has_giant = any(domain in top_domains for domain in SERP_GIANTS)
            has_weak = any(domain in top_domains for domain in SERP_WEAK_COMPETITORS)
            
            if has_weak and not has_giant:
                return {
                    "competition": "🟢 WEAK",
                    "reason": f"前3名有论坛/博客: {', '.join(top_domains[:3])}",
                    "top3": top_domains[:3],
                    "降维打击": True
                }
            elif has_giant:
                return {
                    "competition": "🔴 GIANT",
                    "reason": f"大厂占据: {', '.join(top_domains[:3])}",
                    "top3": top_domains[:3],
                    "降维打击": False
                }
            else:
                return {
                    "competition": "🟡 MEDIUM",
                    "reason": f"中等竞争: {', '.join(top_domains[:3])}",
                    "top3": top_domains[:3],
                    "降维打击": False
                }
        
    except ImportError:
        log_execution("⚠️ Playwright 未安装，使用简化分析", "WARNING")
        return analyze_serp_simple(keyword)
    except Exception as e:
        log_execution(f"SERP 分析失败 {keyword}: {str(e)[:30]}", "WARNING")
        return analyze_serp_simple(keyword)

def analyze_serp_simple(keyword: str) -> Dict:
    """简化版竞争分析（不用 Playwright）"""
    keyword_lower = keyword.lower()
    
    if any(word in keyword_lower for word in ["free", "online", "simple"]):
        return {"competition": "🟡 MEDIUM", "reason": "常见修饰词", "降维打击": False}
    elif len(keyword.split()) >= 4:
        return {"competition": "🟢 LOW", "reason": "长尾词（4+词）", "降维打击": True}
    elif any(word in keyword_lower for word in PAIN_TRIGGERS["strong"]):
        return {"competition": "🟢 LOW", "reason": "痛点词", "降维打击": True}
    else:
        return {"competition": "🟡 MEDIUM-LOW", "reason": "默认评估", "降维打击": False}

def batch_analyze_serp(keywords: List[str], use_playwright: bool = False) -> pd.DataFrame:
    """批量 SERP 分析"""
    results = []
    
    for kw in keywords[:30]:  # 限制数量（Playwright 很慢）
        log_execution(f"🎯 SERP: {kw}")
        
        if use_playwright:
            serp_result = analyze_serp_with_playwright(kw)
            time.sleep(3)  # 防止被封
        else:
            serp_result = analyze_serp_simple(kw)
        
        results.append({
            "keyword": kw,
            "competition": serp_result["competition"],
            "reason": serp_result["reason"],
            "降维打击": serp_result.get("降维打击", False)
        })
    
    df = pd.DataFrame(results)
    csv_path = os.path.join(DATA_DIR, "step3_serp_analysis.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    log_execution(f"📊 Step 3 完成：分析了 {len(df)} 个词")
    return df

# ==================== Step 4: Intent Scoring ====================

def calculate_intent_score(keyword: str) -> Dict:
    """意图评分（优化版）"""
    keyword_lower = keyword.lower()
    score = 0
    signals = []
    
    # 强痛点 +40（提高权重）
    for trigger in PAIN_TRIGGERS["strong"]:
        if trigger in keyword_lower:
            score += 40
            signals.append(f"痛点:{trigger}")
            break
    
    # 工具信号 +30
    for trigger in PAIN_TRIGGERS["tool"]:
        if trigger in keyword_lower:
            score += 30
            signals.append(f"工具:{trigger}")
            break
    
    # 对比需求 +25
    for trigger in PAIN_TRIGGERS["comparison"]:
        if trigger in keyword_lower:
            score += 25
            signals.append(f"对比:{trigger}")
            break
    
    # B2B +25
    for trigger in PAIN_TRIGGERS["b2b"]:
        if trigger in keyword_lower:
            score += 25
            signals.append(f"B2B:{trigger}")
            break
    
    # 速度 +20
    for trigger in PAIN_TRIGGERS["speed"]:
        if trigger in keyword_lower:
            score += 20
            signals.append(f"速度:{trigger}")
            break
    
    # 长尾词 +15
    word_count = len(keyword.split())
    if 2 <= word_count <= 4:
        score += 15
        signals.append(f"长尾:{word_count}词")
    
    return {
        "keyword": keyword,
        "intent_score": min(score, 100),
        "signals": ", ".join(signals) if signals else "无信号"
    }

# ==================== Step 4.5: User Intent Mining (新增) ====================

def detect_user_intent(keyword: str) -> Dict:
    """深挖用户意图（不只是信号，而是用户真正想做什么）"""
    keyword_lower = keyword.lower()
    
    detected_intents = []
    intent_details = []
    
    # 遍历意图模式
    for intent_type, patterns in USER_INTENT_PATTERNS.items():
        for pattern in patterns:
            if pattern in keyword_lower:
                detected_intents.append(intent_type)
                intent_details.append(f"{intent_type}({pattern})")
                break
    
    # 去重
    detected_intents = list(dict.fromkeys(detected_intents))
    
    # 推断用户真正意图
    if not detected_intents:
        user_goal = "未知意图（可能是信息查询）"
        intent_clarity = "低"
    elif len(detected_intents) == 1:
        intent_map = {
            "calculate": "用户想计算某个数值",
            "convert": "用户想转换单位/格式",
            "generate": "用户想自动生成内容",
            "check": "用户想验证/检查某事",
            "compare": "用户想对比两个选项",
            "download": "用户想下载资源",
            "edit": "用户想编辑/修改内容",
            "analyze": "用户想分析数据",
            "track": "用户想追踪/监控",
            "search": "用户想查找信息"
        }
        user_goal = intent_map.get(detected_intents[0], "执行具体操作")
        intent_clarity = "高"
    else:
        user_goal = f"复合需求：{' + '.join(detected_intents)}"
        intent_clarity = "中"
    
    return {
        "keyword": keyword,
        "user_intent": ", ".join(detected_intents) if detected_intents else "无明确意图",
        "intent_details": ", ".join(intent_details) if intent_details else "无",
        "user_goal": user_goal,
        "intent_clarity": intent_clarity
    }

# ==================== Step 5: Final Scoring (优化版) ====================

def calculate_final_score_ultimate(row: pd.Series) -> Dict:
    """终极评分算法（更容易出现"立即做"）"""
    
    # 1. Trend Score（优化：即使没有 GPTs 数据也给基础分）
    ratio = row.get('avg_ratio', 0)
    growth = row.get('growth', 0)
    
    if ratio >= THRESHOLDS["GREAT_GPTS_RATIO"] and growth > 0:
        trend_score = 100
    elif ratio >= THRESHOLDS["GOOD_GPTS_RATIO"] and growth > 5:
        trend_score = 85
    elif ratio >= THRESHOLDS["MIN_GPTS_RATIO"]:
        trend_score = 70  # 提高基础分
    else:
        trend_score = 50  # 即使没数据也给 50 分
    
    # 2. Intent Score
    intent_score = row.get('intent_score', 0)
    
    # 3. Competition Score（优化：降维打击直接加分）
    competition = row.get('competition', '')
    降维打击 = row.get('降维打击', False)
    
    if 降维打击:
        comp_score = 100  # 降维打击 = 满分
    elif '🟢' in competition or 'WEAK' in competition or 'LOW' in competition:
        comp_score = 90
    elif '🟡' in competition:
        comp_score = 60
    else:
        comp_score = 30
    
    # 4. Buildability Score
    keyword_lower = row.get('keyword', '').lower()
    tool_words = ["calculator", "generator", "converter", "maker", "checker"]
    
    if any(tool in keyword_lower for tool in tool_words):
        build_score = 100
    elif "online" in keyword_lower or "free" in keyword_lower:
        build_score = 85
    else:
        build_score = 70
    
    # 综合评分（权重优化）
    final_score = (
        trend_score * 0.25 +      # 降低 Trend 权重
        intent_score * 0.35 +     # 提高 Intent 权重
        comp_score * 0.25 +       # 提高竞争度权重
        build_score * 0.15
    )
    
    # 决策
    if final_score >= THRESHOLDS["BUILD_NOW"]:
        decision = "🔴 BUILD NOW"
    elif final_score >= THRESHOLDS["WATCH"]:
        decision = "🟡 WATCH"
    else:
        decision = "❌ DROP"
    
    return {
        "trend_score": trend_score,
        "competition_score": comp_score,
        "buildability_score": build_score,
        "final_score": round(final_score, 1),
        "decision": decision
    }

# ==================== Main Pipeline ====================

def run_ultimate_hunter(
    seed_words: List[str],
    enable_trends: bool = True,
    enable_playwright: bool = False,  # Playwright 很慢，默认关闭
    max_candidates: int = 100
) -> tuple:
    """运行终极版 Profit Hunter"""
    
    ensure_dirs()
    
    log_execution("=" * 60)
    log_execution("💎 Profit Hunter ULTIMATE 启动")
    log_execution("=" * 60)
    
    # Step 0: Mine
    log_execution("\n🔍 Step 0: Alphabet Soup 挖词...")
    df_suggest = batch_mine_all_seeds(seed_words, max_seeds=None)  # None = 跑全部
    
    all_candidates = df_suggest.copy()
    
    # Step 1: Trends Deep Dive
    if enable_trends:
        log_execution("\n🔥 Step 1: Trends 深度挖掘（含二级）...")
        df_trends = batch_harvest_trends(seed_words)
        if not df_trends.empty:
            df_trends_renamed = df_trends.rename(columns={'keyword': 'keyword'})
            all_candidates = pd.concat([
                all_candidates,
                df_trends_renamed[['keyword', 'seed', 'source']]
            ], ignore_index=True).drop_duplicates(subset=['keyword'])
    
    # 限制候选词数量
    if len(all_candidates) > max_candidates:
        all_candidates = all_candidates.sample(max_candidates)
    
    # Step 2: GPTs Benchmark (必选)
    log_execution(f"\n⚖️ Step 2: GPTs 基准对比（{len(all_candidates)} 个词）...")
    df_gpts = compare_to_gpts_batch(
        all_candidates['keyword'].tolist(),
        batch_size=TRENDS_CONFIG["BATCH_SIZE"],
        max_retries=TRENDS_CONFIG["MAX_RETRIES"],
        delay=TRENDS_CONFIG["DELAY_PER_REQUEST"]
    )
    
    if not df_gpts.empty:
        all_candidates = all_candidates.merge(
            df_gpts,
            on='keyword',
            how='left'
        )
    else:
        # 默认值
        all_candidates['avg_ratio'] = 0.05
        all_candidates['growth'] = 0
    
    # Step 3: SERP Analysis
    log_execution("\n🎯 Step 3: SERP 竞争分析...")
    df_serp = batch_analyze_serp(all_candidates['keyword'].tolist(), use_playwright=enable_playwright)
    all_candidates = all_candidates.merge(df_serp, on='keyword', how='left')
    
    # Step 4: Intent Scoring
    log_execution("\n🧠 Step 4: 意图评分...")
    intent_results = [calculate_intent_score(kw) for kw in all_candidates['keyword']]
    df_intent = pd.DataFrame(intent_results)
    all_candidates = all_candidates.merge(df_intent, on='keyword', how='left')
    
    # Step 4.5: User Intent Mining（新增：深挖用户意图）
    log_execution("\n💡 Step 4.5: 用户意图深挖...")
    user_intent_results = [detect_user_intent(kw) for kw in all_candidates['keyword']]
    df_user_intent = pd.DataFrame(user_intent_results)
    all_candidates = all_candidates.merge(df_user_intent, on='keyword', how='left')
    
    # Step 5: Final Scoring
    log_execution("\n📊 Step 5: 终极评分...")
    scores = all_candidates.apply(lambda row: pd.Series(calculate_final_score_ultimate(row)), axis=1)
    final_df = pd.concat([all_candidates, scores], axis=1)
    final_df = final_df.sort_values("final_score", ascending=False)
    
    # 保存
    csv_path = os.path.join(DATA_DIR, "ultimate_final_results.csv")
    final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # 统计
    stats = {
        'total': len(final_df),
        'build_now': len(final_df[final_df['decision'] == '🔴 BUILD NOW']),
        'watch': len(final_df[final_df['decision'] == '🟡 WATCH']),
        'avg_score': final_df['final_score'].mean()
    }
    
    log_execution("\n" + "=" * 60)
    log_execution("✅ ULTIMATE 完成！")
    log_execution(f"📊 总候选词: {stats['total']}")
    log_execution(f"🔴 立即做: {stats['build_now']}")
    log_execution(f"🟡 观察: {stats['watch']}")
    log_execution(f"📈 平均分: {stats['avg_score']:.1f}")
    log_execution("=" * 60)
    
    return csv_path, final_df, stats

# ==================== CLI ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Profit Hunter ULTIMATE')
    parser.add_argument('--trends', action='store_true', help='启用 Trends 深度挖掘')
    parser.add_argument('--playwright', action='store_true', help='启用 Playwright SERP 分析（慢）')
    parser.add_argument('--max', type=int, default=50, help='最大候选词数量')
    
    args = parser.parse_args()
    
    seeds = load_seed_words()
    
    csv_path, final_df, stats = run_ultimate_hunter(
        seed_words=seeds,
        enable_trends=args.trends,
        enable_playwright=args.playwright,
        max_candidates=args.max
    )
    
    # 显示 Top 10
    print("\n" + "=" * 60)
    print("🔥 Top 10 推荐（按评分排序）：")
    print("=" * 60)
    
    top10 = final_df.head(10)
    for idx, (_, row) in enumerate(top10.iterrows(), 1):
        print(f"\n{idx}. {row['keyword']}")
        print(f"   最终评分: {row['final_score']}")
        print(f"   决策: {row['decision']}")
        print(f"   竞争度: {row['competition']}")
        if row.get('降维打击'):
            print(f"   💎 降维打击机会！")

if __name__ == "__main__":
    main()
