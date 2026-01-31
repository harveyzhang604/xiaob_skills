@echo off
chcp 65001 >nul
echo ==========================================
echo 🚀 Profit Hunter 深度分析 - 立即运行
echo ==========================================
echo.

echo 📍 运行模式：深度分析（约1小时）
echo 📊 分析内容：
echo    1. 关键词挖掘（100个候选词）
echo    2. Reddit痛点验证（Top 30）
echo    3. Google SERP分析
echo    4. 生成详细HTML报告
echo.

pause

echo.
echo 🔍 Step 1: 基础关键词挖掘...
python profit_hunter_ultimate.py --trends --max 100

if errorlevel 1 (
    echo ❌ Step 1 失败
    pause
    exit /b 1
)

echo.
echo ✅ Step 1 完成！
echo.

echo 🔍 Step 2: 深度需求验证...
python profit_hunter_deep_validation.py --input data\ultimate_final_results.csv --max 30

if errorlevel 1 (
    echo ❌ Step 2 失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo ✅ 全部完成！
echo ==========================================
echo.
echo 📂 结果文件：
echo    • data\ultimate_final_results.csv（基础挖掘结果）
echo    • data\validation\deep_validation_*.csv（验证结果）
echo    • data\reports\deep_validation_report_*.html（详细报告）
echo.

pause
