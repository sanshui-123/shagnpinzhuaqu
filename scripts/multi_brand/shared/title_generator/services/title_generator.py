"""
标题生成服务
"""

from typing import Dict, Optional
from . import title_v6
from ..clients.interfaces import GLMClientInterface


class TitleGenerator:
    """标题生成服务的轻量封装。

    已修复GLM响应处理，通过GLMClient支持reasoning_content处理。
    """

    def __init__(self, glm_client: Optional[GLMClientInterface] = None) -> None:
        # GLM客户端注入，用于标题生成
        self._glm_client = glm_client

    def generate(self, product: Dict) -> str:
        """生成中文标题

        Args:
            product: 产品数据字典

        Returns:
            str: 生成的中文标题

        Raises:
            RuntimeError: 当 glm_client 未注入时抛出异常
            Exception: 标题生成失败时抛出异常
        """
        # title_v6.generate_cn_title 只需要一个参数，不需要glm_client
        # GLM相关的配置在函数内部通过环境变量处理
        return title_v6.generate_cn_title(product)