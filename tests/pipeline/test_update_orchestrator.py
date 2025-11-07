"""UpdateOrchestrator 测试用例

测试 UpdateOrchestrator 的完整流程
"""

import pytest
import json

from feishu_update.pipeline.update_orchestrator import UpdateOrchestrator
from feishu_update.clients.interfaces import GLMClientInterface, FeishuClientInterface
from feishu_update.services.title_generator import TitleGenerator
from feishu_update.services.translator import Translator
from feishu_update.services.field_assembler import FieldAssembler
from feishu_update.pipeline.parallel_executor import ParallelTitleExecutor
from tests.fixtures.products import load_fixture
from feishu_update.models.product import Product
from feishu_update.loaders.factory import LoaderFactory
from feishu_update.models.update_result import UpdateResult


class DummyGLMClient(GLMClientInterface):
    """模拟GLM客户端"""
    
    def generate_title(self, prompt, model=None, max_tokens=500, temperature=0.3):
        return "测试标题"
    
    def translate(self, prompt, model=None, max_tokens=4000, temperature=0.2):
        return "【产品描述】测试描述\n【产品亮点】✓ 测试亮点\n【材质信息】测试材质"


class DummyFeishuClient(FeishuClientInterface):
    """模拟飞书客户端"""
    
    def __init__(self):
        self.records = {}
        self.updated = []

    def get_records(self):
        return self.records

    def batch_update(self, records, batch_size=30):
        self.updated.extend(records)
        return {"success_count": len(records), "failed_batches": [], "total_batches": 1}


class TestUpdateOrchestrator:
    """UpdateOrchestrator 测试类"""
    
    def test_orchestrator_full_flow(self, tmp_path):
        """测试编排器完整流程"""
        data = load_fixture("sample_product_details.json")
        filepath = tmp_path / "input.json"
        filepath.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        glm = DummyGLMClient()
        feishu = DummyFeishuClient()
        orchestrator = UpdateOrchestrator(
            glm_client=glm,
            feishu_client=feishu,
        )

        result = orchestrator.execute(str(filepath))
        assert isinstance(result, UpdateResult)
        assert result.success_count == len(feishu.updated)
        assert result.failed_batches == []