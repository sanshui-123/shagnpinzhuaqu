"""
翻译服务
"""

from typing import Dict, Optional
from . import translator_v2


class Translator:
    """商品描述翻译服务的轻量封装。

    当前阶段继续复用 translator_v2.translate_description，后续阶段会通过注入的 GLM 客户端实现统一调用。
    """

    def __init__(self, glm_client: Optional[object] = None) -> None:
        # 保留占位，后续阶段会改为真正的 GLM 客户端注入
        self._glm_client = glm_client

    def translate_description(self, product: Dict) -> str:
        """翻译商品描述"""
        # TODO: 后续阶段使用 self._glm_client.translate
        return translator_v2.translate_description(product)

    def validate_result(self, translated: str) -> bool:
        """校验翻译结果格式"""
        return translator_v2.validate_translation_format(translated)