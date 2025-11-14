#!/usr/bin/env python3
"""
测试长度自动调整功能
"""

import sys
sys.path.insert(0, '.')

from callaway_13field_processor import adjust_title_length

def test_length_adjustment():
    """测试各种长度的标题调整"""

    test_cases = [
        # 太长的标题
        "25秋冬Le Coq公鸡乐卡克高尔夫男士保暖棉服可拆卸轻便夹克",  # 31字，需要减1字
        "25秋冬卡拉威高尔夫男士时尚保暖舒适弹力全拉链夹克",      # 30字，刚好
        "25秋冬卡拉威高尔夫男士新款时尚保暖舒适夹克",             # 29字，刚好

        # 太短的标题
        "25秋冬卡拉威高尔夫男士保暖夹克",                         # 17字，需要加9字
        "25秋冬卡拉威高尔夫男士弹力夹克",                         # 17字，需要加9字
        "25秋冬卡拉威高尔夫男士防泼水夹克",                      # 18字，需要加8字
    ]

    print("=== 标题长度自动调整测试 ===")
    print()

    for i, title in enumerate(test_cases, 1):
        original_length = len(title)
        adjusted_title = adjust_title_length(title)
        adjusted_length = len(adjusted_title)

        print(f"测试 {i}:")
        print(f"  原标题: {title}")
        print(f"  原长度: {original_length}字")
        print(f"  调整后: {adjusted_title}")
        print(f"  调整长度: {adjusted_length}字")

        if 26 <= adjusted_length <= 30:
            status = "✅ 成功"
        else:
            status = "❌ 失败"
        print(f"  结果: {status}")
        print()

if __name__ == "__main__":
    test_length_adjustment()