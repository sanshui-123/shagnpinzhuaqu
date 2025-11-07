"""LoaderFactory 测试用例

测试 LoaderFactory 的格式检测和解析功能
"""

import pytest
from feishu_update.loaders.factory import LoaderFactory
from feishu_update.models.product import Product
from tests.fixtures.products import load_fixture


class TestLoaderFactory:
    """LoaderFactory 测试类"""
    
    def test_detect_detailed_format(self):
        """测试检测详细产品格式"""
        data = load_fixture('sample_product_details.json')
        format_name = LoaderFactory.detect_format(data)
        assert format_name == "detailed"
    
    def test_detect_summarized_format(self):
        """测试检测汇总产品格式"""
        data = load_fixture('sample_summarized_products.json')
        format_name = LoaderFactory.detect_format(data)
        assert format_name == "summarized"
    
    def test_detect_link_only_format(self):
        """测试检测仅链接格式"""
        data = load_fixture('sample_raw_links.json')
        format_name = LoaderFactory.detect_format(data)
        # 根据base.py的get_format_name方法，LinkOnlyProductLoader会返回"linkonly"
        assert format_name in ["linkonly", "link_only"]  # 兼容两种可能的返回值
    
    def test_parse_detailed_products(self):
        """测试解析详细产品数据"""
        data = load_fixture('sample_product_details.json')
        loader = LoaderFactory.create(data)
        products = loader.parse(data)
        
        # 验证返回的是列表且长度大于0
        assert isinstance(products, list)
        assert len(products) > 0
        
        # 验证每个元素都是Product实例
        for product in products:
            assert isinstance(product, Product)
            # 验证关键字段非空
            assert product.product_id  # product_id非空
            assert product.product_name  # product_name非空
    
    def test_parse_link_only_products(self):
        """测试解析仅链接产品数据"""
        data = load_fixture('sample_raw_links.json')
        loader = LoaderFactory.create(data)
        products = loader.parse(data)
        
        # 验证返回的是列表且长度大于0
        assert isinstance(products, list)
        assert len(products) > 0
        
        # 验证每个Product对象的detail_url与原数据一致
        original_products = data['products']
        assert len(products) == len(original_products)
        
        for i, product in enumerate(products):
            assert isinstance(product, Product)
            expected_url = original_products[i]['url']
            assert product.detail_url == expected_url
    
    def test_create_unknown_format(self):
        """测试创建未知格式的数据时抛出异常"""
        unknown_data = {"unknown_field": "unknown_value"}
        
        with pytest.raises(ValueError) as exc_info:
            LoaderFactory.create(unknown_data)
        
        assert "未找到支持此数据格式的加载器" in str(exc_info.value)
    
    def test_detect_unknown_format(self):
        """测试检测未知格式返回'unknown'"""
        unknown_data = {"unknown_field": "unknown_value"}
        format_name = LoaderFactory.detect_format(unknown_data)
        assert format_name == "unknown"
    
    def test_get_available_loaders(self):
        """测试获取可用加载器列表"""
        loaders = LoaderFactory.get_available_loaders()
        assert isinstance(loaders, list)
        assert len(loaders) > 0
        assert "DetailedProductLoader" in loaders
        assert "SummarizedProductLoader" in loaders
        assert "LinkOnlyProductLoader" in loaders
    
    def test_create_by_name(self):
        """测试根据名称创建加载器"""
        loader = LoaderFactory.create_by_name("DetailedProductLoader")
        assert loader.__class__.__name__ == "DetailedProductLoader"
        
        with pytest.raises(ValueError):
            LoaderFactory.create_by_name("NonExistentLoader")