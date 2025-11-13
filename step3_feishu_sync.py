#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三步：飞书数据同步处理器
=====================================

这是所有品牌的统一第三步处理器：
- 固定的飞书API调用逻辑
- 标准化的数据同步机制
- 永远不变的同步核心

使用方法：
  python3 step3_feishu_sync.py --input step2_processed_data.json --token <飞书token>

Author: Claude Code
Date: 2025-11-13
Version: 1.0 - 永久固定版
"""

import json
import sys
import argparse
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

class FeishuSync:
    """飞书同步处理器"""

    def __init__(self, app_token: str = None, table_id: str = None):
        """
        初始化飞书同步器

        Args:
            app_token: 飞书多维表格应用token
            table_id: 飞书多维表格ID
        """
        self.app_token = app_token
        self.table_id = table_id
        self.base_url = "https://open.feishu.cn/open-apis/bitable/v1/apps"

        # 13个飞书字段映射（固定不变）
        self.feishu_field_mapping = {
            '商品链接': 'field_link',       # 商品链接
            '商品ID': 'field_id',           # 商品ID
            '商品标题': 'field_title',      # 商品标题
            '品牌名': 'field_brand',        # 品牌名
            '价格': 'field_price',         # 价格
            '性别': 'field_gender',        # 性别
            '衣服分类': 'field_category',   # 衣服分类
            '图片总数': 'field_image_count', # 图片总数
            '图片链接': 'field_images',      # 图片链接
            '颜色': 'field_colors',        # 颜色
            '尺码': 'field_sizes',         # 尺码
            '详情页文字': 'field_description', # 详情页文字
            '尺码表': 'field_size_chart'    # 尺码表
        }

        # 请求配置
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {app_token}' if app_token else None
        }

        # 同步配置
        self.batch_size = 50  # 每批同步数量
        self.request_delay = 1.0  # 请求间隔（秒）
        self.max_retries = 3  # 最大重试次数

    def load_step2_data(self, input_path: str) -> List[Dict]:
        """
        加载第二步处理后的数据

        Args:
            input_path: 第二步输出文件路径

        Returns:
            处理后的产品数据列表
        """
        print(f"📥 加载第二步数据: {input_path}")

        if not Path(input_path).exists():
            raise FileNotFoundError(f"第二步数据文件不存在: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取产品数据
        if isinstance(data, dict):
            products = data.get('products', [])
        elif isinstance(data, list):
            products = data
        else:
            raise ValueError("不支持的数据格式")

        print(f"✅ 加载完成: {len(products)} 个产品")
        return products

    def validate_feishu_config(self) -> bool:
        """
        验证飞书配置

        Returns:
            配置是否有效
        """
        if not self.app_token:
            print("❌ 飞书应用token未配置")
            return False

        if not self.table_id:
            print("❌ 飞书表格ID未配置")
            return False

        return True

    def test_feishu_connection(self) -> bool:
        """
        测试飞书连接

        Returns:
            连接是否成功
        """
        try:
            url = f"{self.base_url}/{self.app_token}/tables/{self.table_id}/records?page_size=1"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                print("✅ 飞书连接测试成功")
                return True
            else:
                print(f"❌ 飞书连接测试失败: {response.status_code}")
                print(f"响应: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 飞书连接测试异常: {e}")
            return False

    def prepare_feishu_record(self, product: Dict) -> Dict:
        """
        准备飞书记录数据

        Args:
            product: 第二步处理后的产品数据

        Returns:
            飞书记录格式数据
        """
        record = {
            "fields": {}
        }

        # 映射13个字段到飞书
        for field_name, field_key in self.feishu_field_mapping.items():
            value = product.get(field_name, '')

            # 特殊处理不同数据类型
            if field_name == '商品链接' and value:
                record["fields"][field_key] = {
                    "link": {
                        "url": value,
                        "text": "查看商品"
                    }
                }
            elif field_name == '图片链接' and value:
                # 图片链接处理（逗号分隔）
                images = [img.strip() for img in str(value).split(',') if img.strip()]
                record["fields"][field_key] = images[:10]  # 最多10张图片
            elif field_name == '颜色' and value:
                # 颜色处理（多行文本）
                colors = str(value).split('\n')
                record["fields"][field_key] = '\n'.join(colors[:20])  # 最多20行
            elif field_name == '尺码' and value:
                # 尺码处理
                if isinstance(value, list):
                    record["fields"][field_key] = ', '.join(str(s) for s in value)
                else:
                    record["fields"][field_key] = str(value)
            elif field_name == '详情页文字' and value:
                # 描述文字处理（限制长度）
                text = str(value)
                if len(text) > 5000:  # 飞书字段长度限制
                    text = text[:4970] + "..."
                record["fields"][field_key] = text
            elif field_name == '尺码表' and value:
                # 尺码表处理
                record["fields"][field_key] = str(value)[:2000] if len(str(value)) > 2000 else str(value)
            else:
                # 普通字段
                record["fields"][field_key] = value if value else None

        return record

    def sync_batch_to_feishu(self, products: List[Dict], batch_num: int = 1) -> Dict:
        """
        批量同步数据到飞书

        Args:
            products: 产品数据列表
            batch_num: 批次编号

        Returns:
            同步结果
        """
        print(f"🔄 同步第{batch_num}批: {len(products)} 个产品")

        try:
            # 准备记录数据
            records = []
            for product in products:
                record = self.prepare_feishu_record(product)
                records.append(record)

            # 构建请求数据
            url = f"{self.base_url}/{self.app_token}/tables/{self.table_id}/records/batch_create"

            payload = {
                "records": records
            }

            # 发送请求
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                success_count = result.get('data', {}).get('created_count', 0)
                print(f"   ✅ 成功同步: {success_count} 个记录")
                return {"success": True, "count": success_count, "batch": batch_num}
            else:
                print(f"   ❌ 同步失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return {"success": False, "error": response.text, "batch": batch_num}

        except Exception as e:
            print(f"   ❌ 同步异常: {e}")
            return {"success": False, "error": str(e), "batch": batch_num}

    def sync_to_feishu(self, products: List[Dict]) -> Dict:
        """
        同步所有产品数据到飞书

        Args:
            products: 产品数据列表

        Returns:
            同步结果统计
        """
        print("🚀 开始第三步：飞书数据同步")
        print("=" * 60)

        if not self.validate_feishu_config():
            return {"success": False, "error": "飞书配置无效"}

        print("🔍 测试飞书连接...")
        if not self.test_feishu_connection():
            return {"success": False, "error": "飞书连接失败"}

        total_products = len(products)
        total_batches = (total_products + self.batch_size - 1) // self.batch_size

        print(f"📊 同步统计:")
        print(f"   总产品数: {total_products}")
        print(f"   批次数: {total_batches}")
        print(f"   每批大小: {self.batch_size}")

        # 批量同步
        success_count = 0
        failed_batches = []

        for i in range(0, total_products, self.batch_size):
            batch_num = (i // self.batch_size) + 1
            batch_products = products[i:i + self.batch_size]

            result = self.sync_batch_to_feishu(batch_products, batch_num)

            if result["success"]:
                success_count += result["count"]
            else:
                failed_batches.append(batch_num)

            # 请求间隔
            if batch_num < total_batches:
                time.sleep(self.request_delay)

        # 生成同步报告
        print("\n" + "=" * 60)
        print("📊 第三步飞书同步完成报告")
        print("=" * 60)
        print(f"总产品数: {total_products}")
        print(f"成功同步: {success_count}")
        print(f"成功批次: {total_batches - len(failed_batches)}/{total_batches}")

        if failed_batches:
            print(f"失败批次: {failed_batches}")

        success_rate = (success_count / total_products) * 100 if total_products > 0 else 0
        print(f"成功率: {success_rate:.1f}%")

        if success_rate >= 90:
            print("\n🎉 第三步飞书同步成功！")
            return {
                "success": True,
                "total_products": total_products,
                "success_count": success_count,
                "success_rate": success_rate,
                "failed_batches": failed_batches
            }
        else:
            print("\n⚠️ 第三步飞书同步部分失败")
            return {
                "success": False,
                "total_products": total_products,
                "success_count": success_count,
                "success_rate": success_rate,
                "failed_batches": failed_batches
            }

  
def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='第三步：飞书数据同步处理器 (所有品牌统一)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 同步到飞书（需要token）
  python3 step3_feishu_sync.py --input step2_processed_data.json --token <飞书token>

  # 同步并指定表格ID
  python3 step3_feishu_sync.py --input step2_processed_data.json --token <token> --table <table_id>

  # 导出CSV文件（备用）
  python3 step3_feishu_sync.py --input step2_processed_data.json --export csv_output.csv

注意：这是第三步处理器，需要第二步的数据作为输入。
    """
    )

    parser.add_argument(
        '--input', '-i',
        required=True,
        help='第二步处理后的数据文件路径 (必需)'
    )

    parser.add_argument(
        '--token', '-t',
        help='飞书应用token (同步到飞书时必需)'
    )

    parser.add_argument(
        '--table',
        help='飞书表格ID (可选，默认使用配置中的ID)'
    )

  
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='测试模式，不实际同步到飞书'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='第三步飞书同步处理器 v1.0 (永久固定版)'
    )

    args = parser.parse_args()

    # 验证输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        sys.exit(1)

    try:
        # 初始化飞书同步器
        sync = FeishuSync(app_token=args.token, table_id=args.table)

        # 加载第二步数据
        products = sync.load_step2_data(str(input_path))

        if not products:
            print("❌ 没有找到需要同步的产品数据")
            sys.exit(1)

        # 执行同步
        if args.dry_run:
            # 测试模式
            print("🧪 测试模式：验证数据和飞书配置")
            if sync.validate_feishu_config():
                print("✅ 飞书配置有效")
                if sync.test_feishu_connection():
                    print("✅ 飞书连接正常")
                    print(f"📊 准备同步 {len(products)} 个产品")
                else:
                    print("❌ 飞书连接失败")
                    sys.exit(1)
            else:
                print("❌ 飞书配置无效")
                sys.exit(1)
        else:
            # 同步到飞书
            result = sync.sync_to_feishu(products)

            if result["success"]:
                print("\n🎯 第三步统一指令执行成功！")
                sys.exit(0)
            else:
                print("\n❌ 第三步同步失败")
                sys.exit(1)

    except Exception as e:
        print(f"❌ 第三步处理异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()