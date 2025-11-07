"""测试用的飞书客户端模拟实现

此模块提供一个不发起网络请求的DummyFeishuClient，
主要用于dry-run测试和开发环境。
"""

from typing import Dict, List, Any
from .interfaces import FeishuClientInterface


class DummyFeishuClient(FeishuClientInterface):
    """飞书客户端的模拟实现
    
    用于测试和dry-run模式，不发起真实的网络请求。
    """
    
    def __init__(self, **kwargs):
        """初始化DummyFeishuClient
        
        Args:
            **kwargs: 兼容真实客户端的参数（会被忽略）
        """
        # 忽略所有参数，不做任何网络配置
        pass
    
    def get_records(self) -> Dict[str, Dict]:
        """获取飞书表中的所有记录（模拟）
        
        Returns:
            Dict[str, Dict]: 空记录映射，表示表中没有现有记录
                这样所有产品都会被当作新产品处理
        """
        # 返回空字典，表示表中没有现有记录
        # 这会让所有产品都被识别为候选更新对象
        return {}
    
    def batch_update(self, records: List[Dict], batch_size: int = 30) -> Dict[str, Any]:
        """批量更新记录（模拟）
        
        Args:
            records: 待更新的记录列表
            batch_size: 批次大小
            
        Returns:
            Dict[str, Any]: 模拟的更新结果统计
        """
        # 模拟成功更新所有记录
        total_records = len(records)
        total_batches = (total_records + batch_size - 1) // batch_size if total_records > 0 else 0
        
        return {
            'success_count': total_records,
            'failed_batches': [],
            'total_batches': total_batches
        }
    
    def batch_create(self, records: List[Dict], batch_size: int = 30) -> Dict[str, Any]:
        """批量创建记录（模拟）
        
        Args:
            records: 待创建的记录列表，每个记录包含fields和product_id
            batch_size: 批次大小
            
        Returns:
            Dict[str, Any]: 模拟的创建结果统计
        """
        # 模拟成功创建所有记录
        total_records = len(records)
        total_batches = (total_records + batch_size - 1) // batch_size if total_records > 0 else 0
        
        return {
            'success_count': total_records,
            'failed_batches': [],
            'total_batches': total_batches
        }