"""
流式更新编排器 - 修复批量处理缺陷

解决问题：
1. 改为流式处理：一个产品处理完立即同步
2. 添加进度保存：记录已处理的产品ID
3. 支持断点续传：跳过已处理的产品
4. 增加超时控制：单个产品超时不影响整体
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from ..models.product import Product
from ..models.update_result import UpdateResult
from ..models.progress import ProgressEvent
from ..services.field_assembler import FieldAssembler
from ..services.title_generator import TitleGenerator
from ..services.translator import Translator
from ..services.detail_fetcher import DetailFetcher
from ..clients.interfaces import GLMClientInterface, FeishuClientInterface
from ..loaders.factory import LoaderFactory


class StreamingUpdateOrchestrator:
    """流式更新编排器
    
    特性：
    - 逐个产品流式处理，立即同步到飞书
    - 进度自动保存，支持断点续传
    - 单个产品失败不影响其他产品
    - 实时进度反馈
    """

    def __init__(
        self,
        glm_client: GLMClientInterface,
        feishu_client: FeishuClientInterface,
        title_generator: Optional[TitleGenerator] = None,
        translator: Optional[Translator] = None,
        field_assembler: Optional[FieldAssembler] = None,
        progress_callback: Optional[callable] = None,
        progress_save_interval: int = 5,  # 每处理5个产品保存一次进度
        single_timeout: int = 60,  # 单个产品处理超时时间（秒）
    ) -> None:
        self.glm_client = glm_client
        self.feishu_client = feishu_client
        self.title_generator = title_generator or TitleGenerator(glm_client)
        self.translator = translator or Translator(glm_client)
        self.field_assembler = field_assembler or FieldAssembler(
            title_generator=self.title_generator,
            translator=self.translator,
        )
        self.detail_fetcher = DetailFetcher()
        self.progress_callback = progress_callback
        self.progress_save_interval = progress_save_interval
        self.single_timeout = single_timeout

    def execute(
        self,
        input_path: str,
        *,
        force_update: bool = False,
        title_only: bool = False,
        category_only: bool = False,
        dry_run: bool = False,
        resume: bool = True,  # 是否启用断点续传
    ) -> UpdateResult:
        """执行流式更新流程"""
        
        # 创建进度文件路径
        progress_file = self._get_progress_file_path(input_path)
        
        # 1. 读取并解析产品数据
        data = json.load(open(input_path, 'r', encoding='utf-8'))
        loader = LoaderFactory.create(data)
        product_list = loader.parse(data)
        products = {p.product_id: p for p in product_list if p.product_id}

        # progress callback 通知加载完成
        if self.progress_callback:
            event = ProgressEvent.progress_update_event(
                processed_count=0,
                total_count=len(products),
                success_count=0,
                failed_count=0
            )
            event.message = f"已加载 {len(products)} 个产品，准备流式处理"
            self.progress_callback(event)

        # 2. 获取飞书现有记录
        print("🔍 获取飞书现有记录...")
        existing_records = self.feishu_client.get_records()
        existing_records_by_url = self.feishu_client.get_records_by_url()

        # 3. 确保记录存在
        # 3.1 先尝试通过URL或 legacy ID 匹配
        missing_ids = []
        for pid in products.keys():
            if pid not in existing_records:
                product = products[pid]

                extra_data = getattr(product, 'extra', {}) or {}
                legacy_id = (
                    getattr(product, 'legacy_product_id', '') or
                    getattr(product, 'legacyProductId', '') or
                    (extra_data.get('legacyProductId') if isinstance(extra_data, dict) else '')
                )
                legacy_id = str(legacy_id).strip()
                if legacy_id and legacy_id in existing_records:
                    existing_records[pid] = existing_records[legacy_id]
                    print(f"🔁 使用 legacyProductId 匹配到现有记录: {pid} <- {legacy_id}")
                    continue

                detail_url = (getattr(product, 'detail_url', None) or
                             getattr(product, 'detailUrl', None) or '').strip().rstrip('/')
                if detail_url and detail_url in existing_records_by_url:
                    existing_records[pid] = existing_records_by_url[detail_url]
                    print(f"🔁 使用商品链接匹配到现有记录: {pid} -> {detail_url}")
                else:
                    missing_ids.append(pid)
        if missing_ids:
            print(f"发现 {len(missing_ids)} 个缺失的product_id，正在批量创建...")
            self._create_missing_records(missing_ids, products, dry_run)
            # 重新获取飞书记录
            existing_records = self.feishu_client.get_records()

        # 4. 计算需要处理的产品
        fields_to_check = self._get_fields_to_check(title_only, category_only)
        candidate_ids, skipped_ids = self._calculate_candidates(
            products, existing_records, fields_to_check, force_update
        )

        if not candidate_ids:
            print("✅ 没有需要更新的产品")
            return UpdateResult(
                success_count=0,
                failed_batches=[],
                candidates_count=0,
                skipped_count=len(skipped_ids),
                title_failed=[],
                total_batches=0,
                log_path=None
            )

        # 5. 加载进度（如果启用断点续传）
        processed_ids = set()
        if resume:
            processed_ids = self._load_progress(progress_file)
            remaining_candidates = [pid for pid in candidate_ids if pid not in processed_ids]
            if processed_ids:
                print(f"📝 断点续传：已处理 {len(processed_ids)} 个产品，剩余 {len(remaining_candidates)} 个")
                candidate_ids = remaining_candidates

        print(f"🚀 开始流式处理 {len(candidate_ids)} 个产品...")

        # 6. 流式处理每个产品
        return self._process_products_streaming(
            candidate_ids,
            products,
            existing_records,
            title_only,
            category_only,
            force_update,
            dry_run,
            progress_file,
            processed_ids,
            len(skipped_ids)
        )

    def _process_products_streaming(
        self,
        candidate_ids: List[str],
        products: Dict[str, Product],
        existing_records: Dict[str, Dict],
        title_only: bool,
        category_only: bool,
        force_update: bool,
        dry_run: bool,
        progress_file: Path,
        initial_processed: Set[str],
        skipped_count: int
    ) -> UpdateResult:
        """流式处理产品列表"""
        
        success_count = 0
        failed_products = []
        processed_count = len(initial_processed)
        total_count = len(candidate_ids) + processed_count

        for i, product_id in enumerate(candidate_ids, 1):
            try:
                print(f"\n📦 处理产品 {i}/{len(candidate_ids)}: {product_id}")
                
                # 单个产品处理超时控制
                start_time = time.time()
                
                success = self._process_single_product(
                    product_id,
                    products[product_id],
                    existing_records[product_id],
                    title_only,
                    category_only,
                    force_update,
                    dry_run
                )
                
                elapsed = time.time() - start_time
                
                if success:
                    success_count += 1
                    print(f"  ✅ 成功 (耗时: {elapsed:.1f}s)")
                else:
                    failed_products.append(product_id)
                    print(f"  ❌ 失败 (耗时: {elapsed:.1f}s)")
                
                processed_count += 1
                
                # 更新进度回调
                if self.progress_callback:
                    event = ProgressEvent.progress_update_event(
                        processed_count=processed_count,
                        total_count=total_count,
                        success_count=success_count,
                        failed_count=len(failed_products)
                    )
                    event.message = f"流式处理进度: {processed_count}/{total_count}"
                    self.progress_callback(event)
                
                # 定期保存进度
                if i % self.progress_save_interval == 0:
                    processed_ids = initial_processed.union(set(candidate_ids[:i]))
                    self._save_progress(progress_file, processed_ids)
                    print(f"  💾 进度已保存 ({len(processed_ids)} 个产品)")

            except Exception as e:
                print(f"  💥 处理产品 {product_id} 时发生异常: {e}")
                failed_products.append(product_id)
                processed_count += 1

        # 最终保存进度
        final_processed = initial_processed.union(set(candidate_ids))
        self._save_progress(progress_file, final_processed)
        
        print(f"\n🎉 流式处理完成！成功: {success_count}, 失败: {len(failed_products)}")

        return UpdateResult(
            success_count=success_count,
            failed_batches=[{'products': failed_products}] if failed_products else [],
            candidates_count=len(candidate_ids),
            skipped_count=skipped_count,
            title_failed=failed_products,
            total_batches=1,
            log_path=str(progress_file)
        )

    def _process_single_product(
        self,
        product_id: str,
        product: Product,
        record_info: Dict,
        title_only: bool,
        category_only: bool,
        force_update: bool,
        dry_run: bool
    ) -> bool:
        """处理单个产品：生成标题 → 抓取详情（如需要） → 组装字段 → 立即同步"""

        try:
            # 1. 生成标题（带超时控制）
            print(f"  🏷️ 生成标题...")
            title = self._generate_title_with_timeout(product)

            # 2. 转换Product对象为字典格式，透传 extra 数据
            if hasattr(product, '__dict__'):
                # 获取 extra 字段中的数据
                extra = getattr(product, 'extra', {})

                product_dict = {
                    'productId': product.product_id,
                    'detailUrl': product.detail_url,
                    'colors': getattr(product, 'colors', []),
                    'sizes': getattr(product, 'sizes', []),
                    'imageUrls': getattr(product, 'imageUrls', []),  # 新增：图片URL列表
                    'sizeChart': getattr(product, 'sizeChart', {}),  # 新增：尺码表
                    'imagesMetadata': getattr(product, 'images_metadata', []),
                    'productName': getattr(product, 'product_name', ''),
                    'brand': getattr(product, 'brand', ''),
                    'priceText': getattr(product, 'price', ''),
                    'currentPrice': getattr(product, 'current_price', ''),
                    'description': getattr(product, 'description', ''),
                    'gender': getattr(product, 'gender', ''),  # 🔥 添加性别字段
                    'category': getattr(product, 'category', ''),  # 🔥 添加分类字段
                    # 从 extra 中透传 _detail_data 和其他原始数据
                    **extra
                }
            else:
                product_dict = product

            # 3. 检查是否需要抓取详情
            if self.detail_fetcher.needs_detail_fetch(product_dict):
                print(f"  📄 产品 {product_id} 需要补充详情数据...")
                detail_data = self.detail_fetcher.fetch_product_detail(
                    product_dict.get('detailUrl', ''),
                    product_id
                )
                if detail_data:
                    # 合并详情数据到产品字典
                    enhanced_dict = self.detail_fetcher.merge_detail_into_product(product_dict, detail_data)
                    product_dict = enhanced_dict
                    print(f"  ✅ 详情抓取成功")
                else:
                    print(f"  ⚠️ 详情抓取失败，使用基础数据")

            # 4. 提取详情数据
            detail_data = product_dict.get('_detail_data')

            # 5. 组装字段
            fields = self.field_assembler.build_update_fields(
                product=product_dict,
                pre_generated_title=title,
                title_only=title_only,
                category_only=category_only,
                product_detail=detail_data
            )

            if not fields:
                print(f"  ⚠️ 没有字段需要更新")
                return True

            # 调试：打印生成的字段
            print(f"\n📋 产品 {product_id} 生成的字段:")
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
                
            # 3. 检查是否需要更新
            if not force_update and not self._fields_are_different(record_info['fields'], fields):
                print(f"  ⏭️ 字段无变化，跳过更新")
                return True
            
            # 4. 立即同步到飞书
            if dry_run:
                print(f"  🔍 模拟模式：跳过飞书更新")
                return True
                
            print(f"  ⬆️ 同步到飞书...")
            update_record = {
                'record_id': record_info['record_id'],
                'fields': fields
            }
            
            # 单个记录更新
            result = self.feishu_client.batch_update([update_record], batch_size=1)
            return result.get('success_count', 0) > 0
            
        except Exception as e:
            print(f"  💥 处理失败: {e}")
            return False

    def _generate_title_with_timeout(self, product: Product) -> str:
        """带超时控制的标题生成"""
        try:
            # 这里可以添加更精细的超时控制
            title = self.title_generator.generate(product)
            return title or ""
        except Exception as e:
            print(f"    ⚠️ 标题生成失败: {e}")
            return ""

    def _get_progress_file_path(self, input_path: str) -> Path:
        """获取进度文件路径"""
        input_file = Path(input_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        progress_file = input_file.parent / f"streaming_progress_{input_file.stem}_{timestamp}.json"
        return progress_file

    def _save_progress(self, progress_file: Path, processed_ids: Set[str]) -> None:
        """保存处理进度"""
        try:
            progress_data = {
                'timestamp': datetime.now().isoformat(),
                'processed_count': len(processed_ids),
                'processed_ids': list(processed_ids)
            }
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存进度失败: {e}")

    def _load_progress(self, progress_file: Path) -> Set[str]:
        """加载处理进度"""
        try:
            if not progress_file.exists():
                return set()
                
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                processed_ids = set(progress_data.get('processed_ids', []))
                return processed_ids
        except Exception as e:
            print(f"⚠️ 加载进度失败: {e}")
            return set()

    def _create_missing_records(self, missing_ids: List[str], products: Dict[str, Product], dry_run: bool):
        """创建缺失的记录（带ID去重保护）"""
        # 获取已存在的商品ID集合
        existing_ids = self.feishu_client.get_existing_ids()

        create_records = []
        skipped_ids = []

        for pid in missing_ids:
            # 检查ID是否已存在（防止重复创建）
            if pid in existing_ids:
                print(f"⏭️ 跳过已存在的商品ID: {pid}（URL不匹配但ID已存在）")
                skipped_ids.append(pid)
                continue

            product = products[pid]
            create_records.append({
                'fields': {
                    '商品ID': pid,
                    '商品链接': product.detail_url or '',
                    '品牌名': product.brand or '',
                },
                'product_id': pid
            })

        if skipped_ids:
            print(f"⚠️ 跳过 {len(skipped_ids)} 个已存在的商品ID")

        if not create_records:
            print("✅ 没有需要创建的新记录")
            return

        if not dry_run:
            create_result = self.feishu_client.batch_create(create_records, batch_size=30)
            if create_result.get('success_count', 0) > 0:
                print(f"✅ 成功创建 {create_result['success_count']} 条新记录")
                # 将新创建的ID添加到existing_ids集合
                for record in create_records:
                    existing_ids.add(record['product_id'])
            else:
                if not skipped_ids:  # 只有在没有跳过任何记录时才报错
                    raise RuntimeError("缺失记录创建失败，无法继续处理")
        else:
            print(f"模拟模式：跳过创建 {len(create_records)} 条缺失记录")

    def _get_fields_to_check(self, title_only: bool, category_only: bool) -> List[str]:
        """获取需要检查的字段列表"""
        fields_to_check = ['商品ID','商品标题','价格','性别','衣服分类','品牌名',
                          '颜色','尺码','图片URL','图片数量','详情页文字','商品链接','尺码表']
        if title_only:
            fields_to_check = ['商品标题']
        elif category_only:
            fields_to_check = ['衣服分类']
        return fields_to_check

    def _calculate_candidates(
        self,
        products: Dict[str, Product],
        existing_records: Dict[str, Dict],
        fields_to_check: List[str],
        force_update: bool
    ):
        """计算需要处理的候选产品"""
        candidate_ids = []
        skipped_ids = []
        
        for product_id, product in products.items():
            if product_id in existing_records:
                existing_fields = existing_records[product_id]['fields']
                
                if force_update:
                    candidate_ids.append(product_id)
                else:
                    empty_fields = self._has_empty_fields_to_fill(existing_fields, fields_to_check)
                    if empty_fields:
                        candidate_ids.append(product_id)
                    else:
                        skipped_ids.append(product_id)
            else:
                print(f"警告：产品 {product_id} 在缺失记录创建后仍不存在于 existing_records 中")
                candidate_ids.append(product_id)
                
        return candidate_ids, skipped_ids

    def _fields_are_different(self, existing_fields: Dict, new_fields: Dict) -> bool:
        """检查字段是否有变化"""
        for key, new_value in new_fields.items():
            existing_value = existing_fields.get(key, '')
            if self._normalize_field_value(new_value) != self._normalize_field_value(existing_value):
                return True
        return False

    def _has_empty_fields_to_fill(self, existing_fields: Dict, target_fields: List[str]) -> List[str]:
        """检查指定字段中哪些为空需要补齐"""
        empty_fields = []
        for field in target_fields:
            existing_value = self._normalize_field_value(existing_fields.get(field, ''))
            if not existing_value:
                empty_fields.append(field)
        return empty_fields

    def _normalize_field_value(self, value: any) -> str:
        """将飞书字段值统一转成可比对的字符串，兼容单选/多选结构"""
        if isinstance(value, dict):
            # 单选/多选可能返回 {text, option_id}
            if 'text' in value:
                return str(value.get('text') or '').strip()
            return str(value).strip()
        if isinstance(value, list):
            # 多选/单选数组：提取文本后用换行拼接保持顺序
            normalized_items = []
            for item in value:
                if isinstance(item, dict) and 'text' in item:
                    normalized_items.append(str(item.get('text') or '').strip())
                else:
                    normalized_items.append(str(item).strip())
            return '\n'.join(filter(None, normalized_items))
        return str(value or '').strip()
