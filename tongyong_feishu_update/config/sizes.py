"""
尺码转换配置模块

提供日本尺码、美国尺码到中国尺码的转换功能
"""

from typing import List

# 最全面的日本尺码转换映射
JAPAN_SIZE_MAPPING = {
    # 女装
    'women': {
        '7': 'S (小号)',
        '9': 'M (中号)',
        '11': 'L (大号)',
        '13': 'XL (加大号)',
        '15': 'XXL (特大号)',
        '17': 'XXXL (超大号)'
    },
    # 男装/通用
    'unisex': {
        'XS': 'XS (特小号)',
        'S': 'S (小号)',
        'M': 'M (中号)',
        'L': 'L (大号)',
        'LL': 'XL (加大号)',
        'XL': 'XL (加大号)',
        '2L': 'XXL (特大号)',
        '3L': 'XXL (特大号)',
        'XXL': 'XXL (特大号)',
        '4L': 'XXXL (超大号)',
        'XXXL': 'XXXL (超大号)',
        '5L': 'XXXXL (超特大号)'
    },
    # 鞋码 (日本 → 中国)
    'shoes': {
        '23.0': '36',
        '23.5': '37',
        '24.0': '38',
        '24.5': '39',
        '25.0': '40',
        '25.5': '41',
        '26.0': '42',
        '26.5': '43',
        '27.0': '44',
        '27.5': '45',
        '28.0': '46'
    }
}

# 美国尺码 → 中国尺码转换表
SIZE_US_TO_CN = {
    # 字母尺码（美国偏大，建议买小一码）
    'XS': 'S',
    'S': 'M',
    'M': 'L',
    'L': 'XL',
    'XL': 'XXL',
    'XXL': 'XXXL',
    '2XL': 'XXXL',
    '3XL': 'XXXXL',
    # 女装数字尺码
    '0': 'XS',
    '2': 'S',
    '4': 'S',
    '6': 'M',
    '8': 'M',
    '10': 'L',
    '12': 'L',
    '14': 'XL',
    '16': 'XL',
    '18': 'XXL',
    # 男装领围尺码
    '14': 'S',
    '14.5': 'S',
    '15': 'M',
    '15.5': 'M',
    '16': 'L',
    '16.5': 'L',
    '17': 'XL',
    '17.5': 'XL',
    '18': 'XXL'
}

# 特殊尺码映射
SPECIAL_SIZE_MAPPING = {
    'XS': 'XS (特小号)',
    'FREE': '均码',
    'ONE SIZE': '均码',
    'ONESIZE': '均码',
    'OS': '均码',
    'F': '均码',
    'FR': '均码',
    'UNI': '均码',
    'UNISEX': '均码',
    'NA': '均码',
    'フリー': '均码'
}


def convert_size_to_cn(size: str, gender: str) -> str:
    """将日本/美国尺码转换为中国尺码字母标记"""
    if not size:
        return ""
    clean = str(size).strip()
    if not clean:
        return ""
    upper = clean.upper()
    
    # 特殊尺码 - 提取字母部分
    if clean in SPECIAL_SIZE_MAPPING:
        special_result = SPECIAL_SIZE_MAPPING[clean]
        # 提取字母部分，去掉括号和中文
        return special_result.split(' ')[0] if ' ' in special_result else special_result
    if upper in SPECIAL_SIZE_MAPPING:
        special_result = SPECIAL_SIZE_MAPPING[upper]
        return special_result.split(' ')[0] if ' ' in special_result else special_result
    
    # 女装数字尺码 - 提取字母部分
    if gender == '女' and clean in JAPAN_SIZE_MAPPING['women']:
        women_result = JAPAN_SIZE_MAPPING['women'][clean]
        return women_result.split(' ')[0] if ' ' in women_result else women_result
    
    # 通用尺码 - 提取字母部分
    if upper in JAPAN_SIZE_MAPPING['unisex']:
        unisex_result = JAPAN_SIZE_MAPPING['unisex'][upper]
        return unisex_result.split(' ')[0] if ' ' in unisex_result else unisex_result
    
    # 鞋码 - 直接返回数字
    if clean in JAPAN_SIZE_MAPPING['shoes']:
        return JAPAN_SIZE_MAPPING['shoes'][clean]
    
    # 美国尺码转换
    base = SIZE_US_TO_CN.get(upper)
    if base:
        if base in JAPAN_SIZE_MAPPING['unisex']:
            unisex_result = JAPAN_SIZE_MAPPING['unisex'][base]
            return unisex_result.split(' ')[0] if ' ' in unisex_result else unisex_result
        return base
    
    return clean


def build_size_multiline(sizes: List[str], gender: str) -> str:
    """构建尺码多行字符串，输出纯英文格式(S/M/L/XL)，特殊尺码返回均码"""
    if not sizes:
        return ""
    lines = []
    for size in sizes:
        clean = str(size).strip()
        if not clean:
            continue

        # 先检查是否是特殊尺码（FR, FREE, ONE SIZE等）
        upper = clean.upper()
        if upper in SPECIAL_SIZE_MAPPING:
            converted = SPECIAL_SIZE_MAPPING[upper]
        else:
            # 使用 convert_size_to_cn 获取纯英文尺码
            converted = convert_size_to_cn(clean, gender)

        if converted and converted not in lines:
            lines.append(converted)

    return "\n".join(lines)
