"""图片处理服务

提供产品图片相关的处理功能
"""

def build_image_url_multiline(product_data):
    """构建多行图片URL字符串
    
    Args:
        product_data: 产品数据
        
    Returns:
        str: 多行图片URL字符串
    """
    urls = []
    
    def _append_unique(target_list, value):
        if value and value not in target_list:
            target_list.append(value)

    if isinstance(product_data, dict):
        # 处理字典格式
        main_image = product_data.get('mainImage') or product_data.get('main_image')
        _append_unique(urls, main_image)

        if 'images' in product_data:
            images = product_data['images']
            if isinstance(images, dict):
                _append_unique(urls, images.get('mainImage') or images.get('main_image'))
                gallery = images.get('galleryImages') or images.get('gallery_images') or []
                for img in gallery:
                    _append_unique(urls, img)
                for img in images.get('product', []):
                    _append_unique(urls, img)
                for img in images.get('all', []):
                    _append_unique(urls, img)
    elif hasattr(product_data, 'images'):
        # 处理dataclass格式
        images = product_data.images
        # Product 本身的主图
        _append_unique(urls, getattr(product_data, 'main_image', ''))

        _append_unique(urls, getattr(images, 'main_image', ''))
        for img in getattr(images, 'gallery_images', []):
            _append_unique(urls, img)
        for img in getattr(images, 'product', []):
            _append_unique(urls, img)
        for img in getattr(images, 'all', []):
            _append_unique(urls, img)
        for img in getattr(images, 'oss_product_images', []):
            _append_unique(urls, img)

    return '\n'.join(urls) if urls else ''

def count_total_images(product_data):
    """统计总图片数量
    
    Args:
        product_data: 产品数据
        
    Returns:
        int: 图片总数
    """
    count = 0
    
    if isinstance(product_data, dict):
        # 处理字典格式
        if 'images' in product_data:
            images = product_data['images']
            if isinstance(images, dict):
                if images.get('mainImage'):
                    count += 1
                gallery = images.get('galleryImages') or []
                count += len(gallery)
                count += len(images.get('product', []))
                count += len(images.get('all', []))
    elif hasattr(product_data, 'images'):
        # 处理dataclass格式
        images = product_data.images
        seen = set()

        def _record(value):
            nonlocal count
            if value and value not in seen:
                seen.add(value)
                count += 1

        _record(getattr(product_data, 'main_image', ''))
        _record(getattr(images, 'main_image', ''))

        for img in getattr(images, 'gallery_images', []):
            _record(img)
        for img in getattr(images, 'product', []):
            _record(img)
        for img in getattr(images, 'all', []):
            _record(img)
        for img in getattr(images, 'oss_product_images', []):
            _record(img)
        for img_list in getattr(images, 'oss_variant_images', {}).values():
            for img in img_list:
                _record(img)

    return count
