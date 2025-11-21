"""
兼容层：统一复用 tongyong_feishu_update 的标题生成实现
"""

from tongyong_feishu_update.services.title_v6 import (  # noqa: F401
    build_smart_prompt,
    call_glm_api,
    clean_title,
    optimize_title,
    validate_title,
    generate_cn_title,
    TitleGenerationError,
)

__all__ = [
    "build_smart_prompt",
    "call_glm_api",
    "clean_title",
    "optimize_title",
    "validate_title",
    "generate_cn_title",
    "TitleGenerationError",
]
