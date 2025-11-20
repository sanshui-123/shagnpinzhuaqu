# PEARLY GATES 库存巡检快速参考

## 完整3步流程

### 步骤1：导出品牌商品列表

```bash
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.tools.export_brand_products \
  --brand "PEARLY GATES" \
  --output "/tmp/pg_products.json"
```

### 步骤2：运行库存巡检脚本

```bash
cd /Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/pg
node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory.json"
```

### 步骤3：同步库存结果到飞书

```bash
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.run_inventory_sync \
  "/tmp/pg_inventory.json"
```

---

## 常用变体

### 测试模式（前10个商品）

```bash
# 步骤1：导出
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.tools.export_brand_products \
  --brand "PEARLY GATES" \
  --output "/tmp/pg_products_test.json"

# 步骤2：巡检（限制10个）
cd /Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/pg
node check_inventory.js \
  --input "/tmp/pg_products_test.json" \
  --output "/tmp/pg_inventory_test.json" \
  --limit 10

# 步骤3：同步
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a
python3 -m tongyong_feishu_update.run_inventory_sync \
  "/tmp/pg_inventory_test.json"
```

### 后台运行（大批量）

```bash
# 步骤2：后台运行巡检
cd /Users/sanshui/Desktop/CallawayJP/scripts/multi_brand/brands/pg
nohup node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory.json" \
  > /tmp/pg_inventory_check.log 2>&1 &

# 监控进度
tail -f /tmp/pg_inventory_check.log

# 检查进程
ps aux | grep "pg.*check_inventory"
```

### 自定义性能参数

```bash
# 高速模式（并发5，延迟300ms）
node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory.json" \
  --concurrent 5 \
  --delay 300

# 保守模式（并发2，延迟1000ms）
node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory.json" \
  --concurrent 2 \
  --delay 1000
```

---

## 监控和诊断

### 查看实时进度

```bash
# 监控日志
tail -f /tmp/pg_inventory_check.log

# 查看最后20行
tail -20 /tmp/pg_inventory_check.log

# 统计完成数量
grep "✅ 详情页抓取完成" /tmp/pg_inventory_check.log | wc -l
```

### 查看结果摘要

```bash
# 查看完整摘要
cat /tmp/pg_inventory.json | jq '.summary'

# 查看成功数量
cat /tmp/pg_inventory.json | jq '.summary.success'

# 查看失败数量
cat /tmp/pg_inventory.json | jq '.summary.failed'

# 查看库存统计
cat /tmp/pg_inventory.json | jq '.summary | {inStock, partialStock, outOfStock}'
```

### 检查进程状态

```bash
# 查看运行中的巡检进程
ps aux | grep check_inventory.js | grep -v grep

# 查看进程详细信息
ps aux | grep "pg.*check_inventory"

# 杀死卡住的进程
pkill -f "pg.*check_inventory"
```

---

## 故障排除

### 问题：进程启动失败

```bash
# 检查输入文件是否存在
ls -la /tmp/pg_products.json

# 检查文件内容
head -20 /tmp/pg_products.json

# 验证JSON格式
cat /tmp/pg_products.json | jq '.' > /dev/null
```

### 问题：巡检速度太慢

```bash
# 增加并发数
node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory.json" \
  --concurrent 5

# 减少延迟
node check_inventory.js \
  --input "/tmp/pg_products.json" \
  --output "/tmp/pg_inventory.json" \
  --delay 300
```

### 问题：同步到飞书失败

```bash
# 检查环境变量
echo $FEISHU_APP_ID
echo $FEISHU_APP_SECRET
echo $FEISHU_APP_TOKEN
echo $FEISHU_TABLE_ID

# 重新加载环境变量
cd /Users/sanshui/Desktop/CallawayJP
set -a && source callaway.env && set +a

# 查看飞书同步详细日志
python3 -m tongyong_feishu_update.run_inventory_sync \
  "/tmp/pg_inventory.json" --verbose
```

---

## 性能参考

### 推荐配置

- **并发数**: 3
- **延迟**: 500ms
- **性能**: ~11分钟/30商品
- **稳定性**: ★★★★★

### 快速配置

- **并发数**: 5
- **延迟**: 300ms
- **性能**: ~7分钟/30商品
- **稳定性**: ★★★☆☆

### 保守配置

- **并发数**: 2
- **延迟**: 1000ms
- **性能**: ~14分钟/30商品
- **稳定性**: ★★★★★

---

## 帮助

```bash
# 查看完整帮助
node check_inventory.js --help

# 查看详细文档
cat /Users/sanshui/Desktop/CallawayJP/INVENTORY_CHECK_README.md
```
