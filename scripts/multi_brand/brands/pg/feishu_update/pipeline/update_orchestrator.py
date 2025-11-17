"""
更新流程编排器
"""

import json
from typing import Dict, List, Optional
from feishu_update.models.product import Product
from feishu_update.models.update_result import UpdateResult
from feishu_update.models.progress import ProgressEvent
from feishu_update.services.field_assembler import FieldAssembler
from feishu_update.services.title_generator import TitleGenerator
from feishu_update.services.translator import Translator
from feishu_update.clients.interfaces import GLMClientInterface, FeishuClientInterface
from feishu_update.loaders.factory import LoaderFactory
from feishu_update.pipeline.parallel_executor import ParallelTitleExecutor


class UpdateOrchestrator:
    """更新流程编排器（初始版）"""

    def __init__(
        self,
        glm_client: GLMClientInterface,
        feishu_client: FeishuClientInterface,
        title_generator: Optional[TitleGenerator] = None,
        translator: Optional[Translator] = None,
        field_assembler: Optional[FieldAssembler] = None,
        title_executor: Optional[ParallelTitleExecutor] = None,
        progress_callback: Optional[callable] = None,
    ) -> None:
        self.glm_client = glm_client
        self.feishu_client = feishu_client
        self.title_generator = title_generator or TitleGenerator(glm_client)
        self.translator = translator or Translator(glm_client)
        self.field_assembler = field_assembler or FieldAssembler(
            title_generator=self.title_generator,
            translator=self.translator,
        )
        self.title_executor = title_executor or ParallelTitleExecutor(
            generator=self.title_generator
        )
        self.progress_callback = progress_callback

    def execute(
        self,
        input_path: str,
        *,
        force_update: bool = False,
        title_only: bool = False,
        dry_run: bool = False
    ) -> UpdateResult:
        """执行完整更新流程"""
        # 1. 读取并解析产品数据
        data = json.load(open(input_path, 'r', encoding='utf-8'))
        loader = LoaderFactory.create(data)
        product_list = loader.parse(data)
        products = {p.product_id: p for p in product_list if p.product_id}

        # progress callback 通知加载完成
        if self.progress_callback:
            self.progress_callback(ProgressEvent(
                stage='load_complete',
                done=len(products),
                total=len(products),
                message=f"已加载 {len(products)} 个产品"
            ))

        # 2. 获取飞书现有记录
        existing_records = self.feishu_client.get_records()

        # 3. 根据 force_update/title_only 计算 target_fields 列表（与主脚本一致）
        fields_to_check = ['商品ID','商品标题','价格','性别','衣服分类','品牌名',
                           '颜色','尺码','图片URL','图片数量','详情页文字']
        if title_only:
            fields_to_check = ['商品标题']

        # 4. 计算候选产品：保持与主脚本相同逻辑（force_update / 空字段 / 新产品）
        candidate_ids = []
        skipped_ids = []
        missing_ids = []
        empty_fields_count = 0
        
        for product_id, product in products.items():
            if product_id in existing_records:
                existing_fields = existing_records[product_id]['fields']
                
                if force_update:
                    # 强制更新模式：直接加入候选
                    candidate_ids.append(product_id)
                else:
                    # 补空字段模式：只检查目标字段是否为空
                    empty_fields = self._has_empty_fields_to_fill(existing_fields, fields_to_check)
                    if empty_fields:
                        candidate_ids.append(product_id)
                        empty_fields_count += len(empty_fields)
                    else:
                        skipped_ids.append(product_id)
            else:
                # 缺失的记录应该被添加到候选更新列表中，以便创建新记录
                missing_ids.append(product_id)
                candidate_ids.append(product_id)

        if not candidate_ids:
            return UpdateResult(
                success_count=0,
                failed_batches=[],
                candidates_count=0,
                skipped_count=len(skipped_ids),
                title_failed=[],
                total_batches=0,
                log_path=None
            )

        # 5. 并行生成标题
        product_objs = [products[pid] for pid in candidate_ids if pid in products]
        title_results, title_failed = self.title_executor.execute(product_objs)

        # 6. 组装字段，构建 updates 列表（record_id + fields）
        updates = []
        for pid in candidate_ids:
            product = products.get(pid)
            if not product:
                continue
            record_info = existing_records.get(pid)
            pre_title = title_results.get(pid, '')
            fields = self.field_assembler.build_update_fields(
                product,
                pre_generated_title=pre_title,
                title_only=title_only
            )
            if not fields:
                continue
            if record_info:
                if (not force_update) and not self._fields_are_different(record_info['fields'], fields):
                    continue
                updates.append({'record_id': record_info['record_id'], 'fields': fields, 'product_id': pid})
            else:
                updates.append({'record_id': None, 'fields': fields, 'product_id': pid})

        # 7. 调用 FeishuClient 批量更新
        if dry_run:
            return UpdateResult(
                success_count=0,
                failed_batches=[],
                candidates_count=len(candidate_ids),
                skipped_count=len(skipped_ids),
                title_failed=title_failed,
                total_batches=0,
                log_path=None
            )
        
        result = self.feishu_client.batch_update(updates, batch_size=30)

        # 8. 返回 UpdateResult
        return UpdateResult(
            success_count=result['success_count'],
            failed_batches=result['failed_batches'],
            candidates_count=len(candidate_ids),
            skipped_count=len(skipped_ids),
            title_failed=title_failed,
            total_batches=result['total_batches'],
            log_path=None
        )

    def _fields_are_different(self, existing_fields: Dict, new_fields: Dict) -> bool:
        """检查字段是否有变化"""
        for key, new_value in new_fields.items():
            existing_value = existing_fields.get(key, '')
            # 简单的字符串比较，忽略空值差异
            if str(new_value).strip() != str(existing_value).strip():
                return True
        return False

    def _has_empty_fields_to_fill(self, existing_fields: Dict, target_fields: List[str]) -> List[str]:
        """
        检查指定字段中哪些为空需要补齐
        
        Args:
            existing_fields: 飞书现有字段数据
            target_fields: 需要检查的字段列表
        
        Returns:
            List[str]: 需要补齐的空字段列表
        """
        empty_fields = []
        for field in target_fields:
            existing_value = existing_fields.get(field, '').strip()
            if not existing_value:
                empty_fields.append(field)
        return empty_fields