#!/usr/bin/env python
"""
DataPulse ETL Pipeline - Main Entry Point

Supports:
- Full and incremental extraction modes
- Dry-run validation
- Strict mode (fail on warnings)
"""
import sys
import argparse
from datetime import datetime, timezone

from pipeline.orchestration.run_pipeline import run, run_with_guard
from pipeline.utils.logging import get_logger

logger = get_logger("main")


def main():
    parser = argparse.ArgumentParser(
        description="DataPulse ETL Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode full
  python main.py --mode incremental
    python main.py --mode full --strict
  python main.py --dry-run
        """,
    )
    parser.add_argument(
        "--mode", choices=["full", "incremental"], default="full", help="Pipeline execution mode (default: full)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without loading to target")
    parser.add_argument("--strict", action="store_true", help="Fail pipeline on any validation warnings")
    parser.add_argument("--no-watermark", action="store_true", help="Disable watermark-based incremental loading")
    args = parser.parse_args()

    logger.info("Starting DataPulse ETL - Mode: %s", args.mode)
    start = datetime.now(timezone.utc)

    try:
        if args.strict:
            result = run_with_guard(
                mode=args.mode,
                dry_run=args.dry_run,
            )
        else:
            result = run(
                mode=args.mode,
                dry_run=args.dry_run,
                strict=False,
                use_watermark=not args.no_watermark,
            )

        if result.success:
            logger.info("Pipeline completed successfully in %s", result.duration)
            if result.summary:
                logger.info("Loaded: %s", result.summary)
            sys.exit(0)
        else:
            logger.error("Pipeline failed: %s", result.warnings)
            sys.exit(1)

    except RuntimeError as e:
        logger.error("Pipeline failed with guard: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
