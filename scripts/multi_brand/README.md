# 多品牌数据抓取系统

基于卡拉威现有系统扩展的15品牌数据抓取架构

## 🛡️ 安全设计原则

- **零影响**: 完全独立，不影响现有卡拉威流程
- **配置驱动**: 每个品牌独立配置，易于扩展
- **统一接口**: 单一CLI管理所有品牌
- **自动化运行**: 10天循环，无需人工干预

## 📁 目录结构

```
scripts/multi_brand/
├── core/                  # 核心系统
│   ├── cli.js            # 统一CLI入口
│   ├── scraper_engine.js # 统一抓取引擎
│   └── config_manager.js # 配置管理器
├── brands/               # 品牌配置
│   ├── callaway/         # 卡拉威（复用现有）
│   ├── taylormade/       # 泰勒梅
│   ├── titleist/         # Titleist
│   └── ...               # 其他12个品牌
├── monitoring/           # 监控系统
│   ├── health_monitor.js # 健康监控
│   └── scheduler.js      # 任务调度
└── utils/               # 工具模块
    ├── logger.js         # 统一日志
    └── validator.js     # 配置验证
```

## 🚀 快速开始

```bash
# 运行所有品牌
node scripts/multi_brand/core/cli.js run --all

# 运行特定品牌
node scripts/multi_brand/core/cli.js run --brand taylormade

# 查看所有状态
node scripts/multi_brand/core/cli.js status

# 健康检查
node scripts/multi_brand/core/cli.js health-check
```

## 📋 支持的品牌

- Callaway (卡拉威) - 复用现有系统
- TaylorMade (泰勒梅)
- Titleist
- Ping (乒)
- Cobra
- Bridgestone
- Mizuno (美津浓)
- Srixon (史力胜)
- PXG
- Honma (本间)
- Wilson Staff
- Adams Golf
- Cleveland Golf
- Scotty Cameron
- Odyssey

## ⏰ 调度计划

每个品牌独立按10天循环运行，确保时间分散：
- 第1天: Callaway, TaylorMade, Titleist
- 第2天: Ping, Cobra, Bridgestone
- 第3天: Mizuno, Srixon, PXG
- 第4天: Honma, Wilson Staff, Adams
- 第5天: Cleveland, Scotty, Odyssey
- 第6-10天: 休息和健康监控