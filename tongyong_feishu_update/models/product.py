"""产品数据模型 - 终稿版本

定义产品相关的数据结构，包括：
- Variant: 产品变体（颜色/尺码组合）
- Images: 图片集合  
- Product: 完整产品信息，覆盖脚本实际访问的所有字段
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json


@dataclass
class Variant:
    """产品变体（颜色和尺码的组合）- 兼容版本"""
    # 新格式字段
    variant_id: str = ""               # 变体ID
    color_name: str = ""               # 颜色名称
    size_name: str = ""                # 尺码名称
    price: str = ""                    # 价格
    is_available: bool = True          # 是否可用
    stock: Dict[str, Any] = field(default_factory=dict)  # 库存状态分析原始信息

    # 兼容旧格式字段（用于向后兼容）
    colorId: str = ""                  # 颜色ID（兼容字段）
    colorName: str = ""                # 颜色名称（兼容字段）
    isFirstColor: bool = False         # 是否首色（兼容字段）
    sizes: List[str] = field(default_factory=list)  # 尺码列表（兼容字段）

    def __post_init__(self):
        """后处理，同步兼容字段"""
        # 如果使用的是新字段，同步到兼容字段
        if self.variant_id and not self.colorId:
            self.colorId = self.variant_id
        elif self.colorId and not self.variant_id:
            self.variant_id = self.colorId

        if self.color_name and not self.colorName:
            self.colorName = self.color_name
        elif self.colorName and not self.color_name:
            self.color_name = self.colorName


    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（包含兼容字段）"""
        return {
            # 新格式字段
            'variant_id': self.variant_id,
            'color_name': self.color_name,
            'size_name': self.size_name,
            'price': self.price,
            'is_available': self.is_available,
            'stock': self.stock,
            # 兼容字段
            'colorId': self.colorId,
            'colorName': self.colorName,
            'isFirstColor': self.isFirstColor,
            'sizes': self.sizes
        }


@dataclass
class Images:
    """图片集合 - 兼容版本"""
    # 新格式字段
    main_image: str = ""               # 主图片
    gallery_images: List[str] = field(default_factory=list)  # 图集图片
    product: List[str] = field(default_factory=list)           # 产品图片
    variants: List[str] = field(default_factory=list)          # 变体图片
    by_color: Dict[str, List[str]] = field(default_factory=dict)  # 按颜色分类的图片
    all: List[str] = field(default_factory=list)               # 所有图片
    metadata: List[Dict[str, Any]] = field(default_factory=list)  # 图片元数据
    oss_product_images: List[str] = field(default_factory=list)   # OSS产品图片
    oss_variant_images: Dict[str, List[str]] = field(default_factory=dict)  # OSS变体图片

    # 兼容旧格式字段
    totalCount: int = 0                # 总图片数（兼容字段）
    mainImages: List[str] = field(default_factory=list)  # 主图片列表（兼容字段）
    imagesByColor: Dict[str, List[str]] = field(default_factory=dict)  # 按颜色分类的图片（兼容字段）

    def __post_init__(self):
        """后处理，同步兼容字段"""
        # 同步图片数量
        if len(self.all) > 0 and self.totalCount == 0:
            self.totalCount = len(self.all)

        # 同步主图片
        if len(self.mainImages) == 0 and self.main_image:
            self.mainImages = [self.main_image]
        elif len(self.mainImages) > 0 and not self.main_image:
            self.main_image = self.mainImages[0] if self.mainImages else ""

        # 同步按颜色分类的图片
        if len(self.imagesByColor) == 0 and len(self.by_color) > 0:
            self.imagesByColor = self.by_color.copy()
        elif len(self.imagesByColor) > 0 and len(self.by_color) == 0:
            self.by_color = self.imagesByColor.copy()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（包含兼容字段）"""
        return {
            # 新格式字段
            'main_image': self.main_image,
            'gallery_images': self.gallery_images,
            'product': self.product,
            'variants': self.variants,
            'by_color': self.by_color,
            'all': self.all,
            'metadata': self.metadata,
            'oss_product_images': self.oss_product_images,
            'oss_variant_images': self.oss_variant_images,
            # 兼容字段
            'totalCount': self.totalCount,
            'mainImages': self.mainImages,
            'imagesByColor': self.imagesByColor
        }


@dataclass
class Product:
    """完整产品信息 - 终稿版本，覆盖脚本实际访问的所有字段"""
    # 基本信息
    product_id: str = ""               # 产品ID
    legacy_product_id: str = ""        # 旧的产品ID（用于兼容早期导入）
    brand_product_id: str = ""         # 品牌方商品编号
    legacyProductId: str = ""          # 兼容字段 - legacy_product_id
    brandProductId: str = ""           # 兼容字段 - brand_product_id
    product_name: str = ""             # 产品名称
    description: str = ""              # 产品描述
    brand: str = ""                    # 品牌
    category: str = ""                 # 分类
    
    # 价格信息
    price: str = ""                    # 基础价格
    original_price: str = ""           # 原价
    currency: str = "JPY"              # 货币
    current_price: str = ""            # 当前价格
    
    # 产品属性
    sku: str = ""                      # SKU
    status: str = ""                   # 状态
    gender: str = ""                   # 性别
    
    # URL信息
    detail_url: str = ""               # 详情页URL
    
    # 变体和选项
    variants: List[Variant] = field(default_factory=list)  # 产品变体列表
    colors: List[str] = field(default_factory=list)        # 颜色列表
    sizes: List[str] = field(default_factory=list)         # 尺码列表
    size_chart: Dict[str, Any] = field(default_factory=dict)  # 尺码表
    
    # 图片信息
    images: Images = field(default_factory=Images)         # 图片集合
    main_image: str = ""               # 主图片URL
    
    # 库存状态
    stock_status: str = ""             # 库存状态
    
    # 抓取元数据
    scraped_at: str = ""               # 抓取时间
    processing_time: int = 0           # 处理时间（毫秒）
    version: str = ""                  # 版本信息
    total_images: int = 0              # 图片总数
    
    # 额外数据
    extra: Dict[str, Any] = field(default_factory=dict)    # 额外数据

    # 兼容旧格式字段（用于向后兼容）
    productId: str = ""                # 产品ID（兼容字段）
    productName: str = ""              # 产品名称（兼容字段）
    detailUrl: str = ""                 # 详情页URL（兼容字段）
    imageUrls: List[str] = field(default_factory=list)  # 图片URL列表（兼容字段）
    scrapeInfo: Dict[str, Any] = field(default_factory=dict)  # 抓取信息（兼容字段）
    # 🔥 gender字段已在第139行定义，移除此重复定义

    def __post_init__(self):
        """后处理，同步兼容字段"""
        # 如果使用的是新字段，同步到兼容字段
        if self.product_id and not self.productId:
            self.productId = self.product_id
        elif self.productId and not self.product_id:
            self.product_id = self.productId

        if self.product_name and not self.productName:
            self.productName = self.product_name
        elif self.productName and not self.product_name:
            self.product_name = self.productName

        if self.detail_url and not self.detailUrl:
            self.detailUrl = self.detail_url
        elif self.detailUrl and not self.detail_url:
            self.detail_url = self.detailUrl

        # legacy/product id 同步
        if self.legacy_product_id and not self.legacyProductId:
            self.legacyProductId = self.legacy_product_id
        elif self.legacyProductId and not self.legacy_product_id:
            self.legacy_product_id = self.legacyProductId

        if self.brand_product_id and not self.brandProductId:
            self.brandProductId = self.brand_product_id
        elif self.brandProductId and not self.brand_product_id:
            self.brand_product_id = self.brandProductId

        # 同步性别字段
        if hasattr(self, 'gender') and not hasattr(self, '_synced_gender'):
            # 新字段同步到兼容字段
            pass  # gender字段已经存在
        elif hasattr(self, '_synced_gender'):
            # 兼容字段同步到新字段
            self.gender = self._synced_gender

        # 同步图片信息
        if self.imageUrls and not self.images.all:
            self.images.all = self.imageUrls
        elif self.images.all and not self.imageUrls:
            self.imageUrls = self.images.all

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问（向后兼容）- 映射旧key到新属性"""
        # 字段映射，将旧的键名映射到新的属性名
        field_mapping = {
            # 基本信息映射
            'productId': 'product_id',
            'productName': 'product_name',
            'gender': 'gender',  # 添加gender字段映射
            'detailUrl': 'detail_url',
            'currentPrice': 'current_price',
            'originalPrice': 'original_price',
            'mainImage': 'main_image',
            
            # 图片相关映射
            'productImages': 'images.product',
            'variantImages': 'images.variants',
            'imagesByColor': 'images.by_color',
            'imagesAll': 'images.all',
            'imagesMetadata': 'images.metadata',
            'ossProductImages': 'images.oss_product_images',
            'ossVariantImages': 'images.oss_variant_images',
            
            # 变体相关映射
            'variantCount': 'variants',  # 特殊处理，返回长度
            
            # 时间相关映射
            'scrapedAt': 'scraped_at',
            'processingTime': 'processing_time',
            'totalImages': 'total_images',
            
            # 额外数据映射
            'extraData': 'extra',
        }
        
        # 特殊处理variantCount
        if key == 'variantCount':
            return len(self.variants)
        
        # 使用映射后的键名
        mapped_key = field_mapping.get(key, key)
        
        # 处理嵌套属性（如 images.product）
        if '.' in mapped_key:
            obj = self
            for part in mapped_key.split('.'):
                obj = getattr(obj, part, None)
                if obj is None:
                    break
            return obj
        
        # 直接获取属性
        return getattr(self, mapped_key, None)
    
    def get(self, key: str, default: Any = None) -> Any:
        """安全的字典式访问（向后兼容）"""
        try:
            value = self[key]
            return value if value is not None else default
        except (AttributeError, KeyError):
            return default
    
    def has_variants(self) -> bool:
        """检查是否有变体信息"""
        return len(self.variants) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'description': self.description,
            'brand': self.brand,
            'category': self.category,
            'price': self.price,
            'original_price': self.original_price,
            'currency': self.currency,
            'current_price': self.current_price,
            'sku': self.sku,
            'status': self.status,
            'gender': self.gender,  # 添加gender字段
            'detail_url': self.detail_url,
            'variants': [v.to_dict() for v in self.variants],
            'colors': self.colors,
            'sizes': self.sizes,
            'size_chart': self.size_chart,
            'images': self.images.to_dict(),
            'main_image': self.main_image,
            'stock_status': self.stock_status,
            'scraped_at': self.scraped_at,
            'processing_time': self.processing_time,
            'version': self.version,
            'total_images': self.total_images,
            'extra': self.extra
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """从字典创建Product实例"""
        # 处理images字段
        images_data = data.get('images', {})
        if isinstance(images_data, dict):
            images = Images(
                product=images_data.get('product', []),
                variants=images_data.get('variants', []),
                by_color=images_data.get('by_color', {}),
                all=images_data.get('all', []),
                metadata=images_data.get('metadata', []),
                oss_product_images=images_data.get('oss_product_images', []),
                oss_variant_images=images_data.get('oss_variant_images', {})
            )
        else:
            images = Images()
        
        # 处理variants字段
        variants_data = data.get('variants', [])
        variants = []
        if isinstance(variants_data, list):
            for variant_data in variants_data:
                if isinstance(variant_data, dict):
                    variant = Variant(
                        variant_id=variant_data.get('variant_id', ''),
                        color_name=variant_data.get('color_name', variant_data.get('colorName', '')),
                        size_name=variant_data.get('size_name', variant_data.get('sizeName', '')),
                        price=variant_data.get('price', ''),
                        is_available=variant_data.get('is_available', True),
                        stock=variant_data.get('stock', {})
                    )
                    variants.append(variant)
        
        return cls(
            product_id=data.get('product_id', ''),
            product_name=data.get('product_name', ''),
            description=data.get('description', ''),
            brand=data.get('brand', ''),
            category=data.get('category', ''),
            price=data.get('price', ''),
            original_price=data.get('original_price', ''),
            currency=data.get('currency', 'JPY'),
            current_price=data.get('current_price', ''),
            sku=data.get('sku', ''),
            status=data.get('status', ''),
            detail_url=data.get('detail_url', ''),
            variants=variants,
            colors=data.get('colors', []),
            sizes=data.get('sizes', []),
            size_chart=data.get('size_chart', {}),
            images=images,
            main_image=data.get('main_image', ''),
            stock_status=data.get('stock_status', ''),
            scraped_at=data.get('scraped_at', ''),
            processing_time=data.get('processing_time', 0),
            version=data.get('version', ''),
            total_images=data.get('total_images', 0),
            extra=data.get('extra', {})
        )
