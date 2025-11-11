#!/bin/bash
cd /Users/sanshui/Desktop/CallawayJP

# 添加智能混合方案相关文件
echo "添加智能混合方案文件..."

git add HYBRID_TITLE_SOLUTION_SUMMARY.md
git add feishu_update/services/title_hybrid_v2.py
git add scripts/test_hybrid_title.py
git add scripts/test_rule_based.py
git add feishu_update/config/title_config.py

# 修改的文件
git add feishu_update/services/title_v6.py
git add scripts/test_title.py
git add callaway.env

echo "Git add 完成!"