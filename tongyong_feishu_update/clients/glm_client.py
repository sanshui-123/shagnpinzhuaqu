"""GLM客户端实现

提供GLM API的统一调用接口，包含限流、重试和指数退避机制。
"""

import os
import time
import threading
import requests
from typing import Optional

from .interfaces import GLMClientInterface


class GLMClient(GLMClientInterface):
    """GLM客户端实现
    
    提供标题生成和翻译功能，支持：
    - 自动限流控制
    - 429错误重试机制  
    - 指数退避策略
    - 多模型支持
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "glm-4.5-air",
        min_interval: float = 0.4,
        max_retries: int = 3,
        backoff_factor: float = 1.8
    ):
        """初始化GLM客户端
        
        Args:
            api_key: GLM API密钥
            model: 默认模型名称
            min_interval: 调用最小间隔（秒）
            max_retries: 最大重试次数
            backoff_factor: 退避因子
        """
        self.api_key = api_key
        self.default_model = model
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # 调用控制
        self._call_lock = threading.Lock()
        self._last_call_ts = 0.0
        
        # API配置
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    def generate_title(
        self, 
        prompt: str, 
        *, 
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.3
    ) -> str:
        """生成中文商品标题
        
        Args:
            prompt: 标题生成提示词
            model: 可选的模型名称，覆盖默认模型
            max_tokens: 最大令牌数
            temperature: 温度参数
            
        Returns:
            str: 生成的中文标题
        """
        return self._generate_content(
            prompt=prompt,
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def translate(
        self, 
        prompt: str, 
        *, 
        model: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.2
    ) -> str:
        """翻译文本
        
        Args:
            prompt: 翻译提示词
            model: 可选的模型名称，覆盖默认模型
            max_tokens: 最大令牌数
            temperature: 温度参数
            
        Returns:
            str: 翻译结果
        """
        # 翻译通常使用更精确的模型
        translate_model = model or "glm-4.6"
        return self._generate_content(
            prompt=prompt,
            model=translate_model,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def _generate_content(
        self, 
        prompt: str, 
        model: str, 
        max_tokens: int, 
        temperature: float
    ) -> str:
        """统一的内容生成方法
        
        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大令牌数
            temperature: 温度参数
            
        Returns:
            str: 生成的内容
        """
        for attempt in range(self.max_retries + 1):
            try:
                response = self._request(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                if response and 'choices' in response and len(response['choices']) > 0:
                    choice = response['choices'][0]['message']
                    content = choice.get('content', '').strip()
                    reasoning_content = choice.get('reasoning_content', '').strip()
                    
                    # 打印调试信息
                    if reasoning_content:
                        print(f"[GLM Debug] reasoning_content: {reasoning_content[:100]}...")
                    if content:
                        print(f"[GLM Debug] content: {content[:100]}...")
                    
                    # 优先返回content，如果为空则尝试从reasoning_content提取
                    if content:
                        return content
                    elif reasoning_content:
                        # 从reasoning_content中提取有效内容
                        extracted = self._extract_from_reasoning(reasoning_content)
                        print(f"[GLM Debug] extracted: {extracted}")
                        return extracted
                
                return ""
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 or "Too Many Requests" in str(e):
                    if attempt < self.max_retries:
                        backoff_time = 1.0 * (self.backoff_factor ** attempt)
                        print(f"GLM API限流重试，等待{backoff_time}秒...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        print("GLM API达到最大重试次数，请求失败")
                        return ""
                else:
                    print(f"GLM API HTTP错误: {e}")
                    return ""
                    
            except Exception as e:
                error_msg = str(e)
                if "Too Many Requests" in error_msg or "429" in error_msg:
                    if attempt < self.max_retries:
                        backoff_time = 1.0 * (self.backoff_factor ** attempt)
                        print(f"GLM API限流重试，等待{backoff_time}秒...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        print("GLM API达到最大重试次数，请求失败")
                        return ""
                else:
                    print(f"GLM API其他错误: {e}")
                    return ""
        
        return ""
    
    def _request(
        self, 
        prompt: str, 
        model: str, 
        max_tokens: int, 
        temperature: float
    ) -> dict:
        """发送HTTP请求到GLM API
        
        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大令牌数
            temperature: 温度参数
            
        Returns:
            dict: API响应数据
        """
        headers = {
            "Authorization": f"{self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 限流控制
        with self._call_lock:
            current_time = time.time()
            time_since_last_call = current_time - self._last_call_ts
            sleep_time = max(0, self.min_interval - time_since_last_call)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # 发起请求
            response = requests.post(
                self.api_url, 
                headers=headers, 
                json=payload, 
                timeout=120
            )
            self._last_call_ts = time.time()
        
        response.raise_for_status()
        return response.json()
    
    def _extract_from_reasoning(self, reasoning_content: str) -> str:
        """从reasoning_content中提取有效内容
        
        这是一个简化版本，主要用于兼容GLM-4.5模型的推理模式。
        
        Args:
            reasoning_content: 推理内容
            
        Returns:
            str: 提取的有效内容
        """
        if not reasoning_content:
            return ""
        
        # 优化的内容提取逻辑 - 更精确地提取标题
        if len(reasoning_content) < 20:
            return reasoning_content.strip()
        
        lines = [line.strip() for line in reasoning_content.splitlines() if line.strip()]
        
        # 策略1：查找以"25秋冬"或"26春夏"开头的行（最可能是最终标题）
        for line in lines:
            # 先清除分析性前缀
            clean_line = self._remove_analysis_prefix(line)
            if (clean_line.startswith('25') or clean_line.startswith('26')) and '卡拉威' in clean_line and '高尔夫' in clean_line:
                if 20 <= len(clean_line) <= 35:  # 标题长度检查
                    return clean_line
        
        # 策略2：查找最后一个包含关键信息的行
        key_indicators = ['卡拉威', 'Callaway', '高尔夫', '女士', '男士', '外套', '上衣']
        for line in reversed(lines):
            # 清除分析性前缀
            clean_line = self._remove_analysis_prefix(line)
            
            # 过滤掉分析性语句
            analysis_keywords = [
                '我需要', '让我', '分析', '处理', '检查', '字符', '长度', 
                '要求', '禁止', '必须', '出现一次', '符合', '遵循', '根据', '应该'
            ]
            
            has_analysis = any(keyword in clean_line for keyword in analysis_keywords)
            has_key_info = any(indicator in clean_line for indicator in key_indicators)
            
            if has_key_info and not has_analysis and clean_line:
                if 15 <= len(clean_line) <= 35:  # 标题长度检查
                    return clean_line
        
        # 策略3：如果以上都失败，返回最后一行非空内容
        if lines:
            last_line = lines[-1].strip('"\'：:-—•·').strip()
            if 10 <= len(last_line) <= 50:
                return last_line
        
        return ""
    
    def _remove_analysis_prefix(self, text: str) -> str:
        """去除分析性前缀，提取纯标题
        
        Args:
            text: 原始文本
            
        Returns:
            str: 去除前缀后的纯标题
        """
        # 常见的分析性前缀模式
        analysis_prefixes = [
            r'^\d+\.\s*',  # "1. ", "2. " 等
            r'^[^：]*：\s*',  # "标题结构：", "组合起来：", "即：", "所以结构应该是：" 等
            r'^[^:]*:\s*',  # 英文冒号
            r'^所以.*?是[:：]\s*',  # "所以结构应该是："
            r'^因此.*?是[:：]\s*',  # "因此答案是："
            r'^答案.*?是[:：]\s*',  # "答案是："
            r'^结果.*?是[:：]\s*',  # "结果是："
            r'^最终.*?是[:：]\s*',  # "最终答案是："
            r'^即[:：]\s*',  # "即："
            r'^也就是说[:：]\s*',  # "也就是说："
            r'^具体来说[:：]\s*',  # "具体来说："
            r'^换句话说[:：]\s*',  # "换句话说："
        ]
        
        import re
        cleaned = text.strip()
        
        # 逐个去除前缀模式
        for pattern in analysis_prefixes:
            cleaned = re.sub(pattern, '', cleaned)
        
        # 去除可能的引号和标点
        cleaned = cleaned.strip('"\'""''').strip()
        
        # 去除包含变量占位符的部分，如 "[功能词]"
        cleaned = re.sub(r'\[.*?\]', '', cleaned)
        
        return cleaned.strip()