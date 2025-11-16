#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第三步：上传到飞书
"""

import json
import sys
import os
import requests
from datetime import datetime

def main():
    print('🚀 第三步：开始上传到飞书...')

    # 加载飞书格式数据
    try:
        with open('/Users/sanshui/Desktop/CallawayJP/feishu_formatted_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print('❌ 未找到飞书格式数据文件，请先运行第二步！')
        sys.exit(1)

    records = data.get('records', [])
    if not records:
        print('❌ 数据文件中没有记录')
        sys.exit(1)

    print(f'📊 准备上传 {len(records)} 条记录')

    # 飞书配置
    FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', 'cli_a123b456c789d012')
    FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', 'your_app_secret_here')
    FEISHU_TABLE_ID = os.getenv('FEISHU_TABLE_ID', 'tblhBepAOlCyhfoN')

    if FEISHU_APP_SECRET == 'your_app_secret_here':
        print('⚠️ 使用演示模式，不会实际上传到飞书')
        print('📋 记录预览:')
        for i, record in enumerate(records):
            fields = record.get('fields', {})
            print(f'  记录 {i+1}:')
            print(f'    商品ID: {fields.get("商品ID", "")}')
            print(f'    商品标题: {fields.get("商品标题", "")}')
            print(f'    品牌: {fields.get("品牌名", "")}')
            print(f'    性别: {fields.get("性别", "")}')
            print(f'    价格: {fields.get("价格", "")}')
            print(f'    颜色: {fields.get("颜色", "")}')
            print(f'    图片数量: {fields.get("图片数量", "")}')
            print('')

        print('✅ 第三步：飞书上传模拟完成！')
        print('🎯 要实际上传，请配置正确的飞书环境变量')
        return

    try:
        # 获取飞书访问令牌
        print('🔐 获取飞书访问令牌...')
        token_url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        token_response = requests.post(token_url, json={
            'app_id': FEISHU_APP_ID,
            'app_secret': FEISHU_APP_SECRET
        })

        if token_response.status_code != 200:
            print(f'❌ 获取访问令牌失败: {token_response.status_code}')
            print(token_response.text)
            sys.exit(1)

        token_data = token_response.json()
        if token_data.get('code') != 0:
            print(f'❌ 访问令牌错误: {token_data.get("msg")}')
            sys.exit(1)

        access_token = token_data.get('tenant_access_token')
        print('✅ 访问令牌获取成功')

        # 上传记录
        print('📤 开始上传记录...')
        success_count = 0

        for i, record in enumerate(records):
            fields = record.get('fields', {})

            # 构建飞书记录格式
            feishu_record = {
                'fields': fields
            }

            # 上传单条记录
            upload_url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/tables/{FEISHU_TABLE_ID}/records'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            upload_response = requests.post(upload_url, json=feishu_record, headers=headers)

            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                if upload_data.get('code') == 0:
                    success_count += 1
                    print(f'✅ 记录 {i+1} 上传成功: {fields.get("商品标题", "")}')
                else:
                    print(f'❌ 记录 {i+1} 上传失败: {upload_data.get("msg")}')
            else:
                print(f'❌ 记录 {i+1} 上传失败: HTTP {upload_response.status_code}')

        print(f'\\n📊 上传结果汇总:')
        print(f'✅ 成功上传: {success_count} 条记录')
        print(f'❌ 失败: {len(records) - success_count} 条记录')

        if success_count == len(records):
            print('\\n🎉 第三步：飞书上传完全成功！')
        else:
            print('\\n⚠️ 第三步：部分上传成功')

    except Exception as e:
        print(f'❌ 上传过程出错: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()