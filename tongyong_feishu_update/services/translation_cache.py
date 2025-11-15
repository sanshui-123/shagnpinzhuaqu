"""
翻译结果缓存工具
"""

from __future__ import annotations

import json
import hashlib
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime


class TranslationCache:
    """简单的基于 JSON 的翻译缓存"""

    def __init__(self, cache_path: Optional[Path] = None) -> None:
        services_dir = Path(__file__).resolve().parent
        default_cache = services_dir.parents[1] / 'results' / 'translation_cache.json'
        self.cache_path = cache_path or default_cache
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._data: Optional[dict] = None

    def _load(self) -> None:
        if self._data is not None:
            return

        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as fh:
                    self._data = json.load(fh)
            except Exception:
                self._data = {"items": {}}
        else:
            self._data = {"items": {}}

    def _save(self) -> None:
        if self._data is None:
            return

        with open(self.cache_path, 'w', encoding='utf-8') as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)

    @staticmethod
    def build_key(product_id: str, description: str) -> str:
        base = (product_id or 'unknown') + '::' + description
        return hashlib.sha256(base.encode('utf-8')).hexdigest()

    def get(self, product_id: str, description: str) -> Optional[str]:
        key = self.build_key(product_id, description)
        with self._lock:
            self._load()
            entry = self._data.get('items', {}).get(key)
            if isinstance(entry, dict):
                return entry.get('translation')
            return entry

    def set(self, product_id: str, description: str, translation: str) -> None:
        key = self.build_key(product_id, description)
        payload = {
            "translation": translation,
            "updatedAt": datetime.utcnow().isoformat() + 'Z',
            "productId": product_id,
        }
        with self._lock:
            self._load()
            self._data.setdefault('items', {})[key] = payload
            self._save()
