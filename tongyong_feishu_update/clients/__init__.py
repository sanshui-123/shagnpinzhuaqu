"""客户端包

提供GLM和飞书客户端的统一接口和工厂函数。
"""

import os
from typing import Optional

from .interfaces import GLMClientInterface, FeishuClientInterface
from .glm_client import GLMClient
from .feishu_client import FeishuClient
from .dummy_feishu_client import DummyFeishuClient
from ..config.settings import get_glm_config, get_feishu_config


def create_glm_client(
    model: Optional[str] = None, 
    api_key: Optional[str] = None
) -> GLMClientInterface:
    """创建GLM客户端实例
    
    Args:
        model: 可选的模型名称，覆盖配置中的默认模型
        api_key: 可选的API密钥，覆盖环境变量
        
    Returns:
        GLMClientInterface: GLM客户端接口实例
    """
    cfg = get_glm_config(model=model, api_key=api_key)
    
    if not cfg.api_key:
        raise ValueError("GLM API密钥未设置，请检查ZHIPU_API_KEY环境变量")
    
    return GLMClient(
        api_key=cfg.api_key,
        model=cfg.model,
        min_interval=cfg.min_interval,
        max_retries=cfg.max_retries,
        backoff_factor=cfg.backoff_factor,
    )


def create_feishu_client() -> FeishuClientInterface:
    """创建飞书客户端实例
    
    根据环境变量FEISHU_CLIENT的值决定使用真实客户端还是模拟客户端：
    - FEISHU_CLIENT=dummy: 使用DummyFeishuClient（用于测试和dry-run）
    - 其他值或未设置: 使用真实的FeishuClient
    
    Returns:
        FeishuClientInterface: 飞书客户端接口实例
    """
    client_type = os.environ.get('FEISHU_CLIENT', '').lower()
    
    if client_type == 'dummy':
        # 使用模拟客户端，不发起网络请求
        return DummyFeishuClient()
    else:
        # 使用真实客户端
        cfg = get_feishu_config()
        
        return FeishuClient(
            app_id=cfg.app_id,
            app_secret=cfg.app_secret,
            app_token=cfg.app_token,
            table_id=cfg.table_id,
            max_retries=cfg.max_retries,
            backoff_factor=cfg.backoff_factor,
        )


# 导出主要接口和工厂函数
__all__ = [
    'GLMClientInterface',
    'FeishuClientInterface', 
    'GLMClient',
    'FeishuClient',
    'create_glm_client',
    'create_feishu_client',
]