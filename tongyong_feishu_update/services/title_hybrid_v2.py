"""
智能混合标题生成方案 A2
结合规则稳定性 + AI灵活性
"""

import random
import re
import os
from typing import Dict, List, Tuple, Optional

# ============================================================================
# 一、配置
# ============================================================================

# 模板库 - 4种基础结构
TITLE_TEMPLATES = [
    "{season}{brand}高尔夫{gender}{feature}{ending}",  # 基础款：季节+品牌+高尔夫+性别+特征+结尾
    "{feature}{season}{brand}高尔夫{gender}{ending}",  # 特征前置：突出产品特性
    "{season}{brand}{feature}高尔夫{gender}{ending}",  # 品牌+特征组合
    "{season}{brand}高尔夫{gender}{feature}款{ending}",  # 加"款"字，更正式
]

# 特征词修饰库
FEATURE_MODIFIERS = {
    '弹力': ['新款', '经典', '专业', '舒适', '透气', '修身', '宽松'],
    '保暖': ['加厚', '轻薄', '抓绒', '内里', '羽绒', '厚实'],
    '全拉链': ['运动', '休闲', '商务', '户外', '日常', '功能'],
    '两用': ['双面', '可拆卸', '多功能', '一衣两穿', '实用'],
    '轻量': ['超轻', '轻薄', '便携', '轻盈', '无负担'],
    '防风': ['防风', '挡风', '抗风', '耐磨', '防护'],
    '透气': ['透气', '网眼', '速干', '排汗', '通风'],
    '防水': ['防水', '防泼水', '晴雨两用', '全天候'],
    '速干': ['速干', '快干', '排汗', '透气', '清凉'],
    '棉服': ['棉服', '棉袄', '加棉', '保暖棉', '棉花'],
}

# AI润色提示词（简化版，避免触发推理）
AI_POLISH_PROMPTS = [
    "为标题添加1个形容词，保持25-30字：{}",
    "微调标题，加入时尚元素：{}",
    "优化标题，更吸引眼球：{}",
]

# ============================================================================
# 二、规则生成核心
# ============================================================================

class HybridTitleGenerator:
    """混合式标题生成器"""

    def __init__(self):
        self.glm_api_key = os.environ.get('ZHIPU_API_KEY')
        self.use_ai = True if self.glm_api_key else False

    def generate_title(self, product: Dict) -> str:
        """
        生成标题的主入口

        流程：
        1. 规则生成基础标题（保证不翻车）
        2. 随机选择模板结构
        3. 50%概率让AI润色（增加变化）
        """

        # 步骤1：提取基础信息
        base_info = self._extract_base_info(product)

        # 步骤2：生成特征词
        feature_info = self._generate_features(product, base_info)

        # 步骤3：选择模板
        template = random.choice(TITLE_TEMPLATES)

        # 步骤4：组合基础标题
        base_title = self._build_base_title(template, base_info, feature_info)

        # 步骤5：长度调整
        base_title = self._adjust_length(base_title)

        # 步骤6：AI润色（50%概率）
        if self.use_ai and random.random() < 0.5:
            enhanced_title = self._ai_polish(base_title)
            if enhanced_title and self._validate_title(enhanced_title):
                return enhanced_title

        return base_title

    def _extract_base_info(self, product: Dict) -> Dict:
        """提取产品基础信息"""
        name = product.get('productName', '')

        # 品牌信息
        brand_key, brand_chinese, _ = self._extract_brand(product)

        # 季节信息
        season = self._extract_season(name)

        # 性别信息
        gender = self._detect_gender(name)

        # 分类信息
        category = self._detect_category(name, product)
        is_accessory = self._is_accessory(category, name)

        return {
            'brand_key': brand_key,
            'brand_chinese': brand_chinese,
            'season': season,
            'gender': gender,
            'category': category,
            'is_accessory': is_accessory,
            'name': name
        }

    def _generate_features(self, product: Dict, base_info: Dict) -> Dict:
        """生成产品特征词"""
        name = base_info['name']
        is_accessory = base_info['is_accessory']

        # 核心特征
        core_features = []

        # 识别产品特性
        feature_mapping = {
            '中綿': '棉服',
            '中棉': '棉服',
            '裏起毛': '保暖',
            'フリース': '抓绒',
            'フルジップ': '全拉链',
            '全開': '全拉链',
            'ストレッチ': '弹力',
            '弾力': '弹力',
            '軽量': '轻量',
            'ライト': '轻量',
            '防風': '防风',
            'ウインド': '防风',
            '透湿': '透气',
            'メッシュ': '透气',
            '防水': '防水',
            '速乾': '速干',
            '2WAY': '两用',
            'ツーウェイ': '两用',
        }

        for jp, cn in feature_mapping.items():
            if jp in name:
                core_features.append(cn)
                break

        # 添加修饰词
        feature_words = []
        for feature in core_features:
            if feature in FEATURE_MODIFIERS:
                # 随机选择一个修饰词（30%概率）
                if random.random() < 0.3:
                    modifier = random.choice(FEATURE_MODIFIERS[feature])
                    feature_words.append(f"{modifier}{feature}")
                else:
                    feature_words.append(feature)
            else:
                feature_words.append(feature)

        # 如果没有识别到特征，使用默认
        if not feature_words:
            if is_accessory:
                feature_words = ['轻便']
            else:
                feature_words = ['舒适']

        # 结尾词
        ending = self._get_ending_word(base_info['category'], is_accessory, name)

        return {
            'features': feature_words,
            'ending': ending,
            'feature_str': ''.join(feature_words[:2])  # 最多取2个特征词
        }

    def _build_base_title(self, template: str, base_info: Dict, feature_info: Dict) -> str:
        """使用模板构建基础标题"""
        # 组合特征词
        feature_str = feature_info['feature_str']

        # 填充模板
        title = template.format(
            season=base_info['season'],
            brand=base_info['brand_chinese'],
            gender=base_info['gender'],
            feature=feature_str,
            ending=feature_info['ending']
        )

        # 特殊处理：如果是中棉，确保"棉服"出现
        if '中綿' in base_info['name'] or '中棉' in base_info['name']:
            if '棉服' not in title:
                title = title.replace('夹克', '棉服夹克')
                title = title.replace('外套', '棉服外套')

        return title

    def _adjust_length(self, title: str) -> str:
        """调整标题长度到25-30字"""
        current_len = len(title)

        if current_len < 25:
            # 需要增加长度
            add_words = ['新款', '正品', '运动', '专业', '经典', '时尚']

            for word in add_words:
                if current_len + len(word) <= 30:
                    # 在品牌后插入
                    if '卡拉威Callaway' in title:
                        title = title.replace('卡拉威Callaway', f'卡拉威{word}Callaway')
                    else:
                        title = word + title
                    current_len = len(title)
                    break

        elif current_len > 30:
            # 需要缩短
            title = title[:30]

        return title

    def _ai_polish(self, title: str) -> Optional[str]:
        """AI润色（简化版，避免触发推理）"""
        if not self.glm_api_key:
            return None

        try:
            import requests

            # 选择一个润色提示
            prompt = random.choice(AI_POLISH_PROMPTS).format(title)

            # 极简API调用
            response = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.glm_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4-flash",  # 使用flash模型，更稳定
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 50,
                    "temperature": 0.7  # 稍微增加随机性
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    content = data['choices'][0]['message'].get('content', '')
                    if content and len(content) >= 25 and len(content) <= 30:
                        return content.strip()

        except Exception as e:
            print(f"AI润色失败: {e}")

        return None

    def _validate_title(self, title: str) -> bool:
        """验证标题质量"""
        # 基础验证
        if not title or len(title) < 25 or len(title) > 30:
            return False

        # 必须包含的关键词
        required = ['卡拉威', 'Callaway', '高尔夫']
        if not all(word in title for word in required):
            return False

        return True

    # ============================================================================
    # 辅助函数
    # ============================================================================

    def _extract_brand(self, product: Dict) -> Tuple[str, str, str]:
        """提取品牌信息"""
        brand = product.get('brand', '').lower()
        if 'callaway' in brand:
            return 'callawaygolf', '卡拉威Callaway', '卡拉威'
        return 'unknown', '未知品牌', '未知'

    def _extract_season(self, name: str) -> str:
        """提取季节信息"""
        if '25' in name:
            return '25秋冬'
        if '24' in name:
            return '24秋冬'
        if '春夏' in name or 'spring' in name.lower():
            return '25春夏'
        return '25秋冬'

    def _detect_gender(self, name: str) -> str:
        """检测性别"""
        if 'MENS' in name or 'メンズ' in name or '男士' in name:
            return '男士'
        elif 'WOMENS' in name or 'レディース' in name or '女士' in name:
            return '女士'
        return '男士'  # 默认

    def _detect_category(self, name: str, product: Dict) -> str:
        """检测产品分类"""
        name_lower = name.lower()

        # 外套关键词
        if any(kw in name_lower for kw in ['ブルゾン', 'ジャケット', 'コート', 'アウター']):
            return '外套'

        # 上衣关键词
        if any(kw in name_lower for kw in ['シャツ', 'トップス', 'tシャツ', 'ポロ']):
            return '上衣'

        # 下装关键词
        if any(kw in name_lower for kw in ['パンツ', 'トラウザーズ']):
            return '下装'

        # 配件关键词
        if any(kw in name_lower for kw in ['ベルト', 'キャップ', 'グローブ']):
            return '配件'

        return product.get('category', '其他')

    def _is_accessory(self, category: str, name: str) -> bool:
        """判断是否为配件"""
        if category == '配件':
            return True
        accessory_keywords = ['帽子', '手套', '腰带', '皮带', '袜子', '毛巾']
        return any(kw in name for kw in accessory_keywords)

    def _get_ending_word(self, category: str, is_accessory: bool, name: str) -> str:
        """获取结尾词"""
        if is_accessory:
            # 配件类
            if 'ベルト' in name or '腰带' in name:
                return '腰带'
            elif 'キャップ' in name or '帽子' in name:
                return '帽子'
            elif 'グローブ' in name or '手套' in name:
                return '手套'
            else:
                return '腰带'
        else:
            # 服装类
            if category == '外套':
                return '夹克'
            elif category == '上衣':
                if 'ポロ' in name or 'POLO' in name:
                    return 'POLO衫'
                return '上衣'
            elif category == '下装':
                return '长裤'
            else:
                return '夹克'


# ============================================================================
# 三、测试函数
# ============================================================================

def test_hybrid_generator():
    """测试混合生成器"""
    generator = HybridTitleGenerator()

    # 测试产品
    test_products = [
        {
            'productName': 'スターストレッチ2WAY中綿ブルゾン (MENS)',
            'productId': 'C25215107',
            'brand': 'Callaway Golf',
            'category': '外套'
        },
        {
            'productName': 'スターストレッチフルジップブルゾン (MENS)',
            'productId': 'C25215100',
            'brand': 'Callaway Golf',
            'category': '外套'
        },
        {
            'productName': 'ウィンドストレッチ軽量ジャケット',
            'productId': 'C25215101',
            'brand': 'Callaway Golf',
            'category': '外套'
        }
    ]

    print("="*60)
    print("智能混合标题生成方案 A2 测试")
    print("="*60)

    for product in test_products:
        print(f"\n产品: {product['productId']}")
        print(f"名称: {product['productName']}")
        print("-" * 40)

        # 生成5个标题展示多样性
        titles = []
        for i in range(5):
            title = generator.generate_title(product)
            titles.append(title)
            print(f"{i+1}. {title} (长度: {len(title)})")

        # 检查重复率
        unique_titles = set(titles)
        print(f"重复率: {(5-len(unique_titles))/5*100:.1f}%")

        # 验证所有标题
        all_valid = all(25 <= len(t) <= 30 for t in titles)
        print(f"长度合规: {'✅' if all_valid else '❌'}")


if __name__ == "__main__":
    test_hybrid_generator()