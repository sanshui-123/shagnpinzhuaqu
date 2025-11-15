"""抽象产品数据加载器

定义所有产品数据加载器的基类和接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..models import Product


class BaseProductLoader(ABC):
    """抽象产品数据加载器基类
    
    所有具体的产品数据加载器都应该继承此类并实现其抽象方法
    """
    
    @abstractmethod
    def supports(self, data: Dict[str, Any]) -> bool:
        """检查此加载器是否支持给定的数据格式
        
        Args:
            data: 待检查的数据字典
            
        Returns:
            bool: 如果支持此数据格式返回True，否则返回False
        """
        pass
    
    @abstractmethod
    def parse(self, data: Dict[str, Any]) -> List[Product]:
        """解析数据并返回Product对象列表
        
        Args:
            data: 待解析的数据字典
            
        Returns:
            List[Product]: 解析后的Product对象列表
            
        Raises:
            ValueError: 当数据格式不受支持或解析失败时
        """
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据的基本结构
        
        Args:
            data: 待验证的数据字典
            
        Returns:
            bool: 验证通过返回True，否则返回False
        """
        if not isinstance(data, dict):
            return False
        return True
    
    def get_format_name(self) -> str:
        """获取此加载器处理的数据格式名称
        
        Returns:
            str: 格式名称
        """
        return self.__class__.__name__.replace('ProductLoader', '').lower()
    
    def preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数据预处理（可选覆盖）
        
        Args:
            data: 原始数据
            
        Returns:
            Dict[str, Any]: 预处理后的数据
        """
        return data
    
    def postprocess_products(self, products: List[Product]) -> List[Product]:
        """产品列表后处理（可选覆盖）
        
        Args:
            products: 原始产品列表
            
        Returns:
            List[Product]: 后处理后的产品列表
        """
        return products