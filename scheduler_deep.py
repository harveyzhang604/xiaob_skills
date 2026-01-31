#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕒 Profit Hunter Scheduler - 深度分析调度器
============================================

运行策略：
- 每天4次运行
- 每次运行1小时（深度分析）
- 充分利用每分钟50万token限制
- 运行时间：00:00, 06:00, 12:00, 18:00

作者：AI Profit Hunter Team
版本：2.0
日期：2026-01-30
"""

import schedule
import time
import os
import subprocess
from datetime import datetime

def log_execution(message: str):
    """日志记录"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_ultimate_analysis():
    """运行终极分析（1小时深度版本）"""
    log_execution("=" * 60)
    log_execution("🚀 开始深度分析运行...")
    log_execution("=" * 60)
    
    try:
        # Step 1: 运行基础挖掘（30分钟）
        log_execution("📍 Step 1: 基础关键词挖掘（预计30分钟）")
        subprocess.run([
            "python", "profit_hunter_ultimate.py",
            "--trends",        # 启用Trends深度挖掘
            "--max", "100"     # 挖掘100个候选词
        ], check=True)
        
        log_execution("✅ Step 1 完成")
        
        # Step 2: 深度需求验证（30分钟）
        log_execution("📍 Step 2: 深度需求验证（预计30分钟）")
        
        # 找到最新的结果文件
        latest_file = max(
            [f for f in os.listdir("data") if f.startswith("ultimate_final_results")],
            key=lambda x: os.path.getctime(os.path.join("data", x))
        )
        
        subprocess.run([
            "python", "profit_hunter_deep_validation.py",
            "--input", f"data/{latest_file}",
            "--max", "30"      # 验证Top 30个关键词
        ], check=True)
        
        log_execution("✅ Step 2 完成")
        
        log_execution("=" * 60)
        log_execution("✅ 本次深度分析运行完成！")
        log_execution("=" * 60)
        
    except Exception as e:
        log_execution(f"❌ 运行失败: {str(e)}")

def schedule_daily_runs():
    """设置每天4次的运行计划"""
    # 每天4次：00:00, 06:00, 12:00, 18:00
    schedule.every().day.at("00:00").do(run_ultimate_analysis)
    schedule.every().day.at("06:00").do(run_ultimate_analysis)
    schedule.every().day.at("12:00").do(run_ultimate_analysis)
    schedule.every().day.at("18:00").do(run_ultimate_analysis)
    
    log_execution("📅 调度器已启动！运行时间：")
    log_execution("   • 00:00 (深夜)")
    log_execution("   • 06:00 (早晨)")
    log_execution("   • 12:00 (中午)")
    log_execution("   • 18:00 (傍晚)")
    log_execution("")
    log_execution("⏰ 等待下次运行...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次

def run_now():
    """立即运行一次（测试用）"""
    log_execution("🧪 测试模式：立即运行一次")
    run_ultimate_analysis()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        # 立即运行一次（测试）
        run_now()
    else:
        # 启动定时调度
        schedule_daily_runs()
