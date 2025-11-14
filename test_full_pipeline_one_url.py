#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整流程测试：一个URL从抓取到飞书同步
测试真实的产品数据完整处理流程
"""

import os
import sys
import json
import time
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

sys.path.insert(0, '.')

from callaway_13field_processor import Callaway13FieldProcessor

def create_test_product():
    """基于真实URL创建测试产品数据"""

    # 模拟第一步抓取的结果（基于真实产品页面 - 修正为6个颜色）
    product_data = {
        'productId': 'LE1872EM012989',
        'productName': '【袖取り外し可能】ヒートナビ中わた2WAYブルゾン（武井壮着用）',
        'detailUrl': 'https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/',
        'priceText': '￥19,800',
        'brand': 'Le Coq Sportif Golf',

        # 产品详情 - 修正为正确的6个颜色
        'colors': [
            {'name': 'ネイビー', 'code': 'NV00'},      # 海军蓝
            {'name': 'ネイビー×グレー', 'code': 'NV01'}, # 海军蓝 x 灰色
            {'name': 'ブラック', 'code': 'BK00'},       # 黑色
            {'name': 'ブルー', 'code': 'BL00'},         # 蓝色
            {'name': 'グレー', 'code': 'GY00'},         # 灰色
            {'name': 'ベージュ', 'code': 'BG00'}        # 米色
        ],
        'sizes': ['S', 'M', 'L', 'LL', '3L'],
        'description': '保温性に優れた中綿入りブルゾン。袖は取り外し可能で、シーズンを通して活躍する2WAY仕様。ヒートナビ仕様で、体の冷えやすい部分を効果的に保温。アクティブなゴルフシーンをサポートする高機能アイテム。',
        'mainImage': 'https://store.descente.co.jp/images/lecoq/main.jpg',

        # 图片组 - 6个颜色组（暂时使用示例URL，实际应该从真实页面抓取）
        'imageGroups': [
            {
                'colorCode': 'NV00',
                'colorName': 'ネイビー',
                'images': [
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_NV00_1.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_NV00_2.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_NV00_3.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_NV00_4.jpg'
                ]
            },
            {
                'colorCode': 'NV01',
                'colorName': 'ネイビー×グレー',
                'images': [
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_NV01_1.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_NV01_2.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_NV01_3.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_NV01_4.jpg'
                ]
            },
            {
                'colorCode': 'BK00',
                'colorName': 'ブラック',
                'images': [
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BK00_1.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BK00_2.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BK00_3.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BK00_4.jpg'
                ]
            },
            {
                'colorCode': 'BL00',
                'colorName': 'ブルー',
                'images': [
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BL00_1.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BL00_2.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BL00_3.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BL00_4.jpg'
                ]
            },
            {
                'colorCode': 'GY00',
                'colorName': 'グレー',
                'images': [
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_GY00_1.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_GY00_2.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_GY00_3.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_GY00_4.jpg'
                ]
            },
            {
                'colorCode': 'BG00',
                'colorName': 'ベージュ',
                'images': [
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BG00_1.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BG00_2.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BG00_3.jpg',
                    'https://store.descente.co.jp/commodity/images/LE1872EM012989_BG00_4.jpg'
                ]
            }
        ]
    }

    return product_data

def step2_universal_processor(product_data):
    """第二步：通用字段改写处理器"""
    print("\n🔄 第二步：通用字段改写处理")
    print("=" * 60)

    try:
        # 初始化处理器
        processor = Callaway13FieldProcessor()
        print("✅ 通用处理器初始化完成")

        # 处理产品
        print(f"🔄 开始处理产品: {product_data['productName']}")
        processed_result = processor.process_product(product_data)

        if processed_result:
            print("✅ 第二步处理完成")
            return processed_result
        else:
            print("❌ 第二步处理失败")
            return None

    except Exception as e:
        print(f"❌ 第二步处理异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def step3_feishu_sync(processed_data):
    """第三步：飞书数据同步 - 真实API写入"""
    print("\n🔄 第三步：飞书数据同步")
    print("=" * 60)

    try:
        # 获取飞书配置
        app_id = os.environ.get('FEISHU_APP_ID')
        app_secret = os.environ.get('FEISHU_APP_SECRET')
        app_token = os.environ.get('FEISHU_APP_TOKEN')
        table_id = os.environ.get('FEISHU_TABLE_ID')

        if not all([app_id, app_secret, app_token, table_id]):
            print("❌ 飞书配置不完整")
            print(f"   FEISHU_APP_ID: {'已设置' if app_id else '未设置'}")
            print(f"   FEISHU_APP_SECRET: {'已设置' if app_secret else '未设置'}")
            print(f"   FEISHU_APP_TOKEN: {'已设置' if app_token else '未设置'}")
            print(f"   FEISHU_TABLE_ID: {'已设置' if table_id else '未设置'}")
            return False

        print("✅ 飞书配置验证完成")

        # 获取access_token
        print("🔄 获取飞书access_token...")
        access_token = get_feishu_access_token(app_id, app_secret)
        if not access_token:
            print("❌ 获取access_token失败")
            return False
        print(f"✅ access_token获取成功: {access_token[:20]}...")

        # 准备飞书数据
        print("📋 准备写入飞书的数据...")
        record = create_feishu_record(processed_data)
        print("✅ 飞书记录格式准备完成")

        # 执行飞书写入
        print("🔄 执行飞书API写入...")
        success = write_to_feishu(access_token, app_token, table_id, [record])

        if success:
            print("✅ 飞书数据同步成功！")
            return True
        else:
            print("❌ 飞书数据同步失败")
            return False

    except Exception as e:
        print(f"❌ 飞书同步异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_feishu_access_token(app_id: str, app_secret: str) -> str:
    """获取飞书access_token"""
    import requests

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

def create_feishu_record(processed_data: dict) -> dict:
    """创建飞书记录格式"""
    return {
        "fields": {
            "商品链接": processed_data.get('商品链接', ''),
            "商品ID": processed_data.get('商品ID', ''),
            "商品标题": processed_data.get('生成标题', ''),
            "品牌名": processed_data.get('品牌', ''),
            "价格": processed_data.get('价格', ''),
            "性别": processed_data.get('性别', ''),
            "衣服分类": processed_data.get('服装类型', ''),  # 修正字段名
            "图片URL": processed_data.get('图片链接', ''),
            "颜色": processed_data.get('颜色', ''),
            "尺码": processed_data.get('尺寸', ''),
            "详情页文字": processed_data.get('描述翻译', ''),
            "尺码表": ""  # 暂时为空，后续可以添加尺码表HTML
        }
    }

def write_to_feishu(access_token: str, app_token: str, table_id: str, records: list) -> bool:
    """写入数据到飞书多维表格"""
    import requests
    import time

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "CallawayJP Pipeline/1.0"
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
                verify=True  # 确保SSL验证
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

                    return True
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
                time.sleep(2 ** attempt)  # 指数退避
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

def save_processed_data(processed_data, timestamp):
    """保存处理后的数据"""
    output_file = f"full_pipeline_test_{timestamp}.json"

    result = {
        "timestamp": timestamp,
        "url": processed_data.get('商品链接', ''),
        "processed_data": processed_data,
        "processing_time": datetime.now().isoformat()
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"💾 处理结果已保存: {output_file}")
    return output_file

def main():
    """主函数：执行完整的三步流程"""
    print("🚀 开始完整三步流程测试")
    print("🎯 测试URL: https://store.descente.co.jp/commodity/SDSC0140D/LE1872EM012989/")
    print("=" * 80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 第一步：模拟数据抓取（使用预定义数据）
    print("\n📥 第一步：模拟数据抓取")
    print("=" * 60)

    product_data = create_test_product()
    print(f"✅ 产品数据准备完成")
    print(f"   商品ID: {product_data['productId']}")
    print(f"   产品名称: {product_data['productName']}")
    print(f"   品牌: {product_data['brand']}")
    print(f"   价格: {product_data['priceText']}")
    print(f"   颜色数: {len(product_data['colors'])}")
    print(f"   尺码数: {len(product_data['sizes'])}")
    print(f"   图片总数: {sum(len(g['images']) for g in product_data['imageGroups'])}")

    # 第二步：通用字段改写
    processed_data = step2_universal_processor(product_data)
    if not processed_data:
        print("\n❌ 第二步失败，终止流程")
        return False

    # 保存第二步结果
    save_processed_data(processed_data, timestamp)

    # 第三步：飞书同步
    feishu_success = step3_feishu_sync(processed_data)
    if not feishu_success:
        print("\n❌ 第三步失败，但第二步成功")
        print("✅ 第二步（核心处理器）验证成功！")

    print("\n" + "=" * 80)
    print("🎉 完整流程测试完成！")
    print("=" * 80)

    # 最终结果汇总
    print("\n📊 处理结果汇总:")
    print(f"✅ 品牌识别: {processed_data.get('品牌', 'N/A')}")
    print(f"✅ 性别分类: {processed_data.get('性别', 'N/A')}")
    print(f"✅ 服装类型: {processed_data.get('服装类型', 'N/A')}")

    title = processed_data.get('生成标题', '')
    if title:
        print(f"✅ AI标题生成: {title} (长度: {len(title)}字)")
    else:
        print("❌ AI标题生成: 失败")

    translation = processed_data.get('描述翻译', '')
    if translation:
        print(f"✅ 描述翻译: 成功 (长度: {len(translation)}字符)")
    else:
        print("❌ 描述翻译: 失败")

    images = processed_data.get('图片链接', '')
    if images:
        image_count = len(images.split(', ')) if images else 0
        print(f"✅ 图片处理: {image_count}张图片")
    else:
        print("❌ 图片处理: 失败")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)