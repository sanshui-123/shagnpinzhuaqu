"""
更新流程编排器
"""

import json
from typing import Dict, List, Optional
from ..models.product import Product
from ..models.update_result import UpdateResult
from ..models.progress import ProgressEvent
from ..services.field_assembler import FieldAssembler
from ..services.title_generator import TitleGenerator
from ..services.translator import Translator
from ..services.detail_fetcher import DetailFetcher
from ..clients.interfaces import GLMClientInterface, FeishuClientInterface
from ..loaders.factory import LoaderFactory
from .parallel_executor import ParallelTitleExecutor


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
        detail_fetcher: Optional[DetailFetcher] = None,
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
        self.detail_fetcher = detail_fetcher or DetailFetcher()
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
            event = ProgressEvent.progress_update_event(
                processed_count=len(products),
                total_count=len(products),
                success_count=0,
                failed_count=0
            )
            event.message = f"已加载 {len(products)} 个产品"
            self.progress_callback(event)

        # 2. 获取飞书现有记录
        existing_records = self.feishu_client.get_records()
        
        # 3. 确保记录存在（步骤4实现）- 在正式处理前补齐缺失记录
        missing_ids = [pid for pid in products.keys() if pid not in existing_records]
        if missing_ids:
            print(f"发现 {len(missing_ids)} 个缺失的product_id，正在批量创建...")
            create_records = []
            for pid in missing_ids:
                product = products[pid]
                create_records.append({
                    'fields': {
                        '商品ID': pid,
                        '商品链接': product.detail_url or '',
                        '品牌名': product.brand or '',
                        # 设置其他必要的最小字段
                    },
                    'product_id': pid
                })
            
            if not dry_run:
                create_result = self.feishu_client.batch_create(create_records, batch_size=30)
                if create_result.get('success_count', 0) > 0:
                    print(f"✅ 成功创建 {create_result['success_count']} 条新记录")
                    # 重新获取飞书记录，包含新创建的记录
                    existing_records = self.feishu_client.get_records()
                else:
                    raise RuntimeError("缺失记录创建失败，无法继续处理")
            else:
                print(f"干运行模式：跳过创建 {len(missing_ids)} 条缺失记录")

        # 4. 根据 force_update/title_only 计算 target_fields 列表（与主脚本一致）
        fields_to_check = ['商品ID','商品标题','价格','性别','衣服分类','品牌名',
                           '颜色','尺码','图片URL','图片数量','详情页文字','商品链接','尺码表']
        if title_only:
            fields_to_check = ['商品标题']

        # 5. 计算候选产品：保持与主脚本相同逻辑（force_update / 空字段 / 新产品）
        candidate_ids = []
        skipped_ids = []
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
                # 此时不应该有缺失记录，因为已经在步骤3创建了
                print(f"警告：产品 {product_id} 在缺失记录创建后仍不存在于 existing_records 中")
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

        # 6. 并行生成标题
        product_objs = [products[pid] for pid in candidate_ids if pid in products]
        title_results, title_failed = self.title_executor.execute(product_objs)

        # 6.5. 抓取并补充产品详情数据
        print("🔍 检查并抓取缺失的产品详情...")
        enhanced_products_list = []
        for pid in candidate_ids:
            product = products.get(pid)
            if not product:
                continue
            
            # 转换Product对象为字典格式（如果需要的话）
            if hasattr(product, '__dict__'):
                # 获取 extra 字段中的数据
                extra = getattr(product, 'extra', {})

                product_dict = {
                    'productId': product.product_id,
                    'detailUrl': product.detail_url,
                    'colors': getattr(product, 'colors', []),
                    'sizes': getattr(product, 'sizes', []),
                    'gender': getattr(product, 'gender', ''),  # 🎯 修复：添加缺失的gender字段
                    'imageUrls': getattr(product, 'imageUrls', []),  # 新增：图片URL列表
                    'sizeChart': getattr(product, 'sizeChart', {}),  # 新增：尺码表
                    'imagesMetadata': getattr(product, 'images_metadata', []),
                    'productName': getattr(product, 'product_name', ''),
                    'brand': getattr(product, 'brand', ''),
                    'priceText': getattr(product, 'price', ''),  # 修正：使用price字段
                    'currentPrice': getattr(product, 'current_price', ''),
                    'description': getattr(product, 'description', ''),
                    # 从 extra 中透传 _detail_data 和其他原始数据
                    **extra
                }
            else:
                product_dict = product
            
            # 检查是否需要抓取详情
            if self.detail_fetcher.needs_detail_fetch(product_dict):
                print(f"📄 产品 {pid} 需要补充详情数据...")
                detail_data = self.detail_fetcher.fetch_product_detail(
                    product_dict.get('detailUrl', ''), 
                    pid
                )
                if detail_data:
                    enhanced_dict = self.detail_fetcher.merge_detail_into_product(product_dict, detail_data)
                    enhanced_products_list.append((pid, enhanced_dict))
                else:
                    enhanced_products_list.append((pid, product_dict))
            else:
                enhanced_products_list.append((pid, product_dict))

        # 7. 组装字段，构建 updates 列表（record_id + fields）
        updates = []
        
        # 将增强产品列表转换为字典以便快速查找
        enhanced_products = {pid: enhanced_dict for pid, enhanced_dict in enhanced_products_list}
        
        for pid in candidate_ids:
            enhanced_product = enhanced_products.get(pid)
            if not enhanced_product:
                continue
            record_info = existing_records.get(pid)
            if not record_info:
                # 此时所有记录都应该存在，如果不存在说明前面的创建过程有问题
                print(f"警告：产品 {pid} 在缺失记录创建后仍不存在，跳过处理")
                continue
                
            pre_title = title_results.get(pid, '')
            
            # 提取详情数据（如果存在）
            detail_data = enhanced_product.get('_detail_data')
            
            # 调用FieldAssembler，传递详情数据
            fields = self.field_assembler.build_update_fields(
                product=enhanced_product,
                pre_generated_title=pre_title,
                title_only=title_only,
                product_detail=detail_data
            )
            if not fields:
                continue

            # 如果字段组装成功补上了标题，从 title_failed 中移除
            if '商品标题' in fields and pid in title_failed:
                title_failed.remove(pid)

            # 调试：打印生成的字段
            print(f"\n📋 产品 {pid} 生成的字段:")
            print("=" * 60)
            for field_name, field_value in fields.items():
                if field_name in ['颜色', '尺码', '图片URL', '尺码表', '详情页文字']:
                    # 多行字段显示行数
                    if isinstance(field_value, str):
                        lines = field_value.split('\n')
                        print(f"  {field_name}: {len(lines)}行 (总长度:{len(field_value)}字符)")
                    else:
                        print(f"  {field_name}: {field_value}")
                else:
                    print(f"  {field_name}: {field_value}")
            print("=" * 60)
            print(f"共生成 {len(fields)} 个字段\n")
                
            if (not force_update) and not self._fields_are_different(record_info['fields'], fields):
                continue
                
            updates.append({'record_id': record_info['record_id'], 'fields': fields, 'product_id': pid})
        
        # 8. 调用 FeishuClient 批量更新
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

        # 9. 返回 UpdateResult
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
