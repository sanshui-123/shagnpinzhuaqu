# 飞书更新系统 v2.0 技术架构文档

**项目**: Callaway JP 飞书产品数据同步系统  
**版本**: v2.0  
**架构设计**: 分层模块化微服务架构  
**文档版本**: v1.0  

---

## 🏗️ 架构概览

### 1.1 设计原则
- **单一职责**: 每个模块专注于特定功能
- **开放封闭**: 对扩展开放，对修改封闭
- **依赖倒置**: 高层模块不依赖低层模块，都依赖抽象
- **接口隔离**: 使用小而专一的接口

### 1.2 架构分层
```
┌─────────────────────────────────────────────────────────────┐
│                        应用层 (CLI)                         │
├─────────────────────────────────────────────────────────────┤
│                      管道编排层 (Pipeline)                   │
├─────────────────────────────────────────────────────────────┤
│                       服务层 (Services)                     │
├─────────────────────────────────────────────────────────────┤
│                       数据层 (Models)                       │
├─────────────────────────────────────────────────────────────┤
│                      基础设施层 (Clients)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 数据层 (Models)

### 2.1 Product 模型
```python
@dataclass
class Product:
    """产品数据模型 - 系统核心数据结构"""
    
    # 基础标识
    product_id: str          # 产品ID (如: C25215200)
    brand_name: str          # 品牌名称
    product_name: str        # 产品名称
    product_url: str         # 产品链接
    
    # 商品属性
    category: str            # 分类
    price: Optional[str]     # 价格
    colors: List[str]        # 颜色列表
    sizes: List[str]         # 尺寸列表
    
    # 媒体资源
    main_image_url: Optional[str]    # 主图片URL
    image_urls: List[str]            # 其他图片URL列表
    
    # 生成字段
    generated_title: Optional[str]   # 生成的标题
    feishu_fields: Optional[Dict]    # 飞书字段映射
```

### 2.2 UpdateResult 模型
```python
@dataclass  
class UpdateResult:
    """更新结果模型 - 记录处理结果"""
    
    total_candidates: int        # 候选产品总数
    successful_updates: int      # 成功更新数量
    failed_updates: int          # 失败更新数量
    skipped_updates: int         # 跳过更新数量
    
    processing_time: float       # 处理耗时(秒)
    error_details: List[Dict]    # 错误详情列表
    success_details: List[Dict]  # 成功详情列表
```

### 2.3 Progress 模型
```python
@dataclass
class Progress:
    """进度追踪模型 - 实时进度反馈"""
    
    stage: str                   # 当前阶段
    current: int                 # 当前进度
    total: int                   # 总数
    message: str                 # 进度描述
    timestamp: datetime          # 时间戳
```

---

## 🔄 数据加载器层 (Loaders)

### 3.1 加载器接口设计
```python
class BaseProductLoader(ABC):
    """产品加载器基类 - 定义加载器接口标准"""
    
    @abstractmethod
    def can_handle(self, data: Dict) -> bool:
        """判断是否可以处理该数据格式"""
        pass
    
    @abstractmethod  
    def load_products(self, data: Dict) -> List[Product]:
        """加载产品数据，返回Product对象列表"""
        pass
    
    @abstractmethod
    def get_loader_type(self) -> str:
        """返回加载器类型标识"""
        pass
```

### 3.2 DetailedProductLoader
```python
class DetailedProductLoader(BaseProductLoader):
    """详细产品加载器 - 处理单个产品详情文件"""
    
    def can_handle(self, data: Dict) -> bool:
        """检测条件: 包含productId且无products数组"""
        return ('productId' in data and 
                'products' not in data and
                'detailUrl' in data)
    
    def load_products(self, data: Dict) -> List[Product]:
        """
        解析详细产品数据:
        - 支持完整的颜色/尺寸变体
        - 解析价格信息(priceText/salePrice)  
        - 提取所有图片URL
        """
        # 实现详细解析逻辑
        pass
```

### 3.3 SummarizedProductLoader  
```python
class SummarizedProductLoader(BaseProductLoader):
    """汇总产品加载器 - 处理去重后的产品集合"""
    
    def can_handle(self, data: Dict) -> bool:
        """检测条件: 包含products字段"""
        return 'products' in data
    
    def load_products(self, data: Dict) -> List[Product]:
        """
        解析汇总产品数据:
        - 支持products为数组或对象
        - 智能字段映射(detailUrl/productId/brandName等)
        - 批量数据处理优化
        """
        # 实现批量解析逻辑
        pass
```

### 3.4 LinkOnlyProductLoader
```python  
class LinkOnlyProductLoader(BaseProductLoader):
    """链接产品加载器 - 处理原始抓取链接"""
    
    def can_handle(self, data: Dict) -> bool:
        """检测条件: 包含links或rawLinks字段"""
        return ('links' in data or 
                'rawLinks' in data or
                self._has_link_structure(data))
    
    def load_products(self, data: Dict) -> List[Product]:
        """
        解析链接数据:
        - 价格字段自动映射(priceText/salePrice/mainPrice)
        - URL标准化处理
        - 基础产品信息提取
        """
        # 实现链接解析逻辑
        pass
```

### 3.5 LoaderFactory
```python
class LoaderFactory:
    """加载器工厂 - 自动选择合适的加载器"""
    
    def __init__(self):
        self.loaders = [
            DetailedProductLoader(),
            SummarizedProductLoader(), 
            LinkOnlyProductLoader()
        ]
    
    def get_loader(self, data: Dict) -> BaseProductLoader:
        """根据数据格式自动选择加载器"""
        for loader in self.loaders:
            if loader.can_handle(data):
                return loader
        raise ValueError("无法找到合适的数据加载器")
```

---

## 🛠️ 服务层 (Services)

### 4.1 TitleGenerator
```python
class TitleGenerator:
    """标题生成服务 - 基于GLM API生成产品标题"""
    
    def __init__(self, glm_client: GLMClient, config: TitleConfig):
        self.glm_client = glm_client
        self.config = config
        
    async def generate_title(self, product: Product) -> str:
        """
        生成标题逻辑:
        1. 构建GLM提示词模板
        2. 调用GLM API生成标题  
        3. 失败时使用fallback策略
        4. 返回最终标题
        """
        try:
            # 调用GLM API
            prompt = self._build_prompt(product)
            response = await self.glm_client.generate(prompt)
            return self._extract_title(response)
        except Exception as e:
            # Fallback策略
            return self._generate_fallback_title(product)
    
    def _build_prompt(self, product: Product) -> str:
        """构建GLM提示词"""
        return self.config.prompt_template.format(
            product_name=product.product_name,
            brand_name=product.brand_name,
            category=product.category
        )
    
    def _generate_fallback_title(self, product: Product) -> str:
        """生成备用标题"""
        return f"{product.brand_name} {product.product_name}"
```

### 4.2 FieldAssembler
```python
class FieldAssembler:
    """字段组装服务 - 将产品数据转换为飞书字段格式"""
    
    def assemble_fields(self, product: Product) -> Dict:
        """
        组装飞书字段:
        1. 标准化字段映射
        2. 数据类型转换
        3. 必填字段验证
        4. 返回飞书兼容格式
        """
        fields = {
            "商品ID": product.product_id,
            "商品名称": product.product_name, 
            "品牌": product.brand_name,
            "商品链接": product.product_url,
            "分类": product.category,
            "价格": product.price,
            "颜色": self._format_colors(product.colors),
            "尺寸": self._format_sizes(product.sizes),
            "主图": product.main_image_url,
            "生成标题": product.generated_title
        }
        
        # 过滤空值
        return {k: v for k, v in fields.items() if v is not None}
    
    def _format_colors(self, colors: List[str]) -> str:
        """格式化颜色列表"""
        return ", ".join(colors) if colors else ""
    
    def _format_sizes(self, sizes: List[str]) -> str:
        """格式化尺寸列表"""
        return ", ".join(sizes) if sizes else ""
```

### 4.3 Translator
```python
class Translator:
    """翻译服务 - 颜色和尺寸的中日文翻译"""
    
    def __init__(self, translation_config: TranslationConfig):
        self.color_dict = translation_config.color_translations
        self.size_dict = translation_config.size_translations
    
    def translate_color(self, color: str) -> str:
        """翻译颜色名称"""
        return self.color_dict.get(color.lower(), color)
    
    def translate_size(self, size: str) -> str:
        """翻译尺寸名称"""
        return self.size_dict.get(size.upper(), size)
    
    def translate_colors(self, colors: List[str]) -> List[str]:
        """批量翻译颜色"""
        return [self.translate_color(color) for color in colors]
    
    def translate_sizes(self, sizes: List[str]) -> List[str]:
        """批量翻译尺寸"""
        return [self.translate_size(size) for size in sizes]
```

---

## 📈 管道编排层 (Pipeline)

### 5.1 UpdateOrchestrator
```python
class UpdateOrchestrator:
    """更新编排器 - 整体流程控制和编排"""
    
    def __init__(self, 
                 loader_factory: LoaderFactory,
                 title_generator: TitleGenerator, 
                 field_assembler: FieldAssembler,
                 feishu_client: FeishuClient,
                 parallel_executor: ParallelExecutor):
        self.loader_factory = loader_factory
        self.title_generator = title_generator
        self.field_assembler = field_assembler  
        self.feishu_client = feishu_client
        self.parallel_executor = parallel_executor
    
    async def execute_update(self, input_file: str, dry_run: bool) -> UpdateResult:
        """
        执行完整更新流程:
        1. 加载和解析产品数据
        2. 筛选候选更新产品
        3. 并发生成标题
        4. 组装飞书字段
        5. 执行批量更新
        6. 汇总处理结果
        """
        # 步骤1: 加载产品数据
        products = await self._load_products(input_file)
        self._emit_progress("product_loaded", len(products), len(products), 
                           f"已加载 {len(products)} 个产品")
        
        # 步骤2: 筛选候选产品
        candidates = await self._filter_candidates(products)
        self._emit_progress("candidates_filtered", len(candidates), len(products),
                           f"筛选出 {len(candidates)} 个候选产品")
        
        # 步骤3: 并发生成标题
        await self._generate_titles_parallel(candidates)
        
        # 步骤4: 组装字段并更新
        if not dry_run:
            results = await self._execute_updates(candidates)
        else:
            results = self._simulate_updates(candidates)
        
        return results
    
    async def _load_products(self, input_file: str) -> List[Product]:
        """加载产品数据"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        loader = self.loader_factory.get_loader(data)
        return loader.load_products(data)
    
    async def _filter_candidates(self, products: List[Product]) -> List[Product]:
        """筛选候选更新产品 - 识别新产品"""
        existing_ids = await self.feishu_client.get_existing_product_ids()
        candidates = [p for p in products if p.product_id not in existing_ids]
        return candidates
        
    async def _generate_titles_parallel(self, products: List[Product]):
        """并发生成标题"""
        async def generate_single_title(product: Product):
            product.generated_title = await self.title_generator.generate_title(product)
            
        await self.parallel_executor.execute_tasks(
            [generate_single_title(p) for p in products],
            max_concurrency=5
        )
```

### 5.2 ParallelExecutor
```python
class ParallelExecutor:
    """并行执行器 - 控制并发任务执行"""
    
    def __init__(self, max_concurrency: int = 5, timeout: int = 300):
        self.max_concurrency = max_concurrency
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    async def execute_tasks(self, tasks: List[Callable], 
                          max_concurrency: Optional[int] = None) -> List[Any]:
        """
        并发执行任务:
        1. 控制并发度避免API限流
        2. 设置超时避免任务挂起
        3. 收集所有任务结果
        4. 处理异常和错误
        """
        if max_concurrency:
            semaphore = asyncio.Semaphore(max_concurrency)
        else:
            semaphore = self.semaphore
            
        async def execute_single_task(task):
            async with semaphore:
                try:
                    return await asyncio.wait_for(task, timeout=self.timeout)
                except asyncio.TimeoutError:
                    logger.error(f"任务超时: {task}")
                    raise
                except Exception as e:
                    logger.error(f"任务执行失败: {task}, 错误: {e}")
                    raise
        
        # 执行所有任务
        results = await asyncio.gather(
            *[execute_single_task(task) for task in tasks],
            return_exceptions=True
        )
        
        return results
```

---

## 🔌 基础设施层 (Clients)

### 6.1 FeishuClient
```python
class FeishuClient:
    """飞书客户端 - 封装飞书多维表格API"""
    
    def __init__(self, app_id: str, app_secret: str, 
                 app_token: str, table_id: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.table_id = table_id
        self.access_token = None
    
    async def get_existing_product_ids(self) -> Set[str]:
        """获取现有产品ID列表"""
        records = await self._fetch_all_records()
        return {record['fields']['商品ID'] for record in records 
                if '商品ID' in record['fields']}
    
    async def batch_create_records(self, records: List[Dict]) -> Dict:
        """批量创建记录"""
        # 分批处理,避免单次请求过大
        batch_size = 100
        results = {'successful': [], 'failed': []}
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                response = await self._create_records_batch(batch)
                results['successful'].extend(response.get('records', []))
            except Exception as e:
                logger.error(f"批量创建失败: {e}")
                results['failed'].extend(batch)
        
        return results
    
    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        if not self.access_token:
            # 实现token获取逻辑
            pass
        return self.access_token
```

### 6.2 DummyFeishuClient
```python
class DummyFeishuClient(FeishuClientInterface):
    """模拟飞书客户端 - 用于测试和干运行"""
    
    async def get_existing_product_ids(self) -> Set[str]:
        """返回空集合,所有产品都被视为新产品"""
        return set()
    
    async def batch_create_records(self, records: List[Dict]) -> Dict:
        """模拟成功创建"""
        return {
            'successful': records,
            'failed': []
        }
```

### 6.3 GLMClient
```python  
class GLMClient:
    """智谱AI客户端 - 封装GLM API调用"""
    
    def __init__(self, api_key: str, model: str = "glm-4"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    
    async def generate(self, prompt: str) -> str:
        """生成文本内容"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, 
                                  json=payload, 
                                  headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    raise GLMAPIError(f"API调用失败: {response.status}")
```

---

## 🎯 应用层 (CLI)

### 7.1 CLI接口设计
```python  
class CLI:
    """命令行接口 - 用户交互入口"""
    
    def __init__(self):
        self.orchestrator = self._build_orchestrator()
        
    def main(self):
        """CLI主入口"""
        parser = self._build_argument_parser()
        args = parser.parse_args()
        
        # 配置日志
        self._setup_logging(args.verbose)
        
        # 执行更新
        asyncio.run(self._execute_update(args))
    
    def _build_argument_parser(self) -> argparse.ArgumentParser:
        """构建命令行参数解析器"""
        parser = argparse.ArgumentParser(description='飞书产品数据同步工具')
        parser.add_argument('--input', required=True, help='输入数据文件路径')
        parser.add_argument('--dry-run', action='store_true', help='干运行模式')
        parser.add_argument('--verbose', action='store_true', help='详细输出')
        parser.add_argument('--config', help='配置文件路径')
        return parser
    
    async def _execute_update(self, args):
        """执行更新流程"""
        try:
            result = await self.orchestrator.execute_update(
                input_file=args.input,
                dry_run=args.dry_run
            )
            
            # 输出结果
            self._print_result_summary(result)
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            sys.exit(1)
```

---

## 📋 配置管理

### 8.1 配置结构
```python
# config/settings.py
class Settings:
    """全局设置配置"""
    ZHIPU_API_KEY: str = os.getenv('ZHIPU_API_KEY')
    FEISHU_APP_ID: str = os.getenv('FEISHU_APP_ID')
    FEISHU_APP_SECRET: str = os.getenv('FEISHU_APP_SECRET')
    FEISHU_APP_TOKEN: str = os.getenv('FEISHU_APP_TOKEN')
    FEISHU_TABLE_ID: str = os.getenv('FEISHU_TABLE_ID')
    
    # 性能配置
    MAX_CONCURRENCY: int = 5
    TIMEOUT_SECONDS: int = 300
    BATCH_SIZE: int = 100

# config/brands.py  
BRAND_CONFIG = {
    'callawaygolf': {
        'display_name': 'Callaway Golf',
        'categories': ['トップス', 'ボトムス', 'アクセサリー'],
        'url_patterns': [r'callawaygolf\.jp']
    }
}

# config/translation.py
COLOR_TRANSLATIONS = {
    'black': '黑色',
    'white': '白色', 
    'red': '红色',
    'blue': '蓝色'
}

SIZE_TRANSLATIONS = {
    'S': 'S',
    'M': 'M', 
    'L': 'L',
    'XL': 'XL'
}
```

---

## 🔍 错误处理策略

### 9.1 异常层次结构
```python
class FeishuUpdateError(Exception):
    """飞书更新系统基础异常"""
    pass

class LoaderError(FeishuUpdateError):
    """数据加载异常"""
    pass

class GLMAPIError(FeishuUpdateError):
    """GLM API调用异常"""
    pass

class FeishuAPIError(FeishuUpdateError):
    """飞书API调用异常"""
    pass

class ValidationError(FeishuUpdateError):
    """数据验证异常"""
    pass
```

### 9.2 容错机制
- **GLM API故障**: 自动fallback到基础标题生成
- **飞书API限流**: 指数退避重试策略
- **数据解析失败**: 跳过问题记录,继续处理其他数据
- **网络超时**: 任务级别超时控制和重试

---

## 📊 监控和指标

### 10.1 关键指标
- **数据处理指标**: 加载成功率、解析成功率、更新成功率
- **API调用指标**: GLM API成功率、飞书API成功率、响应时间
- **性能指标**: 端到端处理时间、并发任务完成时间
- **错误指标**: 异常类型分布、失败原因统计

### 10.2 日志策略
```python
import logging
import structlog

# 结构化日志配置
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# 使用示例
logger = structlog.get_logger()
logger.info("产品加载完成", 
           total_count=184, 
           loader_type="SummarizedProductLoader",
           processing_time=1.2)
```

---

## 🚀 部署考虑

### 11.1 环境要求
- **Python版本**: 3.8+
- **内存要求**: 最小512MB,推荐1GB+  
- **网络要求**: 稳定的外网访问(GLM API、飞书API)
- **存储要求**: 最小100MB可用空间

### 11.2 扩展性设计
- **水平扩展**: 支持多实例并行处理不同数据源
- **垂直扩展**: 可配置的并发度和批处理大小
- **新数据源接入**: 通过实现BaseProductLoader接口轻松扩展
- **新服务集成**: 通过依赖注入集成新的外部服务

---

**总结**: 本架构文档详细描述了飞书更新系统v2.0的技术实现，采用分层模块化设计，确保了系统的可维护性、可扩展性和可测试性。每个组件都有明确的职责边界和接口定义，为后续的功能扩展和维护提供了坚实的技术基础。

---

*文档生成时间: 2025-11-04*  
*维护负责人: Claude (AI Assistant)*  
*审核状态: 待技术审核*