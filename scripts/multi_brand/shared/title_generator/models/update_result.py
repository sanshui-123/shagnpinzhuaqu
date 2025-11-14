"""
Pipeline 更新结果数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class UpdateResult:
    """一次更新流程的聚合结果"""

    success_count: int = 0
    failed_batches: List[Dict[str, Any]] = field(default_factory=list)
    candidates_count: int = 0
    skipped_count: int = 0
    title_failed: List[str] = field(default_factory=list)
    total_batches: int = 0
    log_path: Optional[str] = None

    def to_summary(self, verbose: bool = False) -> str:
        lines = [
            "=" * 60,
            "📈 更新处理汇总",
            "=" * 60,
            f"✓ 成功更新: {self.success_count} 条",
            f"📊 候选产品: {self.candidates_count} 个",
        ]

        if self.skipped_count:
            lines.append(f"➤ 跳过记录: {self.skipped_count} 条")
        if self.title_failed:
            lines.append(f"⚠️ 标题失败: {len(self.title_failed)} 条")
            if verbose:
                lines.append(f"   失败ID: {', '.join(self.title_failed[:10])}")
        if self.failed_batches:
            lines.append(f"✗ 失败批次: {len(self.failed_batches)}")
        if self.total_batches:
            lines.append(f"📦 批次数量: {self.total_batches}")
        if self.log_path:
            lines.append(f"📄 日志文件: {self.log_path}")
        lines.append("=" * 60)
        return "\n".join(lines)