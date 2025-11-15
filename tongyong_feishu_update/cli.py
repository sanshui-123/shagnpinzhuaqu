"""
命令行入口
"""
import argparse
import os
import sys

from .models.update_result import UpdateResult


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='GLM-Feishu 产品更新 CLI'
    )
    parser.add_argument('--input', required=True, help='产品数据文件路径')
    parser.add_argument('--force-update', action='store_true', help='强制更新所有字段')
    parser.add_argument('--dry-run', action='store_true', help='干运行模式，不写入飞书')
    parser.add_argument('--title-only', action='store_true', help='仅更新标题')
    parser.add_argument('--verbose', action='store_true', help='显示详细进度')
    
    # 新增流式处理选项
    parser.add_argument('--streaming', action='store_true', 
                       help='启用流式处理模式（推荐）：逐个产品处理并立即同步，支持断点续传')
    parser.add_argument('--no-resume', action='store_true',
                       help='禁用断点续传功能（仅在流式模式下有效）')
    parser.add_argument('--single-timeout', type=int, default=60,
                       help='单个产品处理超时时间（秒，默认60）')
    parser.add_argument('--save-interval', type=int, default=5,
                       help='进度保存间隔（处理N个产品后保存，默认5）')
    
    return parser.parse_args(argv)


def main(argv=None):
    """
    CLI主入口 - 步骤7修改版本
    现在转调 run_pipeline.main() 保持兼容性
    """
    args = parse_args(argv)
    
    # 转调新的 Runner，传递所有参数
    try:
        from .run_pipeline import main as pipeline_main
        
        result: UpdateResult = pipeline_main(
            input_path=args.input,
            force_update=args.force_update,
            title_only=args.title_only,
            dry_run=args.dry_run,
            verbose=args.verbose,
            streaming=args.streaming,
            resume=not args.no_resume,
            single_timeout=args.single_timeout,
            save_interval=args.save_interval
        )
        
        print(result.to_summary(verbose=args.verbose))
        
    except SystemExit:
        # Runner 中的 sys.exit() 调用，直接传递
        raise
    except Exception as e:
        print(f"❌ CLI 执行失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()