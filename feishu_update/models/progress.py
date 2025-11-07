"""进度事件数据模型

定义批量更新过程中的进度事件数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum


class ProgressEventType(Enum):
    """进度事件类型"""
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PROGRESS_UPDATE = "progress_update"
    BATCH_COMPLETED = "batch_completed"


@dataclass
class ProgressEvent:
    """进度事件"""
    # 事件基本信息
    event_type: ProgressEventType = ProgressEventType.PROGRESS_UPDATE
    timestamp: str = ""
    
    # 进度统计
    total_count: int = 0               # 总数量
    processed_count: int = 0           # 已处理数量
    success_count: int = 0             # 成功数量
    failed_count: int = 0              # 失败数量
    
    # 当前处理项目
    current_product_id: str = ""       # 当前处理的产品ID
    current_product_name: str = ""     # 当前处理的产品名称
    
    # 消息和状态
    message: str = ""                  # 状态消息
    detail: str = ""                   # 详细信息
    
    # 性能指标
    elapsed_time: float = 0.0          # 已用时间（秒）
    estimated_remaining: float = 0.0   # 预估剩余时间（秒）
    avg_processing_time: float = 0.0   # 平均处理时间（秒）
    
    # 额外数据
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def progress_percentage(self) -> float:
        """计算进度百分比"""
        if self.total_count == 0:
            return 0.0
        return (self.processed_count / self.total_count) * 100
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.processed_count == 0:
            return 0.0
        return (self.success_count / self.processed_count) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'event_type': self.event_type.value if isinstance(self.event_type, ProgressEventType) else self.event_type,
            'timestamp': self.timestamp,
            'total_count': self.total_count,
            'processed_count': self.processed_count,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'current_product_id': self.current_product_id,
            'current_product_name': self.current_product_name,
            'message': self.message,
            'detail': self.detail,
            'elapsed_time': self.elapsed_time,
            'estimated_remaining': self.estimated_remaining,
            'avg_processing_time': self.avg_processing_time,
            'progress_percentage': self.progress_percentage,
            'success_rate': self.success_rate,
            'extra_data': self.extra_data
        }
    
    @classmethod
    def started_event(cls, total_count: int, timestamp: str = "", message: str = "开始批量更新") -> 'ProgressEvent':
        """创建开始事件"""
        return cls(
            event_type=ProgressEventType.STARTED,
            timestamp=timestamp,
            total_count=total_count,
            message=message
        )
    
    @classmethod
    def processing_event(cls, product_id: str, product_name: str, processed_count: int, 
                        total_count: int, timestamp: str = "") -> 'ProgressEvent':
        """创建处理中事件"""
        return cls(
            event_type=ProgressEventType.PROCESSING,
            timestamp=timestamp,
            total_count=total_count,
            processed_count=processed_count,
            current_product_id=product_id,
            current_product_name=product_name,
            message=f"正在处理: {product_name}"
        )
    
    @classmethod
    def completed_event(cls, total_count: int, success_count: int, failed_count: int,
                       elapsed_time: float, timestamp: str = "") -> 'ProgressEvent':
        """创建完成事件"""
        return cls(
            event_type=ProgressEventType.COMPLETED,
            timestamp=timestamp,
            total_count=total_count,
            processed_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            elapsed_time=elapsed_time,
            message=f"批量更新完成: 成功 {success_count}/{total_count}"
        )
    
    @classmethod
    def progress_update_event(cls, processed_count: int, total_count: int, success_count: int,
                             failed_count: int, elapsed_time: float = 0.0, timestamp: str = "") -> 'ProgressEvent':
        """创建进度更新事件"""
        return cls(
            event_type=ProgressEventType.PROGRESS_UPDATE,
            timestamp=timestamp,
            total_count=total_count,
            processed_count=processed_count,
            success_count=success_count,
            failed_count=failed_count,
            elapsed_time=elapsed_time,
            message=f"进度: {processed_count}/{total_count} (成功: {success_count}, 失败: {failed_count})"
        )