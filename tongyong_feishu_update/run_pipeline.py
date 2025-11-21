"""
飞书更新流程 Python Runner - 步骤2实现
整合环境校验、缺失记录创建和业务逻辑的统一入口
"""

import argparse
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
    category_only: bool = False,
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
        category_only: 仅更新衣服分类字段
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

            # 检查断点续传状态文件
            if resume:
                from pathlib import Path
                progress_file = Path(input_path).stem + '_progress.json'
                if Path(progress_file).exists():
                    print(f"📝 断点续传启用：已存在进度文件 {progress_file}，之前处理过的产品将跳过。")
                    print(f"   若要强制重跑，请删除该文件或使用 --no-resume。")

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
                category_only=category_only,
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
                category_only=category_only,
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


def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='run_pipeline',
        description='飞书更新流程 - 将产品数据同步到飞书表格',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 基本用法
  python -m tongyong_feishu_update.run_pipeline input.json

  # 详细输出
  python -m tongyong_feishu_update.run_pipeline input.json --verbose

  # 流式处理模式（推荐用于大批量数据）
  python -m tongyong_feishu_update.run_pipeline input.json --streaming

  # 仅更新标题
  python -m tongyong_feishu_update.run_pipeline input.json --title-only

  # 强制更新所有字段
  python -m tongyong_feishu_update.run_pipeline input.json --force-update

  # 干运行模式（不实际更新飞书）
  python -m tongyong_feishu_update.run_pipeline input.json --dry-run
        '''
    )

    # 必需参数
    parser.add_argument(
        'input_path',
        help='输入的产品数据文件路径（JSON格式）'
    )

    # 处理模式选项
    mode_group = parser.add_argument_group('处理模式')
    mode_group.add_argument(
        '--streaming',
        action='store_true',
        help='启用流式处理模式（推荐用于大批量数据，支持断点续传）'
    )

    # 更新选项
    update_group = parser.add_argument_group('更新选项')
    update_group.add_argument(
        '--force-update',
        action='store_true',
        help='强制更新所有字段（默认仅更新空字段）'
    )
    update_group.add_argument(
        '--title-only',
        action='store_true',
        help='仅更新标题字段'
    )
    update_group.add_argument(
        '--category-only',
        action='store_true',
        help='仅更新衣服分类字段'
    )
    update_group.add_argument(
        '--dry-run',
        action='store_true',
        help='干运行模式（不实际更新飞书，仅显示处理结果）'
    )

    # 输出选项
    output_group = parser.add_argument_group('输出选项')
    output_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细进度信息'
    )
    output_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式（仅显示错误信息）'
    )

    # 高级选项
    advanced_group = parser.add_argument_group('高级选项')
    advanced_group.add_argument(
        '--no-resume',
        action='store_true',
        help='禁用断点续传（仅流式模式）'
    )
    advanced_group.add_argument(
        '--timeout',
        type=int,
        default=60,
        metavar='SECONDS',
        help='单个产品处理超时时间（秒，默认：60）'
    )
    advanced_group.add_argument(
        '--save-interval',
        type=int,
        default=5,
        metavar='COUNT',
        help='进度保存间隔（处理多少个产品保存一次，默认：5）'
    )

    return parser


if __name__ == "__main__":
    # 创建命令行参数解析器
    parser = create_argument_parser()
    args = parser.parse_args()

    # 验证输入文件
    import os
    if not os.path.exists(args.input_path):
        print(f"❌ 输入文件不存在: {args.input_path}")
        sys.exit(1)

    if not os.path.isfile(args.input_path):
        print(f"❌ 输入路径不是文件: {args.input_path}")
        sys.exit(1)

    # 设置详细输出
    verbose = args.verbose and not args.quiet

    # 显示使用的输入文件
    if verbose:
        print(f'🎯 使用的输入文件: {args.input_path}')

    # 调用主函数
    try:
        result = main(
            input_path=args.input_path,
            force_update=args.force_update,
            title_only=args.title_only,
            category_only=args.category_only,
            dry_run=args.dry_run,
            verbose=verbose,
            streaming=args.streaming,
            resume=not args.no_resume,
            single_timeout=args.timeout,
            save_interval=args.save_interval
        )

        # 显示结果摘要
        if not args.quiet:
            print(result.to_summary(verbose=verbose))

        # 根据结果设置退出码 - 只关注真正的批次失败
        # 标题预生成失败不计入错误（后续会在字段组装时重新生成）
        has_errors = len(result.failed_batches) > 0

        if has_errors:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(130)  # 标准的键盘中断退出码
    except Exception as e:
        print(f"❌ 执行过程中发生未预期的错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)