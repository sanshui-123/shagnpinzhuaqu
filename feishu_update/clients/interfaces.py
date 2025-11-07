"""飞书更新系统客户端接口定义

本模块定义了GLM和飞书客户端的抽象接口，确保客户端实现的一致性和可替换性。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class GLMClientInterface(ABC):
    """GLM客户端抽象接口
    
    提供标题生成和翻译功能的统一接口。
    """
    
    @abstractmethod
    def generate_title(
        self, 
        prompt: str, 
        *, 
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.3
    ) -> str:
        """生成中文商品标题
        
        Args:
            prompt: 标题生成提示词
            model: 可选的模型名称，覆盖默认模型
            max_tokens: 最大令牌数
            temperature: 温度参数，控制随机性
            
        Returns:
            str: 生成的中文标题
        """
        pass
    
    @abstractmethod
    def translate(
        self, 
        prompt: str, 
        *, 
        model: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.2
    ) -> str:
        """翻译文本
        
        Args:
            prompt: 翻译提示词
            model: 可选的模型名称，覆盖默认模型
            max_tokens: 最大令牌数
            temperature: 温度参数，控制随机性
            
        Returns:
            str: 翻译结果
        """
        pass


class FeishuClientInterface(ABC):
    """飞书客户端抽象接口
    
    提供飞书表格记录的获取和更新功能。
    """
    
    @abstractmethod
    def get_records(self) -> Dict[str, Dict]:
        """获取飞书表中的所有记录
        
        Returns:
            Dict[str, Dict]: 记录映射，key为productId，value为包含record_id和fields的字典
                格式: {productId: {"record_id": str, "fields": Dict}}
        """
        pass
    
    @abstractmethod
    def batch_update(self, records: List[Dict], batch_size: int = 30) -> Dict[str, Any]:
        """批量更新记录
        
        Args:
            records: 待更新的记录列表，每个记录包含record_id和fields
            batch_size: 批次大小
            
        Returns:
            Dict[str, Any]: 更新结果统计
                格式: {
                    'success_count': int,
                    'failed_batches': List[Dict],
                    'total_batches': int
                }
        """
        pass
    
    @abstractmethod
    def batch_create(self, records: List[Dict], batch_size: int = 30) -> Dict[str, Any]:
        """批量创建记录
        
        Args:
            records: 待创建的记录列表，每个记录包含fields和product_id
            batch_size: 批次大小
            
        Returns:
            Dict[str, Any]: 创建结果统计
                格式: {
                    'success_count': int,
                    'failed_batches': List[Dict],
                    'total_batches': int
                }
        """
        pass