#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于test_full_pipeline_one_url.py的生产版本：处理真实JSON数据并同步到飞书
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

def load_real_data(json_file):
    """加载真实的JSON数据文件"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 转换为处理器需要的格式
        converted_data = {
            'productId': data.get('商品ID', ''),
            'productName': data.get('商品标题', ''),
            'detailUrl': data.get('商品链接', ''),
            'priceText': data.get('价格', ''),
            'brand': data.get('品牌名', 'Le Coq公鸡乐卡克'),
            'gender': data.get('性别', ''),
            'colors': data.get('颜色', []),
            'imageUrls': data.get('图片链接', []),
            'sizes': data.get('尺码', []),
            'description': data.get('详情页文字', ''),
            'sizeChart': data.get('尺码表', {}),
        }

        print(f"✅ 成功加载JSON文件: {json_file}")
        print(f"   产品ID: {converted_data['productId']}")
        print(f"   产品名称: {converted_data['productName']}")
        print(f"   品牌: {converted_data['brand']}")
        print(f"   价格: {converted_data['priceText']}")
        print(f"   性别: {converted_data['gender']}")
        print(f"   颜色数: {len(converted_data['colors'])}")
        print(f"   图片数: {len(converted_data['imageUrls'])}")
        print(f"   尺码数: {len(converted_data['sizes'])}")

        return converted_data

    except Exception as e:
        print(f"❌ 加载JSON文件失败: {e}")
        return None

def determine_gender_fixed(product_data):
    """修复版性别检测 - 基于我们之前修复过的逻辑"""
    product_name = product_data.get('productName', '')
    gender_from_source = product_data.get('gender', '')  # 来源数据的性别
    detail_url = product_data.get('detailUrl', '')

    print(f"🔍 性别检测调试:")
    print(f"   来源性别: {gender_from_source}")
    print(f"   产品名: {product_name}")
    print(f"   详情URL: {detail_url}")

    # 1. 最高优先级：使用来源数据的性别（第一步已经检测过的）
    if gender_from_source == '女':
        print("   ✅ 使用来源性别: 女")
        return '女'
    elif gender_from_source == '男':
        print("   ✅ 使用来源性别: 男")
        return '男'

    # 2. 检查详情页URL中的性别标识
    if detail_url:
        if 'ds_F' in detail_url or 'ds_L' in detail_url or 'womens' in detail_url:
            print("   ✅ URL检测: 女")
            return '女'
        elif 'ds_M' in detail_url or 'mens' in detail_url:
            print("   ✅ URL检测: 男")
            return '男'

    # 3. 检查产品名称中的日文性别标识
    if 'レディース' in product_name or '女性' in product_name:
        print("   ✅ 名称检测: 女")
        return '女'
    elif 'メンズ' in product_name or '男性' in product_name:
        print("   ✅ 名称检测: 男")
        return '男'

    # 4. 默认返回空，让后续处理决定
    print("   ⚠️ 无法确定性别，返回空")
    return ''

def step2_process(product_data):
    """第二步：通用字段改写处理器"""
    print("\n🔄 第二步：通用字段改写处理")
    print("=" * 60)

    try:
        # 初始化处理器
        processor = Callaway13FieldProcessor()
        print("✅ 通用处理器初始化完成")

        # 🚀 修复：使用我们修复过的性别检测
        fixed_gender = determine_gender_fixed(product_data)
        if fixed_gender:
            product_data['gender'] = fixed_gender
            print(f"✅ 修复性别检测: {fixed_gender}")

        # 处理产品
        print(f"🔄 开始处理产品: {product_data['productName']}")
        processed_result = processor.process_product(product_data)

        if processed_result:
            print("✅ 第二步处理完成")

            # 🚀 强制覆盖性别字段，使用我们修复过的结果
            if fixed_gender:
                processed_result['性别'] = fixed_gender
                print(f"🔧 强制覆盖性别字段: {fixed_gender}")

            return processed_result
        else:
            print("❌ 第二步处理失败")
            return None

    except Exception as e:
        print(f"❌ 第二步异常: {e}")
        return None

def step3_feishu_sync(processed_data):
    """第三步：飞书数据同步 - 基于test_full_pipeline_one_url.py的成功逻辑"""
    print("\n🔄 第三步：飞书数据同步")
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

        # 准备飞书数据
        print("📋 准备写入飞书的数据...")
        record = create_feishu_record(processed_data)
        print("✅ 飞书记录格式准备完成")

        # 调试：打印即将发送到飞书的数据
        print("🔍 调试：准备发送到飞书的数据字段:")
        for key, value in record["fields"].items():
            print(f"   {key}: {value[:50] if value else '空'}{'...' if value and len(value) > 50 else ''}")

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
        return False

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
    # 基于完整的13个字段映射
    record = {
        "fields": {
            "商品链接": processed_data.get('商品链接', ''),
            "商品ID": processed_data.get('商品ID', ''),
            "商品标题": processed_data.get('生成标题', processed_data.get('商品标题', '')),
            "品牌名": processed_data.get('品牌', ''),
            "价格": processed_data.get('价格', ''),
            "性别": processed_data.get('性别', ''),
            "衣服分类": processed_data.get('服装类型', ''),
            "图片URL": processed_data.get('图片链接', ''),
            "颜色": processed_data.get('颜色', ''),
            "尺码": processed_data.get('尺寸', ''),
            "详情页文字": processed_data.get('描述翻译', ''),
            "尺码表": ""
        }
    }

    # 调试：打印即将发送到飞书的数据
    print("🔍 调试：准备发送到飞书的数据字段:")
    for key, value in record["fields"].items():
        print(f"   {key}: {value[:50] if value else '空'}{'...' if value and len(value) > 50 else ''}")

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
            print(f"🔄 尝试 {attempt + 1}/{max_retries}: 调用飞书API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"📊 飞书API响应状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📋 飞书API响应: {data}")
                if data.get('code') == 0:
                    print(f"✅ 飞书写入成功！记录数量: {len(records)}")
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

def save_processed_data(processed_data, timestamp):
    """保存处理后的数据"""
    try:
        output_file = f"real_data_processed_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 处理数据已保存: {output_file}")
    except Exception as e:
        print(f"⚠️ 保存数据失败: {e}")

def main():
    """主函数：处理真实数据文件"""
    json_file = "/Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf/single_url_fixed_2025-11-15T01-58-13-687Z.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("🚀 开始处理真实JSON数据并同步到飞书")
    print(f"📁 目标文件: {json_file}")
    print("=" * 80)

    # 加载真实数据
    product_data = load_real_data(json_file)
    if not product_data:
        print("❌ 流程终止：数据加载失败")
        return False

    # 第二步：数据转换
    processed_data = step2_process(product_data)
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
    print("🎉 真实数据处理流程完成！")
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
        image_count = len(images.split(', ')) if isinstance(images, str) else len(images) if images else 0
        print(f"✅ 图片处理: {image_count}张图片")
    else:
        print("❌ 图片处理: 失败")

    print(f"✅ 飞书同步: {'成功' if feishu_success else '失败'}")

    return feishu_success

if __name__ == "__main__":
    # 导入requests（放在这里避免重复导入）
    import requests

    success = main()
    sys.exit(0 if success else 1)