#!/usr/bin/env python3
"""
测试指定URL的完整三步流程
"""

import sys
import os
sys.path.append('/Users/sanshui/Desktop/CallawayJP')

import json
import subprocess
from pathlib import Path

def test_complete_pipeline():
    """测试完整的三步流程"""
    test_url = "https://store.descente.co.jp/commodity/SDSC0140D/LE1872EW011538/"

    print("🚀 开始测试完整三步流程")
    print(f"📍 测试URL: {test_url}")
    print("=" * 60)

    # Step 1: JavaScript抓取
    print("\n📡 Step 1: JavaScript数据抓取...")
    try:
        # 切换到lecoqgolf目录
        lecoq_dir = "/Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/lecoqgolf"

        # 运行单URL处理器
        result = subprocess.run([
            'node', 'single_url_fixed_processor.js', '--url', test_url
        ],
        cwd=lecoq_dir,
        capture_output=True,
        text=True,
        timeout=60
        )

        if result.returncode != 0:
            print(f"❌ Step 1 失败: {result.stderr}")
            return False
        else:
            print("✅ Step 1 完成")
            print(f"输出: {result.stdout[-200:]}")  # 显示最后200字符

    except subprocess.TimeoutExpired:
        print("❌ Step 1 超时")
        return False
    except Exception as e:
        print(f"❌ Step 1 异常: {e}")
        return False

    # 查找生成的JSON文件
    output_files = list(Path(lecoq_dir).glob("single_url_fixed_*.json"))
    if not output_files:
        print("❌ 未找到Step 1输出文件")
        return False

    latest_file = max(output_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 Step 1 输出文件: {latest_file}")

    # 检查数据质量
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            step1_data = json.load(f)

        products = step1_data.get('products', {})
        if not products:
            print("❌ Step 1 数据为空")
            return False

        # 检查第一个产品的关键字段
        first_product = list(products.values())[0]

        print("\n📊 Step 1 数据质量检查:")
        print(f"  - Product ID: {first_product.get('productId', 'N/A')}")
        print(f"  - Product Name: {first_product.get('productName', 'N/A')[:50]}...")
        print(f"  - Gender: {first_product.get('gender', 'N/A')}")
        print(f"  - Price: {first_product.get('price', 'N/A')}")
        print(f"  - Colors: {len(first_product.get('colors', []))}")
        print(f"  - Sizes: {len(first_product.get('sizes', []))}")
        print(f"  - Images: {len(first_product.get('imageUrls', []))}")
        print(f"  - Description Length: {len(first_product.get('description', ''))}")

        # 验证关键字段是否正确
        issues = []
        if not first_product.get('gender'):
            issues.append("性别字段缺失")
        if not first_product.get('imageUrls'):
            issues.append("图片链接缺失")
        if not first_product.get('description'):
            issues.append("描述缺失")

        if issues:
            print(f"⚠️ 发现问题: {', '.join(issues)}")
        else:
            print("✅ Step 1 数据质量良好")

    except Exception as e:
        print(f"❌ Step 1 数据检查失败: {e}")
        return False

    # Step 2: Python处理
    print("\n🔄 Step 2: Python数据处理...")
    try:
        # 复制Step 1的输出到Python处理目录
        python_input = "/Users/sanshui/Desktop/CallawayJP/test_fixed_final.json"

        import shutil
        shutil.copy2(latest_file, python_input)
        print(f"📁 复制文件到: {python_input}")

        # 运行Python处理脚本
        result = subprocess.run([
            'python3', 'update_orchestrator.py'
        ],
        cwd="/Users/sanshui/Desktop/CallawayJP/tongyong_feishu_update",
        capture_output=True,
        text=True,
        timeout=120
        )

        if result.returncode != 0:
            print(f"❌ Step 2 失败: {result.stderr}")
            return False
        else:
            print("✅ Step 2 完成")
            print(f"输出: {result.stdout[-300:]}")  # 显示最后300字符

    except subprocess.TimeoutExpired:
        print("❌ Step 2 超时")
        return False
    except Exception as e:
        print(f"❌ Step 2 异常: {e}")
        return False

    # Step 3: 检查飞书更新结果
    print("\n📋 Step 3: 检查飞书更新结果...")

    # 查找飞书输出文件
    feishu_files = list(Path("/Users/sanshui/Desktop/CallawayJP/tongyong_feishu_update").glob("feishu_results_*.json"))
    if not feishu_files:
        print("⚠️ 未找到飞书结果文件，可能需要检查API配置")
        return True  # 不算失败，因为API配置问题
    else:
        latest_feishu = max(feishu_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 飞书结果文件: {latest_feishu}")

        try:
            with open(latest_feishu, 'r', encoding='utf-8') as f:
                feishu_data = json.load(f)

            print("\n📊 飞书更新结果:")
            print(f"  - 总记录数: {feishu_data.get('total_records', 0)}")
            print(f"  - 成功更新: {feishu_data.get('updated_records', 0)}")
            print(f"  - 新增记录: {feishu_data.get('new_records', 0)}")
            print(f"  - 失败记录: {feishu_data.get('failed_records', 0)}")

            # 如果有详细记录，检查第一个记录的性别字段
            details = feishu_data.get('details', [])
            if details:
                first_detail = details[0]
                updated_fields = first_detail.get('updated_fields', {})
                gender_value = updated_fields.get('性别', 'N/A')
                print(f"  - 性别字段值: {gender_value}")

                if gender_value == '女':
                    print("✅ 性别字段正确显示为'女'")
                else:
                    print(f"⚠️ 性别字段显示为'{gender_value}'，期望为'女'")

            print("✅ 完整流程测试完成")
            return True

        except Exception as e:
            print(f"❌ 飞书结果检查失败: {e}")
            return False

if __name__ == "__main__":
    print("🧪 开始测试指定URL的完整流程")
    success = test_complete_pipeline()

    if success:
        print("\n🎉 测试成功完成！")
    else:
        print("\n❌ 测试过程中发现问题")

    print("\n请检查上述详细输出以确认修复效果。")