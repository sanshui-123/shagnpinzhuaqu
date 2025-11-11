#!/bin/bash
cd /Users/sanshui/Desktop/CallawayJP

# 添加测试脚本
git add scripts/claude_title_test.py
git add scripts/debug_glm.py
git add scripts/direct_prompt_test.py
git add scripts/final_glm_test.py
git add scripts/simple_glm_test.py
git add scripts/test_claude_title.py
git add scripts/test_glm_no_ssl.py
git add scripts/test_ultra_simple.py
git add scripts/test_rule_based.py

# 添加新抓取的产品数据
git add results/product_details_R24298105_2025-11-11T04-01-37-774Z.json
git add results/product_details_R24298105_2025-11-11T03-40-06-962Z.json
git add results/product_details_R24298101_2025-11-11T04-02-15-311Z.json
git add results/product_details_R24298105_2025-11-11T04-00-34-725Z.json
git add results/product_details_C25215100_2025-11-11T05-36-14-841Z.json
git add results/product_details_C25215106_2025-11-11T04-36-38-135Z.json
git add results/product_details_C25215107_2025-11-11T11-48-11-701Z.json
git add results/product_details_C25215107_2025-11-11T12-01-04-795Z.json

# 添加测试结果相关的文件
git add test_detail_integration.py
git add test_field_generation.py
git add test_fields.py
git add tmp_single_product.json
git add single_test.json

echo "添加测试文件完成!"