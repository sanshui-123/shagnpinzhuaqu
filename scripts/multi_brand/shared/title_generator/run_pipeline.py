"""
飞书更新流程 Python Runner - 步骤2实现
整合环境校验、缺失记录创建和业务逻辑的统一入口
"""

import sys
from typing import Optional

from .config.settings import validate_runtime, EnvironmentValidationError, GLMConnectionError
from .clients import create_glm_client, create_feishu_client
from .pipeline.update_orchestrator import UpdateOrchestrator
from .pipeline.streaming_orchestrator import StreamingUpdateOrchestrator
from .services.title_v6 import TitleGenerationError
from .models.update_result import UpdateResult


def main(
    input_path: str, 
    *,
    force_update: bool = False,
    title_only: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    streaming: bool = False,
    resume: bool = True,
    single_timeout: int = 60,
    save_interval: int = 5
) -> UpdateResult:
    """
    飞书更新流程主入口 - 支持批量和流式处理
    
    功能：
    1. 调用环境校验函数
    2. 调用"确保记录存在"函数
    3. 根据模式选择批量或流式处理
    
    Args:
        input_path: 产品数据文件路径
        force_update: 强制更新所有字段
        title_only: 仅更新标题字段
        dry_run: 干运行模式
        verbose: 显示详细进度
        streaming: 启用流式处理模式（推荐）
        resume: 是否启用断点续传（仅流式模式）
        single_timeout: 单个产品处理超时时间（秒）
        save_interval: 进度保存间隔
        
    Returns:
        UpdateResult: 更新结果
        
    Raises:
        EnvironmentValidationError: 环境配置错误
        GLMConnectionError: 智谱API连接失败
        TitleGenerationError: 标题生成失败
        RuntimeError: 其他业务逻辑错误
    """
    # ========================================================================
    # 步骤1：环境与网络校验
    # ========================================================================
    print("🔍 正在进行环境校验...")
    try:
        validate_runtime()
    except EnvironmentValidationError as e:
        print(f"❌ 环境校验失败：\n{e}")
        sys.exit(1)
    except GLMConnectionError as e:
        print(f"❌ 网络连接失败：\n{e}")
        sys.exit(1)
    
    # ========================================================================
    # 步骤2：创建客户端
    # ========================================================================
    print("🔧 正在初始化客户端...")
    try:
        glm_client = create_glm_client()
        feishu_client = create_feishu_client()
    except Exception as e:
        print(f"❌ 客户端初始化失败：{e}")
        sys.exit(1)
    
    # ========================================================================
    # 步骤3：设置进度回调（如果需要详细输出）
    # ========================================================================
    def progress_callback(event):
        if verbose:
            if event.message:
                print(f"[{event.event_type.value}] {event.message}")
            else:
                print(f"[{event.event_type.value}] {event.processed_count}/{event.total_count}")
    
    # ========================================================================
    # 步骤4：执行业务逻辑（根据模式选择批量或流式处理）
    # ========================================================================
    try:
        if streaming:
            print("🚀 开始执行流式更新流程...")
            orchestrator = StreamingUpdateOrchestrator(
                glm_client=glm_client,
                feishu_client=feishu_client,
                progress_callback=progress_callback if verbose else None,
                progress_save_interval=save_interval,
                single_timeout=single_timeout
            )
            
            result = orchestrator.execute(
                input_path=input_path,
                force_update=force_update,
                title_only=title_only,
                dry_run=dry_run,
                resume=resume
            )
        else:
            print("🚀 开始执行批量更新流程...")
            orchestrator = UpdateOrchestrator(
                glm_client=glm_client,
                feishu_client=feishu_client,
                progress_callback=progress_callback if verbose else None
            )
            
            # 这里会自动调用步骤3的环境校验和步骤4的缺失记录创建
            result = orchestrator.execute(
                input_path=input_path,
                force_update=force_update,
                title_only=title_only,
                dry_run=dry_run
            )
        
        print("✅ 飞书更新流程执行完成")
        return result
        
    except TitleGenerationError as e:
        print(f"❌ 标题生成失败：{e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ 飞书API操作失败：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行过程中发生未知错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    # 简单的命令行测试入口
    if len(sys.argv) < 2:
        print("用法: python -m CallawayJP.feishu_update.run_pipeline <input_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    result = main(input_path, verbose=True)
    print(result.to_summary(verbose=True))