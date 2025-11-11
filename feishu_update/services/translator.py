"""
翻译服务
"""

import os
from typing import Dict, Optional

from . import translator_v2
from .translation_cache import TranslationCache

_ENV_VARS = ('ZHIPU_API_KEY', 'GLM_API_KEY')


class Translator:
    """商品描述翻译服务的轻量封装"""

    def __init__(
        self,
        glm_client: Optional[object] = None,
        cache: Optional[TranslationCache] = None,
    ) -> None:
        self._glm_client = glm_client
        self._cache = cache or TranslationCache()
        self._env_checked = False

    def _ensure_env_ready(self) -> None:
        if self._env_checked:
            return
        if not any(os.environ.get(var) for var in _ENV_VARS):
            raise EnvironmentError(
                "GLM 翻译依赖的 ZHIPU_API_KEY 或 GLM_API_KEY 未配置，请先在环境变量或 callaway.env 中设置。"
            )
        self._env_checked = True

    def translate_description(self, product: Dict) -> str:
        """翻译商品描述，优先命中缓存"""
        cleaned_description = translator_v2.extract_source_description(product)
        if not cleaned_description:
            return ""

        product_id = str(product.get('productId') or product.get('product_id') or 'unknown')
        cached = self._cache.get(product_id, cleaned_description)
        if cached:
            return cached

        self._ensure_env_ready()

        translated = translator_v2.translate_description(product)
        if not translated:
            raise RuntimeError(f"GLM 翻译失败，productId={product_id}")

        self._cache.set(product_id, cleaned_description, translated)
        return translated

    def validate_result(self, translated: str) -> bool:
        """校验翻译结果格式"""
        return translator_v2.validate_translation_format(translated)
