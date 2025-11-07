#!/usr/bin/env bash
set -euo pipefail

CALLAWAY_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$CALLAWAY_DIR"

if [[ ! -f "callaway.env" ]]; then
  echo "✗ 找不到 callaway.env，请先配置环境变量。" >&2
  exit 1
fi

set -a
source callaway.env
set +a

TITLE_WORKERS=${TITLE_WORKERS:-6}
FEISHU_BATCH_SLEEP=${FEISHU_BATCH_SLEEP:-0.1}
ZHIPU_TITLE_MODEL=${ZHIPU_TITLE_MODEL:-glm-4.5-air}

TITLE_WORKERS=$TITLE_WORKERS \
FEISHU_BATCH_SLEEP=$FEISHU_BATCH_SLEEP \
ZHIPU_TITLE_MODEL=$ZHIPU_TITLE_MODEL \
python3 -m feishu_update.cli "$@"