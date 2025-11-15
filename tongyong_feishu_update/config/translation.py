"""翻译配置

本模块包含多语言翻译相关的配置常量和映射关系。
主要包括：
- 中英文翻译映射
- 产品名称翻译
- 分类名称翻译
- 特殊术语翻译
- 颜色名称翻译映射
"""

# ============================================================================
# 英文颜色名称到中文的翻译表
# ============================================================================

COLOR_NAME_TRANSLATION = {
    # 基础色
    'BLACK': '黑色',
    'WHITE': '白色',
    'BLUE': '蓝色',
    'RED': '红色',
    'NAVY': '藏蓝色',
    'GRAY': '灰色',
    'GREY': '灰色',
    'GREEN': '绿色',
    'YELLOW': '黄色',
    'ORANGE': '橙色',
    'PINK': '粉色',
    'PURPLE': '紫色',
    'BROWN': '棕色',
    'BEIGE': '米色',
    'KHAKI': '卡其色',
    'OLIVE': '橄榄绿',
    'SILVER': '银色',
    'GOLD': '金色',
    
    # 深浅变化
    'LIGHT BLUE': '浅蓝色',
    'DARK BLUE': '深蓝色',
    'LIGHT GRAY': '浅灰色',
    'DARK GRAY': '深灰色',
    'LIGHT GREY': '浅灰色',
    'DARK GREY': '深灰色',
    'LIGHT GREEN': '浅绿色',
    'DARK GREEN': '深绿色',
    'LIGHT PINK': '浅粉色',
    'DARK PINK': '深粉色',
    'LIGHT BROWN': '浅棕色',
    'DARK BROWN': '深棕色',
    
    # 复合颜色
    'BLACK/WHITE': '黑白',
    'WHITE/BLACK': '白黑',
    'NAVY/WHITE': '藏蓝色/白',
    'WHITE/NAVY': '白/藏蓝色',
    'RED/WHITE': '红白',
    'WHITE/RED': '白红',
    'BLUE/WHITE': '蓝白',
    'WHITE/BLUE': '白蓝',
    'GRAY/WHITE': '灰白',
    'WHITE/GRAY': '白灰',
    
    # 高尔夫常见颜色
    'CAMO': '迷彩',
    'CAMOUFLAGE': '迷彩',
    'NEON': '荧光',
    'METALLIC': '金属色',
    'TURQUOISE': '土耳其蓝',
    'LIME': '青柠色',
    'MAGENTA': '洋红色',
    'CYAN': '青色',
    'MAROON': '栗色',
    'TEAL': '深青色',
    'IVORY': '象牙色',
    'CREAM': '奶油色',
    
    # 小写版本
    'black': '黑色',
    'white': '白色',
    'blue': '蓝色',
    'red': '红色',
    'navy': '藏蓝色',
    'gray': '灰色',
    'grey': '灰色',
    'green': '绿色',
    'yellow': '黄色',
    'orange': '橙色',
    'pink': '粉色',
    'purple': '紫色',
    'brown': '棕色',
    'beige': '米色',
    'khaki': '卡其色',
    'olive': '橄榄绿',
    'silver': '银色',
    'gold': '金色',
    
    # 首字母大写版本
    'Black': '黑色',
    'White': '白色',
    'Blue': '蓝色',
    'Red': '红色',
    'Navy': '藏蓝色',
    'Gray': '灰色',
    'Grey': '灰色',
    'Green': '绿色',
    'Yellow': '黄色',
    'Orange': '橙色',
    'Pink': '粉色',
    'Purple': '紫色',
    'Brown': '棕色',
    'Beige': '米色',
    'Khaki': '卡其色',
    'Olive': '橄榄绿',
    'Silver': '银色',
    'Gold': '金色',
    'Camo': '迷彩',
    'Neon': '荧光',
    'Metallic': '金属色',
    
    # 日文颜色映射
    'ブラック': '黑色',
    'ホワイト': '白色',
    'ネイビー': '藏蓝色',
    'グレー': '灰色',
    'グレイ': '灰色',
    'ブルー': '蓝色',
    'レッド': '红色',
    'グリーン': '绿色',
    'イエロー': '黄色',
    'オレンジ': '橙色',
    'ピンク': '粉色',
    'パープル': '紫色',
    'ブラウン': '棕色',
    'ベージュ': '米色',
    'カーキ': '卡其色',
    'オリーブ': '橄榄绿',
    'シルバー': '银色',
    'ゴールド': '金色',
    'カモ': '迷彩',
    'ネオン': '荧光',
    'メタリック': '金属色',
    'バーガンディ': '酒红色',
    'マルーン': '栗色',
    'ターコイズ': '土耳其蓝',
    'ライム': '青柠色',
    'マゼンタ': '洋红色',
    'シアン': '青色',
    'ティール': '深青色',
    'アイボリー': '象牙色',
    'クリーム': '奶油色',
}

def translate_color_name(color_name: str) -> str:
    """将英文颜色名称翻译成中文
    
    支持自动大小写处理，优先级：
    1. 直接匹配
    2. 转大写匹配  
    3. 转首字母大写匹配
    4. 找不到返回原值
    
    Args:
        color_name: 英文颜色名称
        
    Returns:
        str: 中文颜色名称，找不到时返回原值
    """
    if not color_name:
        return color_name
    
    # 先尝试直接匹配
    if color_name in COLOR_NAME_TRANSLATION:
        return COLOR_NAME_TRANSLATION[color_name]
    
    # 尝试转大写匹配
    upper_name = color_name.upper()
    if upper_name in COLOR_NAME_TRANSLATION:
        return COLOR_NAME_TRANSLATION[upper_name]
    
    # 尝试转首字母大写匹配
    title_name = color_name.title()
    if title_name in COLOR_NAME_TRANSLATION:
        return COLOR_NAME_TRANSLATION[title_name]
    
    # 找不到就返回原值
    return color_name

def build_color_multiline(colors) -> str:
    """构建颜色多行字符串，只输出中文名称
    
    Args:
        colors: 颜色列表或字符串
        
    Returns:
        str: 换行分隔的纯中文颜色列表
    """
    if not colors:
        return ""
    
    # 如果是字符串，尝试分割
    if isinstance(colors, str):
        colors = [c.strip() for c in colors.split(',') if c.strip()]
    
    # 如果不是列表，转换为列表
    if not isinstance(colors, (list, tuple)):
        colors = [str(colors)]
    
    lines = []
    for color in colors:
        if not color:
            continue
        chinese = translate_color_name(str(color).strip())
        if chinese:
            lines.append(chinese)
    
    return "\n".join(lines)