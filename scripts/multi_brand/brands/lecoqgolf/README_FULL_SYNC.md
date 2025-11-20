# Le Coq Golf 完整同步流程

## 一键执行脚本

`run_full_sync.sh` 现在包含完整的三步流程：

```bash
./run_full_sync.sh
```

## 流程说明

### Step 1: 抓取商品列表
- 使用 `scrape_category.js` 抓取Le Coq官网商品列表
- 生成文件：`golf_content/lecoqgolf/lecoqgolf_products_[时间戳].json`

### Step 1.5: 导入基础记录到飞书
- 使用 `import_basic_products.py` 将基础信息导入飞书
- 只导入商品ID、品牌名等基本字段
- 为后续详情抓取做准备

### Step 2: 抓详情并同步
- 使用 `sequential_sync.js` 顺序抓取每个商品的详情页
- 抓取完成后立即同步到飞书
- 支持断点续传（检测到 `sequential_sync_status.json` 时自动跳过已处理商品）

### Step 3: 库存巡检并同步（新增）
**自动执行，无需手动操作**

#### Step 3.1: 从飞书导出商品列表
```bash
python3 -m tongyong_feishu_update.tools.export_brand_products \
  --brand "Le Coq公鸡乐卡克" \
  --output "/tmp/lecoq_inventory_products.json"
```

#### Step 3.2: 运行库存巡检
```bash
node check_inventory.js \
  --input "/tmp/lecoq_inventory_products.json" \
  --output "/tmp/lecoq_inventory_result.json"
```

#### Step 3.3: 同步库存到飞书
```bash
python3 -m tongyong_feishu_update.run_inventory_sync \
  "/tmp/lecoq_inventory_result.json"
```

**更新的字段：**
- 颜色（过滤只保留有货的颜色）
- 尺码（过滤只保留有货的尺码）
- 库存状态（详细缺货信息，如"白色(M/L) 没货"）

---

## 使用方法

### 完整流程（推荐）
```bash
./run_full_sync.sh
```
执行所有步骤，包括：抓列表 → 导入飞书 → 抓详情同步 → 库存巡检

### 跳过Step 1（使用已有列表文件）
```bash
./run_full_sync.sh --skip-step1
```
适用场景：已经有最新的商品列表文件，只需要抓详情和库存

### 测试模式（限制处理数量）
```bash
./run_full_sync.sh --limit 10
```
只处理前10个商品，用于测试

### 组合使用
```bash
./run_full_sync.sh --skip-step1 --limit 5
```
使用已有列表，只处理前5个商品

---

## 输出文件位置

### 商品列表
```
golf_content/lecoqgolf/lecoqgolf_products_[时间戳].json
```

### 库存巡检结果
```
/tmp/lecoq_inventory_products.json  # 导出的商品列表
/tmp/lecoq_inventory_result.json    # 库存巡检结果
```

### 断点续传状态
```
sequential_sync_status.json  # Step 2 的断点续传状态
```

---

## 执行时间估算

以 382 个商品为例：

- **Step 1**: ~2-5 分钟（抓取列表）
- **Step 1.5**: ~1 分钟（导入基础记录）
- **Step 2**: ~30-60 分钟（抓详情，取决于商品数量）
- **Step 3**: ~2.5 小时（库存巡检，382个商品）

**总计**: ~3-4 小时

---

## 故障处理

### 进程中断
如果脚本执行过程中被中断：
1. Step 2 支持断点续传，重新运行会自动跳过已处理商品
2. Step 3 需要重新执行（会重新巡检所有商品）

### 查看进度
```bash
# 查看Step 2进度
cat sequential_sync_status.json | jq '.processed | length'

# 查看库存巡检进度（如果在后台运行）
tail -f /tmp/lecoq_inventory_check.log
```

### 只执行库存巡检
如果只想单独执行库存巡检（不执行Step 1-2）：

```bash
cd /Users/sanshui/Desktop/CallawayJP

# 1. 导出商品
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.tools.export_brand_products \
  --brand "Le Coq公鸡乐卡克" \
  --output "/tmp/lecoq_inventory_products.json"

# 2. 巡检库存
cd scripts/multi_brand/brands/lecoqgolf
node check_inventory.js \
  --input "/tmp/lecoq_inventory_products.json" \
  --output "/tmp/lecoq_inventory_result.json"

# 3. 同步到飞书
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.run_inventory_sync \
  "/tmp/lecoq_inventory_result.json"
```

---

## 注意事项

1. **环境变量**: 确保 `callaway.env` 文件存在且包含正确的飞书API凭证
2. **网络稳定性**: 库存巡检时间较长，建议使用稳定的网络连接
3. **并发控制**: 库存巡检默认并发3，延迟500ms，已优化性能
4. **断点续传**: Step 2 支持断点续传，Step 3 不支持（每次全量巡检）
5. **后台运行**: 对于大批量处理，建议使用 `nohup` 或 `screen` 在后台运行

---

## 版本历史

- **2025-11-20**: 添加 Step 3（库存巡检），实现一键完整同步
- **2025-11-19**: 优化 Step 2 性能，添加断点续传支持
- **2025-11-18**: 初始版本，包含 Step 1、1.5、2
