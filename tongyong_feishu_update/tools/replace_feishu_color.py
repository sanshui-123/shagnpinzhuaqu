#!/usr/bin/env python3
"""
批量替换飞书颜色字段的文本

用法:
    python3 -m tongyong_feishu_update.tools.replace_feishu_color \
        --target "卡其色" \
        --replacement "卡其绿" \
        --field "颜色" \
        --brand "Le Coq公鸡乐卡克"
"""

import argparse
from typing import Any, Dict, List, Tuple

from ..clients import create_feishu_client


def _replace_value(value: Any, target: str, replacement: str) -> Tuple[bool, Any]:
    """替换字段值中的目标文本"""
    if value is None:
        return False, value

    if isinstance(value, str):
        new_value = value.replace(target, replacement)
        return (new_value != value), new_value

    if isinstance(value, list):
        changed = False
        new_list = []
        for item in value:
            item_changed, new_item = _replace_value(item, target, replacement)
            if item_changed:
                changed = True
            new_list.append(new_item)
        return changed, new_list

    if isinstance(value, dict):
        changed = False
        new_dict = {}
        for k, v in value.items():
            item_changed, new_v = _replace_value(v, target, replacement)
            if item_changed:
                changed = True
            new_dict[k] = new_v
        return changed, new_dict

    return False, value


def main():
    parser = argparse.ArgumentParser(
        description="批量替换飞书表格中指定字段的文本内容"
    )
    parser.add_argument("--target", required=True, help="需要替换的原始文本")
    parser.add_argument("--replacement", required=True, help="新的文本内容")
    parser.add_argument("--field", default="颜色", help="需要更新的字段名称，默认: 颜色")
    parser.add_argument("--brand", help="可选，按品牌名过滤记录")
    parser.add_argument("--dry-run", action="store_true", help="只统计不提交更新")

    args = parser.parse_args()

    feishu_client = create_feishu_client()
    records = feishu_client.get_records()
    target = args.target
    replacement = args.replacement
    field_name = args.field
    brand_filter = args.brand.strip() if args.brand else None

    updates: List[Dict[str, Any]] = []
    total_checked = 0
    total_matched = 0

    for product_id, record in records.items():
        fields = record["fields"]
        brand_name = (fields.get("品牌名") or "").strip()

        if brand_filter and brand_name != brand_filter:
            continue

        value = fields.get(field_name)
        total_checked += 1
        changed, new_value = _replace_value(value, target, replacement)

        if changed:
            total_matched += 1
            update_entry = {
                "record_id": record["record_id"],
                "fields": {field_name: new_value},
            }
            updates.append(update_entry)

    print(f"共检查 {total_checked} 条记录，匹配 {total_matched} 条")

    if not updates:
        print("没有找到需要替换的记录，无需更新。")
        return

    if args.dry_run:
        print("Dry run 模式，未提交更新。")
        return

    print(f"开始更新 {len(updates)} 条记录...")
    feishu_client.batch_update(updates, batch_size=30)
    print("✅ 替换完成")


if __name__ == "__main__":
    main()
