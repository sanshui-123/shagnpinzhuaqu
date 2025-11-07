import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent / "data"

def load_fixture(name: str):
    """
    加载测试固件数据
    
    Args:
        name: 固件文件名 (例如: 'sample_product_details.json')
    
    Returns:
        dict: 解析后的JSON数据
    """
    with open(FIXTURE_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)