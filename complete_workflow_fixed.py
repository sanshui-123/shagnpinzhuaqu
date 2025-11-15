#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版完整三步流程：真实URL抓取→处理→飞书同步
基于test_full_pipeline_one_url.py的成功逻辑，修复字段映射问题
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
        '--output', 'step2_processed_fixed.json'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ 第二步失败: {result.stderr}")
        return None

    print("✅ 第二步完成: step2_processed_fixed.json")
    return 'step2_processed_fixed.json'

def step3_sync(input_file):
    """第三步：同步到飞书（修复版）"""
    print(f"\n📤 第三步：同步到飞书")
    print("=" * 50)
    print(f"输入文件: {input_file}")

    # 读取处理后的数据
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

    # 获取access_token
    print("🔄 获取飞书access_token...")
    access_token = get_feishu_access_token()
    if not access_token:
        print("❌ 获取access_token失败")
        return False
    print(f"✅ access_token获取成功")

    # 创建飞书记录（使用正确的字段映射）
    print("📋 准备写入飞书的数据...")
    record = create_feishu_record_fixed(data)
    print("✅ 飞书记录格式准备完成")

    # 调试：打印将要发送的数据
    print("🔍 将要发送的字段:")
    for key, value in record["fields"].items():
        print(f"   {key}: {value[:50] if value else '空'}{'...' if value and len(value) > 50 else ''}")

    # 执行飞书写入
    print("🔄 执行飞书API写入...")
    success = write_to_feishu_fixed(access_token, [record])

    if success:
        print("✅ 飞书数据同步成功！")
        return True
    else:
        print("❌ 飞书数据同步失败")
        return False

def get_feishu_access_token():
    """获取飞书access_token"""
    import requests

    app_id = os.environ.get('FEISHU_APP_ID', 'cli_a871862032b2900d')
    app_secret = os.environ.get('FEISHU_APP_SECRET', 'jC6o0dMadbyAh8AJHvNljghoUeBFaP2h')

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                return data.get('tenant_access_token')
            else:
                print(f"获取token失败: {data}")
                return None
        else:
            print(f"请求失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def create_feishu_record_fixed(processed_data):
    """创建飞书记录格式（修复版 - 只使用正确的字段名）"""
    return {
        "fields": {
            "商品链接": processed_data.get('商品链接', ''),
            "商品ID": processed_data.get('商品ID', ''),
            "商品标题": processed_data.get('生成标题', ''),
            "品牌名": processed_data.get('品牌', ''),
            "价格": processed_data.get('价格', ''),
            "性别": processed_data.get('性别', ''),
            "衣服分类": processed_data.get('服装类型', ''),
            "图片URL": processed_data.get('图片链接', ''),
            "颜色": processed_data.get('颜色', ''),
            "尺码": processed_data.get('尺寸', ''),
            "详情页文字": processed_data.get('描述翻译', ''),
            "尺码表": ""  # 暂时为空
        }
    }

def write_to_feishu_fixed(access_token, records):
    """写入数据到飞书多维表格（修复版）"""
    import requests

    app_token = os.environ.get('FEISHU_APP_TOKEN', 'OlU0bHLUVa6LSLsTkn2cPUHunZa')
    table_id = os.environ.get('FEISHU_TABLE_ID', 'tblhBepAOlCyhfoN')

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "CallawayJP Fixed Pipeline/1.0"
    }

    payload = {
        "records": records
    }

    # 添加重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🔄 尝试 {attempt + 1}/{max_retries}: 调用飞书API...")

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
                verify=True
            )

            print(f"📊 飞书API响应状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📋 飞书API响应: {data}")

                if data.get('code') == 0:
                    record_results = data.get('data', {}).get('records', [])
                    success_count = len(record_results)
                    print(f"✅ 成功创建 {success_count} 条记录")

                    # 显示创建的记录ID
                    for i, record in enumerate(record_results):
                        record_id = record.get('record_id', 'N/A')
                        print(f"   记录 {i+1}: {record_id}")

                    return success_count > 0
                else:
                    print(f"❌ 飞书API返回错误: {data}")
                    return False
            else:
                print(f"❌ 飞书API请求失败: {response.status_code}")
                print(f"错误详情: {response.text}")
                return False

        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ 连接错误 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                print("❌ 所有重试都失败")
                return False

        except Exception as e:
            print(f"❌ 飞书API调用异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                return False

def main():
    """主函数"""
    # 加载环境变量
    load_env()

    # 测试URL
    test_url = "https://store.descente.co.jp/commodity/SDSC0140D/LE1872AM012332/"

    print("🚀 开始修复版完整三步流程")
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
        print("🎉 修复版完整流程成功！数据已同步到飞书")
    else:
        print("⚠️ 修复版完整流程部分成功，数据已处理但飞书同步可能失败")

    print("=" * 80)
    return step3_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)