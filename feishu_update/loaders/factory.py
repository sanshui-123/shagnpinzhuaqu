"""加载器工厂

提供自动格式检测和对应加载器创建功能
"""

import logging
from typing import Dict, Any, List, Type
from .base import BaseProductLoader
from .detailed import DetailedProductLoader
from .summarized import SummarizedProductLoader
from .link_only import LinkOnlyProductLoader

logger = logging.getLogger(__name__)


class LoaderFactory:
    """产品数据加载器工厂
    
    根据数据格式自动选择合适的加载器
    """
    
    # 注册的加载器类列表，按优先级排序
    _loaders: List[Type[BaseProductLoader]] = [
        DetailedProductLoader,     # 优先检测详细格式
        SummarizedProductLoader,   # 其次是汇总格式
        LinkOnlyProductLoader      # 最后是仅链接格式
    ]
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> BaseProductLoader:
        """根据数据格式创建对应的加载器
        
        Args:
            data: 待处理的数据字典
            
        Returns:
            BaseProductLoader: 适合处理该数据的加载器实例
            
        Raises:
            ValueError: 当没有找到合适的加载器时
        """
        for loader_class in cls._loaders:
            loader = loader_class()
            if loader.supports(data):
                logger.info(f"选择加载器: {loader_class.__name__}")
                return loader
        
        # 如果没有找到合适的加载器，抛出异常并列出支持的格式
        supported_formats = [
            "DetailedProductLoader: 详细产品数据，包含{product, variants, scrapeInfo}或{products: {...}}",
            "SummarizedProductLoader: 汇总产品数据，有基本信息但缺少详细变体",
            "LinkOnlyProductLoader: 仅链接数据，只包含链接和最基本信息"
        ]
        error_msg = f"未找到支持此数据格式的加载器。\n\n支持的格式：\n" + "\n".join(f"- {fmt}" for fmt in supported_formats)
        raise ValueError(error_msg)
    
    @classmethod
    def detect_format(cls, data: Dict[str, Any]) -> str:
        """检测数据格式
        
        Args:
            data: 待检测的数据字典
            
        Returns:
            str: 数据格式名称，如果无法识别则返回 'unknown'
        """
        try:
            loader = cls.create(data)
            return loader.get_format_name()
        except ValueError:
            return 'unknown'
    
    @classmethod
    def register_loader(cls, loader_class: Type[BaseProductLoader], priority: int = None):
        """注册新的加载器类
        
        Args:
            loader_class: 要注册的加载器类
            priority: 优先级，数字越小优先级越高。如果为None，添加到列表末尾
        """
        if not issubclass(loader_class, BaseProductLoader):
            raise ValueError("加载器类必须继承自 BaseProductLoader")
        
        if loader_class in cls._loaders:
            logger.warning(f"加载器 {loader_class.__name__} 已经注册")
            return
        
        if priority is None:
            cls._loaders.append(loader_class)
        else:
            cls._loaders.insert(priority, loader_class)
        
        logger.info(f"注册加载器: {loader_class.__name__}")
    
    @classmethod
    def get_available_loaders(cls) -> List[str]:
        """获取所有可用的加载器名称
        
        Returns:
            List[str]: 加载器名称列表
        """
        return [loader.__name__ for loader in cls._loaders]
    
    @classmethod
    def create_by_name(cls, loader_name: str) -> BaseProductLoader:
        """根据名称创建加载器
        
        Args:
            loader_name: 加载器类名
            
        Returns:
            BaseProductLoader: 加载器实例
            
        Raises:
            ValueError: 当找不到指定名称的加载器时
        """
        for loader_class in cls._loaders:
            if loader_class.__name__ == loader_name:
                return loader_class()
        
        raise ValueError(f"未找到名为 '{loader_name}' 的加载器")
    
    @classmethod
    def validate_data_with_all_loaders(cls, data: Dict[str, Any]) -> Dict[str, bool]:
        """使用所有加载器验证数据
        
        Args:
            data: 待验证的数据
            
        Returns:
            Dict[str, bool]: 每个加载器的支持情况
        """
        results = {}
        for loader_class in cls._loaders:
            loader = loader_class()
            try:
                supports = loader.supports(data)
                results[loader_class.__name__] = supports
            except Exception as e:
                logger.error(f"使用 {loader_class.__name__} 验证数据时出错: {e}")
                results[loader_class.__name__] = False
        
        return results