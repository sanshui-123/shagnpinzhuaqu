"""DetailedProductLoader 测试用例

针对 DetailedProductLoader 的细节测试
"""

import pytest
from feishu_update.loaders.detailed import DetailedProductLoader
from feishu_update.models.product import Product
from tests.fixtures.products import load_fixture


class TestDetailedProductLoader:
    """DetailedProductLoader 测试类"""
    
    def test_supports_with_product_variants_scrapeinfo(self):
        """测试supports方法识别包含product、variants、scrapeInfo的数据"""
        data = load_fixture('sample_product_details.json')
        loader = DetailedProductLoader()
        
        # 验证supports方法返回True
        assert loader.supports(data) is True
    
    def test_supports_returns_false_for_invalid_data(self):
        """测试supports方法对无效数据返回False"""
        loader = DetailedProductLoader()
        
        # 测试空字典
        assert loader.supports({}) is False
        
        # 测试缺少关键字段的数据
        incomplete_data = {"product": {"productId": "test"}}
        assert loader.supports(incomplete_data) is False
    
    def test_parse_single_product_fields(self):
        """测试解析单个产品并验证关键字段"""
        data = load_fixture('sample_product_details.json')
        loader = DetailedProductLoader()
        products = loader.parse(data)
        
        # 验证返回列表，取第一个Product
        assert isinstance(products, list)
        assert len(products) > 0
        
        product = products[0]
        assert isinstance(product, Product)
        
        # 验证关键字段正确填充
        assert product.product_id  # product_id非空
        assert isinstance(product.colors, list)  # colors是列表
        assert isinstance(product.sizes, list)   # sizes是列表
        assert hasattr(product.images, 'all')    # images有all属性
        assert product.stock_status  # stock_status非空
        
        # 验证Product的__getitem__兼容性
        assert product['productId'] == product.product_id
        assert product['productName'] == product.product_name
        assert product['detailUrl'] == product.detail_url
    
    def test_parse_handles_missing_optional_fields(self):
        """测试解析时处理缺失的可选字段"""
        # 创建一个最小化的测试数据
        minimal_data = {
            "product": {
                "productId": "TEST001",
                "productName": "测试产品"
            },
            "variants": [],
            "scrapeInfo": {
                "url": "https://example.com/test",
                "timestamp": "2025-11-04T12:00:00.000Z"
            }
        }
        
        loader = DetailedProductLoader()
        products = loader.parse(minimal_data)
        
        assert len(products) == 1
        product = products[0]
        
        # 验证必填字段
        assert product.product_id == "TEST001"
        assert product.product_name == "测试产品"
        assert product.detail_url == "https://example.com/test"
        
        # 验证可选字段有默认值
        assert product.description == ""
        assert product.brand == ""
        assert product.category == ""
        assert isinstance(product.variants, list)
        assert len(product.variants) == 0
    
    def test_get_method_with_default_values(self):
        """测试Product的get方法提供默认值"""
        data = load_fixture('sample_product_details.json')
        loader = DetailedProductLoader()
        products = loader.parse(data)
        
        product = products[0]
        
        # 测试get方法
        assert product.get('productId') == product.product_id
        assert product.get('nonExistentField', 'default') == 'default'
        assert product.get('productName', 'fallback') == product.product_name
    
    def test_has_variants_method(self):
        """测试has_variants方法"""
        data = load_fixture('sample_product_details.json')
        loader = DetailedProductLoader()
        products = loader.parse(data)
        
        product = products[0]
        
        # 根据样例数据中的variants决定预期结果
        # 如果variants列表为空，should return False；否则True
        expected = len(product.variants) > 0
        assert product.has_variants() == expected
    
    def test_format_name(self):
        """测试get_format_name方法"""
        loader = DetailedProductLoader()
        assert loader.get_format_name() == "detailed"
    
    def test_parse_with_unsupported_data_raises_error(self):
        """测试用不支持的数据调用parse时抛出错误"""
        loader = DetailedProductLoader()
        unsupported_data = {"invalid": "data"}
        
        with pytest.raises(ValueError) as exc_info:
            loader.parse(unsupported_data)
        
        assert "数据格式不受此加载器支持" in str(exc_info.value)