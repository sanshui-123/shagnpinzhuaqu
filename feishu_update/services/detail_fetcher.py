"""
产品详情抓取服务
"""

import json
import subprocess
import tempfile
import os
import time
from typing import Dict, Optional, List
from pathlib import Path


class DetailFetcher:
    """产品详情抓取器

    负责调用Node.js脚本抓取产品详情数据，并解析返回结果。
    """

    def __init__(self, project_root: Optional[str] = None) -> None:
        """初始化抓取器

        Args:
            project_root: 项目根目录路径，默认自动查找
        """
        self.project_root = project_root or self._find_project_root()
        self.scrape_script = os.path.join(self.project_root, 'scripts', 'scrape_product_detail.js')
        self.last_fetch_time = 0
        self.fetch_interval = float(os.getenv('DETAIL_FETCH_INTERVAL', '2.0'))  # 默认2秒间隔
        
    def _find_project_root(self) -> str:
        """自动查找项目根目录"""
        current_dir = Path(__file__).parent
        while current_dir != current_dir.parent:
            if (current_dir / 'scripts' / 'scrape_product_detail.js').exists():
                return str(current_dir)
            current_dir = current_dir.parent
        
        # 如果找不到，使用相对路径
        return os.getcwd()
    
    def needs_detail_fetch(self, product: Dict) -> bool:
        """检查产品是否需要抓取详情

        检查是否缺少颜色、尺码、图片等关键信息。

        Args:
            product: 产品数据字典

        Returns:
            bool: 如果需要抓取详情则返回True
        """
        # 首先检查是否已经有详情数据
        if product.get('_detail_data') or product.get('extra', {}).get('_detail_data'):
            return False

        # 检查是否缺少关键字段
        colors = product.get('colors', [])
        sizes = product.get('sizes', [])
        images = product.get('imagesMetadata', [])

        # 如果颜色、尺码、图片任一为空，则需要抓取
        return not colors or not sizes or not images
    
    def fetch_product_detail(self, product_url: str, product_id: str = None) -> Optional[Dict]:
        """抓取单个产品的详情数据

        Args:
            product_url: 产品详情页URL
            product_id: 产品ID（可选，从URL自动提取）

        Returns:
            Dict: 抓取的详情数据，如果失败则返回None
        """
        # 限速：确保请求间隔
        current_time = time.time()
        time_since_last = current_time - self.last_fetch_time
        if time_since_last < self.fetch_interval:
            sleep_time = self.fetch_interval - time_since_last
            print(f"⏳ 限速中，等待 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)

        try:
            print(f"🔍 正在抓取产品详情: {product_id or 'unknown'}")
            self.last_fetch_time = time.time()
            
            # 创建临时输出目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 构建命令参数
                cmd = [
                    'node', self.scrape_script,
                    '--url', product_url,
                    '--output-dir', temp_dir
                ]
                
                if product_id:
                    cmd.extend(['--product-id', product_id])
                
                # 执行node脚本
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=180,  # 3分钟超时
                    cwd=self.project_root
                )
                
                if result.returncode != 0:
                    print(f"❌ 抓取失败: {result.stderr}")
                    return None
                
                # 查找生成的JSON文件
                json_files = list(Path(temp_dir).glob(f'product_details_{product_id}_*.json'))
                if not json_files:
                    json_files = list(Path(temp_dir).glob('product_details_*.json'))
                
                if not json_files:
                    print(f"❌ 未找到输出文件")
                    return None
                
                # 读取最新的JSON文件
                latest_file = sorted(json_files)[-1]
                with open(latest_file, 'r', encoding='utf-8') as f:
                    detail_data = json.load(f)
                
                print(f"✅ 抓取成功: {detail_data['scrapeInfo']['totalImages']}张图片, {detail_data['scrapeInfo']['totalColors']}种颜色, {detail_data['scrapeInfo']['totalSizes']}个尺码")
                return detail_data
                
        except subprocess.TimeoutExpired:
            print(f"❌ 抓取超时: {product_url}")
            return None
        except Exception as e:
            print(f"❌ 抓取异常: {e}")
            return None
    
    def merge_detail_into_product(self, product: Dict, detail_data: Dict) -> Dict:
        """将详情数据合并到产品数据中

        Args:
            product: 原始产品数据
            detail_data: 抓取的详情数据

        Returns:
            Dict: 合并后的产品数据
        """
        # 创建产品副本，避免修改原数据
        enhanced_product = product.copy()

        # 关键：将完整的详情数据存储到 _detail_data 字段
        enhanced_product['_detail_data'] = detail_data

        # 合并颜色信息
        if detail_data.get('colors'):
            enhanced_product['colors'] = [
                color.get('name', color.get('code', 'Unknown'))
                for color in detail_data['colors']
            ]

        # 合并尺码信息
        if detail_data.get('sizes'):
            enhanced_product['sizes'] = detail_data['sizes']

        # 合并图片信息
        if detail_data.get('images', {}).get('product'):
            # 构建图片元数据格式
            images_metadata = []
            colors = detail_data.get('colors', [])
            images_data = detail_data['images']
            
            # 优先使用variants中的颜色-图片对应关系
            if images_data.get('variants') and colors:
                # 按颜色分组处理图片
                for color in colors:
                    color_code = color.get('code', '')
                    color_name = color.get('name', '')
                    
                    # 查找该颜色对应的图片
                    color_images = images_data['variants'].get(color_code, [])
                    
                    # 如果该颜色没有专属图片，使用product中的图片
                    if not color_images and images_data.get('product'):
                        color_images = images_data['product']
                    
                    # 为该颜色的每张图片创建元数据
                    for i, image_url in enumerate(color_images):
                        images_metadata.append({
                            'name': f'{color_name}_{i+1}' if color_name else f'Image_{len(images_metadata)+1}',
                            'url': image_url,
                            'colorName': color_name,
                            'colorCode': color_code
                        })
                        
            enhanced_product['imagesMetadata'] = images_metadata
        
        # 添加详情数据引用（用于FieldAssembler）
        enhanced_product['_detail_data'] = detail_data

        # 保留尺码表文本，便于后续格式化
        if detail_data.get('sizeSectionText'):
            enhanced_product['sizeSectionText'] = detail_data.get('sizeSectionText')
        if detail_data.get('sizeSection', {}).get('text'):
            enhanced_product['sizeSectionText'] = detail_data['sizeSection']['text']
        
        return enhanced_product
    
    def fetch_and_enhance_products(self, products: List[Dict]) -> List[Dict]:
        """批量抓取并增强产品数据
        
        Args:
            products: 产品列表
            
        Returns:
            List[Dict]: 增强后的产品列表
        """
        enhanced_products = []
        
        for product in products:
            try:
                # 检查是否需要抓取详情
                if not self.needs_detail_fetch(product):
                    print(f"⏭️ 产品 {product.get('productId', 'unknown')} 无需抓取详情")
                    enhanced_products.append(product)
                    continue
                
                # 获取产品URL和ID
                product_url = product.get('detailUrl') or product.get('detail_url')
                product_id = product.get('productId') or product.get('product_id')
                
                if not product_url:
                    print(f"⚠️ 产品 {product_id} 缺少详情URL，跳过抓取")
                    enhanced_products.append(product)
                    continue
                
                # 抓取详情数据
                detail_data = self.fetch_product_detail(product_url, product_id)
                
                if detail_data:
                    # 合并数据
                    enhanced_product = self.merge_detail_into_product(product, detail_data)
                    enhanced_products.append(enhanced_product)
                else:
                    # 抓取失败，使用原数据
                    print(f"⚠️ 产品 {product_id} 详情抓取失败，使用原数据")
                    enhanced_products.append(product)
                    
            except Exception as e:
                print(f"❌ 处理产品 {product.get('productId', 'unknown')} 时出错: {e}")
                enhanced_products.append(product)
        
        return enhanced_products
