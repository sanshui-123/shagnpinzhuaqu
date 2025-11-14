"""
并行标题执行器
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable, Tuple

from ..services.title_generator import TitleGenerator
from ..models import Product
from ..models.progress import ProgressEvent


class ParallelTitleExecutor:
    """使用线程池并行生成标题"""

    def __init__(
        self,
        generator: Optional[TitleGenerator] = None,
        workers: int = 6,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None
    ) -> None:
        self.generator = generator or TitleGenerator()
        self.workers = workers
        self.progress_callback = progress_callback

    def execute(self, products: List[Product]) -> Tuple[Dict[str, str], List[str]]:
        results: Dict[str, str] = {}
        failed: List[str] = []
        total = len(products)
        completed = 0

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_map = {
                executor.submit(self._generate_title, product): product.product_id
                for product in products
            }

            for future in as_completed(future_map):
                product_id = future_map[future]
                completed += 1

                try:
                    title = future.result()
                    results[product_id] = title
                    if not title.strip():
                        failed.append(product_id)
                except Exception:
                    results[product_id] = ""
                    failed.append(product_id)

                if self.progress_callback:
                    event = ProgressEvent.progress_update_event(
                        processed_count=completed,
                        total_count=total,
                        success_count=completed - len(failed),
                        failed_count=len(failed)
                    )
                    event.message = f"标题生成进度: {completed}/{total}"
                    self.progress_callback(event)

        return results, failed

    def _generate_title(self, product: Product) -> str:
        return self.generator.generate(product)
