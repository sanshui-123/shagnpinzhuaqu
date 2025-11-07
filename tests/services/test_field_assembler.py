"""FieldAssembler 测试用例

测试 FieldAssembler 的字段组装功能
"""

import pytest

from feishu_update.services.field_assembler import FieldAssembler
from feishu_update.services.title_generator import TitleGenerator
from feishu_update.services.translator import Translator
from tests.fixtures.products import load_fixture


# 如果不想被真的调用 GLM/翻译，可用简单的替身类
class DummyTitleGenerator(TitleGenerator):
    def __init__(self):
        pass
    
    def generate(self, product):
        return "测试标题"


class DummyTranslator(Translator):
    def __init__(self):
        pass
    
    def translate_description(self, product):
        return "【产品描述】测试描述\n【产品亮点】✓ 测试亮点\n【材质信息】测试材质"


class TestFieldAssembler:
    """FieldAssembler 测试类"""
    
    def test_build_fields_basic(self):
        """测试基本字段组装功能"""
        data = load_fixture("sample_product_details.json")
        product = data["product"]  # loader 返回 dataclass，这里我们先直接用 dict 模拟

        assembler = FieldAssembler(
            title_generator=DummyTitleGenerator(),
            translator=DummyTranslator(),
        )
        fields = assembler.build_update_fields(product, pre_generated_title=None, title_only=False)

        assert fields["商品标题"] == "测试标题"
        assert fields["详情页文字"].startswith("【产品描述】")
        assert "价格" in fields
        assert "颜色" in fields
        assert "尺码" in fields
        assert "图片URL" in fields

    def test_title_only_mode(self):
        """测试仅标题模式"""
        data = load_fixture("sample_product_details.json")
        product = data["product"]
        assembler = FieldAssembler(DummyTitleGenerator(), DummyTranslator())
        fields = assembler.build_update_fields(product, title_only=True)
        assert list(fields.keys()) == ["商品标题"]

    def test_pre_generated_title(self):
        """测试预生成标题功能"""
        data = load_fixture("sample_product_details.json")
        product = data["product"]
        assembler = FieldAssembler(DummyTitleGenerator(), DummyTranslator())
        fields = assembler.build_update_fields(product, pre_generated_title="缓存标题")
        assert fields["商品标题"] == "缓存标题"