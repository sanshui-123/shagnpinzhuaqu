"""
兼容层：统一复用 tongyong_feishu_update 的标题生成实现
"""

from tongyong_feishu_update.services.title_generator import TitleGenerator  # noqa: F401

__all__ = ["TitleGenerator"]
