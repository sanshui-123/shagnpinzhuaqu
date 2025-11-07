#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书产品详情翻译服务 v2
====================================

提供结构化的日文商品描述翻译功能，支持：
- 产品描述段落化
- 产品亮点突出显示  
- 材质信息单独成行
- 尺码表 Markdown 格式化
- 产地和洗涤信息标注

Author: Assistant
Date: 2025-11-03
Version: 2.0 - 修复循环依赖，内部实现 GLM 调用
"""

import re
import os
import time
import threading
import requests
from typing import Dict, Optional

# GLM API 配置常量
GLM_MIN_INTERVAL = float(os.environ.get('GLM_MIN_INTERVAL', 0.4))  # 单位秒，默认 0.4
GLM_MAX_RETRIES = int(os.environ.get('GLM_MAX_RETRIES', 3))
GLM_BACKOFF_FACTOR = float(os.environ.get('GLM_BACKOFF_FACTOR', 1.8))

# GLM API 调用控制全局变量（独立于主脚本）
_glm_call_lock = threading.Lock()
_last_glm_call_ts = 0.0

def clean_description_text(description: str) -> str:
    """清理日文描述文本，提取真正的商品描述内容
    
    复用现有逻辑，移除无关信息
    """
    if not description:
        return ""
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', description)
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 移除常见的无关信息
    unwanted_patterns = [
        r'※.*?。',  # 注意事项
        r'お客様.*?。',  # 客户相关
        r'返品.*?。',  # 退货相关
        r'配送.*?。',  # 配送相关
    ]
    
    for pattern in unwanted_patterns:
        text = re.sub(pattern, '', text)
    
    return text.strip()

def build_enhanced_translation_prompt(description: str) -> str:
    """构建增强的商品描述翻译提示词
    
    按照用户要求的"更详细的提示词版本"格式实现
    """
    return f"""请将以下日文服装产品描述翻译成中文，具体要求：

【翻译要求】
- 语言流畅自然，避免机翻腔
- 专业术语准确（如面料名称、工艺）
- 保持营销文案的吸引力

【格式要求】
- 产品描述：分段落展示，每个特点单独一段
- 产品亮点：用【】突出显示，如【8向弹力】
- 材质信息：单独成行
- 产地和洗涤：单独标注
- 尺码表：必须格式化为Markdown表格

【尺码表格式示例】
| 尺码 | 胸围 | 衣长 | 袖长 |
|------|------|------|------|
| S    | 106cm| 58cm | 77.5cm|
| M    | 110cm| 60cm | 79cm|

【期望输出格式】
注意：只输出指定结构内容，禁止写开场白、致谢、解释等额外文字，直接从【产品描述】开头输出。

【产品描述】
采用塔夫塔面料，具有全方向弹力和适度挺括感。融入运动风格设计的茄克式外套。为应对温差变化，袖子采用可拆卸设计，可在短袖⇔长袖之间切换。下摆配有抽绳，可调节版型。

【产品亮点】
✓ 半袖风格 - 本季必备的半袖款式
✓ 8向弹力 - 全方向伸缩面料
✓ 2WAY设计 - 可拆卸袖子

【材质信息】
面料：100%聚酯纤维
辅料：100%聚酯纤维

【产地与洗涤】
产地：越南制造
洗涤：按标签说明

【尺码对照表】
| 尺码 | 胸围 | 衣长 | 袖长 |
|------|------|------|------|
| S    | 106cm| 58cm | 77.5cm|
| M    | 110cm| 60cm | 79cm|
| L    | 114cm| 62cm | 80cm|
| LL   | 118cm| 63cm | 81cm|

【尺码说明】
※ 以上尺寸为成品实测尺寸（包含松量）
※ 因面料特性，可能存在1-2cm误差
※ 商品标签标注的为净体尺寸，请参考尺码表选择

原文：
{description}
"""

def call_glm_api_internal(prompt: str) -> str:
    """内部 GLM API 调用实现
    
    TODO: 后续替换为 glm_client 依赖注入
    临时内部实现，避免循环依赖
    """
    global _last_glm_call_ts
    
    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        print("错误：ZHIPU_API_KEY 环境变量未设置")
        return ""
    
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"{api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4.6",  # 使用 GLM-4.6 模型进行翻译
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 4000
    }
    
    # 限流控制和重试逻辑
    for attempt in range(GLM_MAX_RETRIES + 1):
        try:
            # 使用锁控制最小间隔
            with _glm_call_lock:
                current_time = time.time()
                time_since_last_call = current_time - _last_glm_call_ts
                sleep_time = max(0, GLM_MIN_INTERVAL - time_since_last_call)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # 发起请求
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                _last_glm_call_ts = time.time()
            
            response.raise_for_status()
            data = response.json()
            print(f"GLM API响应状态: {response.status_code}")
            
            if 'choices' in data and len(data['choices']) > 0:
                choice = data['choices'][0]['message']
                content = choice.get('content', '').strip()
                
                print(f"提取的content: {content[:200]}...")
                return content
            else:
                print(f"API响应格式异常: choices不存在或为空")
                return ""
            
        except requests.exceptions.HTTPError as e:
            print(f"GLM API HTTP错误 (尝试{attempt+1}/{GLM_MAX_RETRIES+1}): {e}")
            
            # 检查是否是429错误
            if e.response.status_code == 429 or "Too Many Requests" in str(e):
                if attempt < GLM_MAX_RETRIES:
                    # 指数退避策略
                    backoff_time = 1.0 * (GLM_BACKOFF_FACTOR ** attempt)
                    print(f"限流重试，等待{backoff_time}秒...")
                    time.sleep(backoff_time)
                    continue
                else:
                    print("达到最大重试次数，放弃请求")
                    return ""
            else:
                print("非429错误，放弃请求")
                return ""
                
        except Exception as e:
            print(f"GLM API其他错误 (尝试{attempt+1}/{GLM_MAX_RETRIES+1}): {e}")
            
            # 其他类型的错误
            if "Too Many Requests" in str(e) or "429" in str(e):
                if attempt < GLM_MAX_RETRIES:
                    backoff_time = 1.0 * (GLM_BACKOFF_FACTOR ** attempt)
                    print(f"限流重试，等待{backoff_time}秒...")
                    time.sleep(backoff_time)
                    continue
                else:
                    print("达到最大重试次数，放弃请求")
                    return ""
            else:
                print("其他错误，放弃请求")
                return ""
    
    return ""

def validate_translation_format(translated: str) -> bool:
    """验证翻译结果是否符合预期格式
    
    检查是否包含必要的结构标记
    """
    if not translated:
        return False
    
    required_sections = [
        '【产品描述】',
        '【产品亮点】',
        '【材质信息】'
    ]
    
    # 检查是否包含所有必需的部分
    for section in required_sections:
        if section not in translated:
            print(f"验证失败：缺少必需部分 {section}")
            return False
    
    # 检查是否包含亮点列表（✓ 符号）
    if '✓' not in translated:
        print("验证失败：缺少产品亮点列表（✓ 符号）")
        return False
    
    print("翻译格式验证通过")
    return True

def translate_description(product: Dict) -> str:
    """将商品描述翻译成结构化中文格式
    
    Args:
        product: 商品数据字典，包含 description 字段
        
    Returns:
        str: 结构化的中文描述，包含：
            - 【产品描述】段落化
            - 【产品亮点】✓ 列表
            - 【材质信息】单独成行
            - 【产地与洗涤】单独标注
            - Markdown 尺码表
            - 尺码说明提示
            
        如果翻译失败或格式不符合要求，返回空字符串
    """
    if not product:
        return ""
    
    description = product.get('description', '')
    if not description:
        return ""
    
    # 1. 清理描述文本
    cleaned_description = clean_description_text(description)
    if not cleaned_description:
        print("警告：description 清理后为空，跳过翻译")
        return ""
    
    print(f"清理后的描述内容（前100字符）：{cleaned_description[:100]}...")
    
    # 2. 构建增强提示词
    prompt = build_enhanced_translation_prompt(cleaned_description)
    print(f"准备调用 GLM 翻译，提示词长度：{len(prompt)}")
    
    # 3. 调用 GLM 翻译
    try:
        translated = call_glm_api_internal(prompt)
        print(f"GLM 翻译返回结果长度：{len(translated) if translated else 0}")
        print(f"翻译结果（前100字符）：{translated[:100] if translated else 'None'}...")
        
        if not translated:
            print("GLM 翻译返回空结果")
            return ""
        
        # 4. 验证翻译结果格式
        if not validate_translation_format(translated):
            print("翻译结果格式验证失败，返回空字符串")
            return ""
        
        print("翻译成功完成")
        return translated.strip()
            
    except Exception as e:
        print(f"翻译过程出现异常：{e}")
        return ""

# 导出主要函数
__all__ = ['translate_description', 'validate_translation_format']