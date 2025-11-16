#!/usr/bin/env python3
"""
Step 2: Python数据处理和AI改写
"""

import sys
import os
sys.path.append('/Users/sanshui/Desktop/CallawayJP')

import json
import subprocess
from pathlib import Path

def run_step2_processing():
    """执行Step 2处理"""
    print("🔄 Step 2: Python数据处理和AI改写...")

    # 设置环境变量
    os.environ['PYTHONPATH'] = '/Users/sanshui/Desktop/CallawayJP'
    os.environ['FEISHU_TABLE_ID'] = 'tblhBepAOlCyhfoN'

    # 切换到tongyong_feishu_update目录
    os.chdir('/Users/sanshui/Desktop/CallawayJP/tongyong_feishu_update')

    try:
        # 运行流式处理脚本
        result = subprocess.run([
            'python3', '-c', '''
import sys
sys.path.append("/Users/sanshui/Desktop/CallawayJP")

from tongyong_feishu_update.pipeline.streaming_orchestrator import StreamingUpdateOrchestrator
from tongyong_feishu_update.config.settings import Config

# 加载配置
config = Config()

# 创建流式处理器
orchestrator = StreamingUpdateOrchestrator(config)

# 处理单个文件
input_file = "/Users/sanshui/Desktop/CallawayJP/test_fixed_final.json"
output_file = "/Users/sanshui/Desktop/CallawayJP/step2_result.json"

print("🔄 开始流式处理...")
result = orchestrator.process_single_file(input_file, output_file, dry_run=True)

print("✅ Step 2 处理完成")
print(f"📊 处理结果: {result}")
'''
        ],
        capture_output=True,
        text=True,
        timeout=120
        )

        print(f"Step 2 输出:")
        print(result.stdout)

        if result.stderr:
            print(f"错误信息:")
            print(result.stderr)

        if result.returncode == 0:
            print("✅ Step 2 完成")
            return True
        else:
            print("❌ Step 2 失败")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Step 2 超时")
        return False
    except Exception as e:
        print(f"❌ Step 2 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始Step 2数据处理")
    success = run_step2_processing()

    if success:
        print("🎉 Step 2处理成功")
    else:
        print("❌ Step 2处理失败")