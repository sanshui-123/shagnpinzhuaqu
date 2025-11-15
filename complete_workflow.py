#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整三步流程：真实URL抓取→处理→飞书同步
真正能工作的完整流程
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

def load_env():
    """加载环境变量"""
    env_file = Path("callaway.env")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip()
    print("✅ 已加载环境变量")

def step1_scrape(url):
    """第一步：抓取数据"""
    print("\n🔍 第一步：抓取数据")
    print("=" * 50)

    cmd = [
        'node',
        'single_url_fixed_processor.js',
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd='scripts/multi_brand/brands/lecoqgolf')

    if result.returncode != 0:
        print(f"❌ 第一步失败: {result.stderr}")
        return None

    # 查找生成的JSON文件
    import glob
    json_files = glob.glob('scripts/multi_brand/brands/lecoqgolf/single_url_fixed_*.json')
    if json_files:
        latest_file = max(json_files, key=os.path.getctime)
        print(f"✅ 第一步完成: {latest_file}")
        return latest_file
    else:
        print("❌ 未找到抓取结果文件")
        return None

def step2_process(input_file):
    """第二步：处理数据"""
    print(f"\n🔄 第二步：处理数据")
    print("=" * 50)
    print(f"输入文件: {input_file}")

    cmd = [
        'python3',
        'callaway_13field_processor.py',
        '--input', input_file,
        '--output', 'step2_processed.json'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ 第二步失败: {result.stderr}")
        return None

    print("✅ 第二步完成: step2_processed.json")
    return 'step2_processed.json'

def step3_sync(input_file):
    """第三步：同步到飞书"""
    print(f"\n📤 第三步：同步到飞书")
    print("=" * 50)
    print(f"输入文件: {input_file}")

    # 设置环境变量
    env_vars = {
        'FEISHU_APP_ID': 'cli_a871862032b2900d',
        'FEISHU_APP_SECRET': 'jC6o0dMadbyAh8AJHvNljghoUeBFaP2h',
        'FEISHU_APP_TOKEN': 'OlU0bHLUVa6LSLsTkn2cPUHunZa',
        'FEISHU_TABLE_ID': 'tblhBepAOlCyhfoN'
    }

    cmd = [
        'python3',
        'step3_feishu_sync.py',
        '--input', input_file
    ]

    # 使用环境变量运行
    env = os.environ.copy()
    env.update(env_vars)

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    print("📋 第三步执行结果:")
    print(result.stdout)
    if result.stderr:
        print("❌ 错误信息:")
        print(result.stderr)

    return result.returncode == 0

def main():
    """主函数"""
    # 加载环境变量
    load_env()

    # 测试URL
    test_url = "https://store.descente.co.jp/commodity/SDSC0140D/LE1872AM012332/"

    print("🚀 开始完整三步流程")
    print(f"🎯 目标URL: {test_url}")
    print("=" * 80)

    # 第一步：抓取
    step1_file = step1_scrape(test_url)
    if not step1_file:
        print("❌ 流程终止：第一步失败")
        return False

    # 第二步：处理
    step2_file = step2_process(step1_file)
    if not step2_file:
        print("❌ 流程终止：第二步失败")
        return False

    # 第三步：同步
    step3_success = step3_sync(step2_file)

    print("\n" + "=" * 80)
    if step3_success:
        print("🎉 完整流程成功！数据已同步到飞书")
    else:
        print("⚠️ 完整流程部分成功，数据已处理但飞书同步可能失败")

    print("=" * 80)
    return step3_success

if __name__ == "__main__":
    main()