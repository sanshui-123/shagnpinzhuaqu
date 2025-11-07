#!/usr/bin/env bash
set -euo pipefail

# 进入CallawayJP目录
CALLAWAY_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$CALLAWAY_DIR"

# 检查 callaway.env 是否存在
if [[ ! -f "callaway.env" ]]; then
  echo "✗ 找不到 callaway.env，请先在CallawayJP目录创建并填写必需的环境变量。" >&2
  exit 1
fi

# 加载 callaway.env 中的所有变量，并导出给后续子进程
set -a
source callaway.env
set +a

# 允许传参覆盖抓取分类 & URL，否则使用默认（可自行改成 mens_all）
CATEGORY="${1:-womens_all}"
CATEGORY_URL="${2:-https://www.callawaygolf.jp/apparel/womens}"

echo "📂 工作目录: $CALLAWAY_DIR"
echo "🌐 抓取分类: $CATEGORY_URL"
echo "🏷️  分类标识: $CATEGORY"

echo "👉 Step 1 / 4: 抓取分类商品 ..."
node scripts/scrape_category.js \
  --url "$CATEGORY_URL" \
  --category "$CATEGORY" \
  --skip-if-unchanged \
  --overwrite-latest

echo "👉 Step 2 / 4: 合并去重 ..."
dedup_file=$(python3 scripts/merge_dedup.py \
  --category "$CATEGORY" \
  --print-path)
echo "   去重结果: $dedup_file"

echo "👉 Step 3 / 4: 同步缺失商品到飞书 ..."
cache_file="results/feishu_id_cache.json"
needs_sync="1"
if [[ -f "$cache_file" ]]; then
  needs_sync=$(dedup_file="$dedup_file" cache_file="$cache_file" python3 - <<'PY'
import json
import os

dedup_path = os.environ["dedup_file"]
cache_path = os.environ["cache_file"]

with open(dedup_path, "r", encoding="utf-8") as f:
    data = json.load(f)

dedup_ids = {
    item.get("productId")
    for item in data.get("products", [])
    if item.get("productId")
}

try:
    with open(cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)
    cache_ids = set(cache.get("ids", []))
except FileNotFoundError:
    print(1, end="")
    raise SystemExit

print(0 if dedup_ids.issubset(cache_ids) else 1, end="")
PY
)
  needs_sync=$(printf '%s' "$needs_sync" | tr -d '\n')
fi

if [[ "$needs_sync" == "1" ]]; then
  python3 scripts/sync_feishu_products.py \
    --input "$dedup_file"
else
  echo "   所有商品都已存在于飞书缓存中，跳过同步。"
fi

echo "👉 Step 4 / 4: 并行生成标题并更新飞书 ..."
# 如果 callaway.env 未给出，提供默认值
TITLE_WORKERS="${TITLE_WORKERS:-6}"
FEISHU_BATCH_SLEEP="${FEISHU_BATCH_SLEEP:-0.1}"
ZHIPU_TITLE_MODEL="${ZHIPU_TITLE_MODEL:-glm-4.5-air}"

TITLE_WORKERS=$TITLE_WORKERS \
FEISHU_BATCH_SLEEP=$FEISHU_BATCH_SLEEP \
ZHIPU_TITLE_MODEL=$ZHIPU_TITLE_MODEL \
python3 -m feishu_update.cli \
  --input "$dedup_file" \
  --verbose

echo "✅ 流程完成！"
