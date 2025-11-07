"""通用设置配置

本模块包含系统通用配置常量和设置。
主要包括：
- API配置
- 文件路径配置
- 数据处理参数
- 日志配置
- 其他通用设置
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class GLMConfig:
    """GLM配置类"""
    api_key: str
    model: str = "glm-4.5-air"
    min_interval: float = 0.4
    max_retries: int = 3
    backoff_factor: float = 1.8


@dataclass
class FeishuConfig:
    """飞书配置类"""
    app_id: str
    app_secret: str
    app_token: str
    table_id: str
    max_retries: int = 3
    backoff_factor: float = 1.8


def get_glm_config(
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> GLMConfig:
    """获取GLM配置
    
    Args:
        model: 可选的模型名称，覆盖环境变量
        api_key: 可选的API密钥，覆盖环境变量
        
    Returns:
        GLMConfig: GLM配置对象
    """
    return GLMConfig(
        api_key=api_key or os.environ.get('ZHIPU_API_KEY', ''),
        model=model or os.environ.get('ZHIPU_TITLE_MODEL', 'glm-4.5-air'),
        min_interval=float(os.environ.get('GLM_MIN_INTERVAL', 0.4)),
        max_retries=int(os.environ.get('GLM_MAX_RETRIES', 3)),
        backoff_factor=float(os.environ.get('GLM_BACKOFF_FACTOR', 1.8))
    )


def get_feishu_config() -> FeishuConfig:
    """获取飞书配置
    
    从配置文件中加载飞书配置信息。
    
    Returns:
        FeishuConfig: 飞书配置对象
        
    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置格式错误
    """
    # TODO: 这里暂时使用现有的配置文件路径
    # 后续可以考虑迁移到更合适的位置
    config_path = Path(__file__).resolve().parents[3] / 'TaobaoUploader' / 'config.json'
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        feishu_config = config.get('feishu', {})
        if not feishu_config:
            raise ValueError("配置文件中缺少feishu配置段")
        
        return FeishuConfig(
            app_id=feishu_config['app_id'],
            app_secret=feishu_config['app_secret'],
            app_token=feishu_config['app_token'],
            table_id=feishu_config['table_id'],
            max_retries=int(os.environ.get('FEISHU_MAX_RETRIES', 3)),
            backoff_factor=float(os.environ.get('FEISHU_BACKOFF_FACTOR', 1.8))
        )
        
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"配置文件格式错误: {e}")


# 其他通用配置常量
DEFAULT_BATCH_SIZE = 30
DEFAULT_PAGE_SIZE = 500
DEFAULT_TIMEOUT = 30


# ============================================================================
# 新增：环境与网络校验功能
# ============================================================================

class GLMConnectionError(Exception):
    """智谱API连接错误"""
    pass


class EnvironmentValidationError(Exception):
    """环境校验错误"""
    pass


def validate_runtime() -> None:
    """
    环境与网络校验函数 - 步骤3实现
    
    检查项目：
    1. 检查 ZHIPU_API_KEY 是否配置
    2. 测试智谱API连接性
    
    Raises:
        EnvironmentValidationError: 环境配置错误
        GLMConnectionError: 智谱API连接失败
    """
    import requests
    
    # 1. 检查 ZHIPU_API_KEY 是否配置
    api_key = os.environ.get('ZHIPU_API_KEY')
    if not api_key or api_key.strip() == '':
        raise EnvironmentValidationError(
            "❌ ZHIPU_API_KEY 未配置或为空\n"
            "请确保 .env 文件中包含有效的智谱API密钥"
        )
    
    # 2. 测试智谱API连接性
    try:
        # 使用 HEAD 请求测试 API 可达性，超时设置短一些
        test_url = "https://open.bigmodel.cn"
        response = requests.head(
            test_url,
            timeout=5,  # 5秒超时
            allow_redirects=True
        )
        
        # 不要求特定状态码，只要能连接即可
        print("✅ 智谱API网络连接正常")
        
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.ConnectTimeout, 
        requests.exceptions.ReadTimeout,
        requests.exceptions.ProxyError
    ) as e:
        raise GLMConnectionError(
            f"❌ 智谱API网络连接失败：{e}\n"
            "请检查网络连接或代理设置"
        )
    except Exception as e:
        raise GLMConnectionError(
            f"❌ 智谱API连接测试异常：{e}"
        )
    
    print("✅ 环境校验通过")