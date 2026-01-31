@echo off
chcp 65001 >nul
echo ==========================================
echo 🚀 Profit Hunter LITE - 快速版
echo ==========================================
echo.
echo 📍 融合 Yuanbao Skills 的优点：
echo    ✅ DuckDuckGo SERP（避免限频）
echo    ✅ GPTs Benchmark 对比
echo    ✅ 加权意图评分系统
echo    ✅ 简化决策矩阵
echo.
echo 📊 预计运行时间：10-15分钟
echo.

pause

python profit_hunter_lite.py

if errorlevel 1 (
    echo.
    echo ❌ 运行失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 运行完成！
echo ==========================================
echo.
echo 📂 结果文件：
echo    • data\reports\profit_hunter_lite_*.html
echo.

pause
