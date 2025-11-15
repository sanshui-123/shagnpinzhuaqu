#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三步-only：批量同步已处理的数据到飞书
基于production_processor.py的已验证逻辑
"""

import os
import sys
import json
import time
import requests
import glob
from pathlib import Path
from datetime import datetime

# 加载环境变量
env_file = Path("callaway.env")
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value
    print("✅ 已加载callaway.env环境变量")
else:
    print("❌ 未找到callaway.env文件")
    sys.exit(1)

def load_processed_data(input_file=None):
    """加载已处理的数据文件"""
    try:
        if input_file:
            # 使用指定的文件
            if not os.path.exists(input_file):
                print(f"❌ 文件不存在: {input_file}")
                return None
            json_files = [input_file]
        else:
            # 自动查找最新的处理结果文件
            pattern = "step2_batch_processed_*.json"
            json_files = glob.glob(pattern)

            if not json_files:
                pattern = "batch_production_processed_*.json"
                json_files = glob.glob(pattern)

            if not json_files:
                print("❌ 未找到已处理的数据文件")
                print("   请先运行第二步处理，或指定具体的输入文件")
                return None

            # 按文件名排序，取最新的
            json_files.sort(reverse=True)

        print(f"✅ 找到 {len(json_files)} 个处理结果文件")

        # 使用第一个文件（最新的）
        data_file = json_files[0]
        print(f"📄 使用文件: {data_file}")

        with open(data_file, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)

        print(f"✅ 成功加载 {len(processed_data)} 条处理后的记录")
        return processed_data

    except Exception as e:
        print(f"❌ 加载处理数据失败: {e}")
        return None

def get_feishu_access_token(app_id: str, app_secret: str) -> str:
    """获取飞书access_token"""
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
                print(f"❌ 获取token失败: {data}")
                return None
        else:
            print(f"❌ 请求失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def create_feishu_record(processed_data: dict) -> dict:
    """创建飞书记录格式"""
    record = {
        "fields": {
            "商品链接": processed_data.get('商品链接', ''),
            "商品ID": processed_data.get('商品ID', ''),
            "商品标题": processed_data.get('生成标题', processed_data.get('productName', '')),
            "品牌名": processed_data.get('品牌名', ''),
            "价格": processed_data.get('价格', ''),
            "性别": processed_data.get('性别', ''),
            "衣服分类": processed_data.get('衣服分类', ''),
            "图片URL": processed_data.get('图片链接', ''),
            "颜色": processed_data.get('颜色', ''),
            "尺码": processed_data.get('尺码', ''),
            "详情页文字": processed_data.get('详情页文字', ''),
            "尺码表": processed_data.get('尺码表', '')
        }
    }
    return record

def write_to_feishu(access_token: str, app_token: str, table_id: str, records: list) -> bool:
    """写入数据到飞书多维表格"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {"records": records}
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    return True
                else:
                    print(f"❌ 飞书API返回错误: {data}")
                    if attempt == max_retries - 1:
                        return False
                    time.sleep(2)
            else:
                print(f"❌ 飞书API请求失败: {response.status_code}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(2)

        except Exception as e:
            print(f"❌ 飞书API调用异常 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2)

    return False

def batch_sync_to_feishu(processed_data_list):
    """批量同步到飞书"""
    print("\\n🔄 第三步：批量飞书数据同步")
    print("=" * 50)

    try:
        # 获取飞书配置
        app_id = os.environ.get('FEISHU_APP_ID')
        app_secret = os.environ.get('FEISHU_APP_SECRET')
        app_token = os.environ.get('FEISHU_APP_TOKEN')
        table_id = os.environ.get('FEISHU_TABLE_ID')

        if not all([app_id, app_secret, app_token, table_id]):
            print("❌ 飞书配置不完整")
            print("   FEISHU_APP_ID:", "✅" if app_id else "❌")
            print("   FEISHU_APP_SECRET:", "✅" if app_secret else "❌")
            print("   FEISHU_APP_TOKEN:", "✅" if app_token else "❌")
            print("   FEISHU_TABLE_ID:", "✅" if table_id else "❌")
            return False

        print("✅ 飞书配置验证完成")

        # 获取飞书access_token
        print("🔄 获取飞书access_token...")
        access_token = get_feishu_access_token(app_id, app_secret)
        if not access_token:
            print("❌ 获取飞书access_token失败")
            return False
        print("✅ 飞书access_token获取成功")

        # 准备飞书数据 - 批量处理
        print("📋 准备批量写入飞书的数据...")
        records = []
        for processed_data in processed_data_list:
            record = create_feishu_record(processed_data)
            records.append(record)

        print(f"✅ 飞书记录格式准备完成: {len(records)} 条记录")

        # 分批写入（飞书API限制每次最多500条）
        batch_size = 100
        total_success = 0
        total_failed = 0

        for i in range(0, len(records), batch_size):
            batch_records = records[i:i + batch_size]
            print(f"\\n🔄 写入批次 {i//batch_size + 1}/{(len(records)-1)//batch_size + 1}: {len(batch_records)} 条记录")

            success = write_to_feishu(access_token, app_token, table_id, batch_records)
            if success:
                total_success += len(batch_records)
                print(f"   ✅ 批次写入成功")
            else:
                total_failed += len(batch_records)
                print(f"   ❌ 批次写入失败")

            # 避免API限制
            time.sleep(1)

        print(f"\\n📊 飞书同步汇总:")
        print(f"   总记录数: {len(records)}")
        print(f"   成功同步: {total_success}")
        print(f"   同步失败: {total_failed}")
        print(f"   成功率: {total_success/len(records)*100:.1f}%")

        return total_failed == 0

    except Exception as e:
        print(f"❌ 飞书批量同步异常: {e}")
        return False

def save_sync_report(processed_data_list, success_count, failed_count, timestamp):
    """保存同步报告"""
    try:
        report = {
            "同步时间": timestamp,
            "总记录数": len(processed_data_list),
            "成功同步": success_count,
            "同步失败": failed_count,
            "成功率": f"{success_count/len(processed_data_list)*100:.1f}%" if processed_data_list else "0%",
            "产品ID列表": [item.get('商品ID', 'Unknown') for item in processed_data_list]
        }

        report_file = f"step3_sync_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"✅ 同步报告已保存: {report_file}")
        return report_file
    except Exception as e:
        print(f"⚠️ 保存同步报告失败: {e}")
        return None

def main():
    """主函数：批量同步已处理的数据到飞书（第三步-only）"""
    import argparse

    parser = argparse.ArgumentParser(description='第三步：批量同步到飞书')
    parser.add_argument('--input', '-i', type=str, help='指定输入的JSON文件路径')
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("🚀 第三步批量同步器：将处理后的数据同步到飞书")
    if args.input:
        print(f"📄 指定输入文件: {args.input}")
    else:
        print("📄 输入文件: 自动检测最新的处理结果")
    print("=" * 80)

    # 第一步：加载已处理的数据
    print("\\n🔄 第一步：加载已处理的数据")
    print("=" * 60)
    processed_data_list = load_processed_data(args.input)
    if not processed_data_list:
        print("❌ 流程终止：数据加载失败")
        return False

    # 第二步：批量同步到飞书
    print(f"\\n🔄 第二步：批量同步到飞书")
    print("=" * 60)
    success = batch_sync_to_feishu(processed_data_list)

    # 保存同步报告
    success_count = len(processed_data_list) if success else 0
    failed_count = 0 if success else len(processed_data_list)
    report_file = save_sync_report(processed_data_list, success_count, failed_count, timestamp)

    print("\\n" + "=" * 80)
    print("🎉 第三步批量同步完成！")
    print("=" * 80)

    # 最终结果汇总
    print("\\n📊 第三步同步结果汇总:")
    print(f"✅ 处理记录数: {len(processed_data_list)}")
    print(f"✅ 飞书同步: {'成功' if success else '失败'}")
    if report_file:
        print(f"✅ 同步报告: {report_file}")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)