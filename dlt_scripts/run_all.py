import argparse
import sys
import os
from dlt_scripts.common import run_pipeline_by_name, PIPELINE_CONFIGS

# Default active pipelines matching the current workflow steps
DEFAULT_ACTIVE_PIPELINES = [
    "players",
    "draft_picks",
    "league",
    "rosters",
    "assets",
    "schedule",
    "scores",
    "standings",
    "results",
    "cap_penalties"
]

def main():
    parser = argparse.ArgumentParser(description="Run MFL DLT pipelines.")
    parser.add_argument(
        "--pipelines",
        type=str,
        help="Comma-separated list of specific pipeline names to run."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all pipelines defined in common.py including archived last year pipelines."
    )
    parser.add_argument(
        "--force-create",
        action="store_true",
        default=os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true",
        help="Force recreate pipeline destination tables (using drop_sources refresh mode)."
    )

    args = parser.parse_args()

    # Determine pipelines to run
    if args.pipelines:
        pipelines_to_run = [p.strip() for p in args.pipelines.split(",") if p.strip()]
    elif args.all:
        pipelines_to_run = list(PIPELINE_CONFIGS.keys())
    else:
        pipelines_to_run = DEFAULT_ACTIVE_PIPELINES

    # Validate pipelines
    invalid_pipelines = [p for p in pipelines_to_run if p not in PIPELINE_CONFIGS]
    if invalid_pipelines:
        print(f"Error: Unknown pipeline(s): {', '.join(invalid_pipelines)}", file=sys.stderr)
        print(f"Available pipelines: {', '.join(PIPELINE_CONFIGS.keys())}", file=sys.stderr)
        sys.exit(1)

    print("=========================================")
    print("Starting MFL DLT Pipeline Execution Run")
    print(f"Pipelines to run: {', '.join(pipelines_to_run)}")
    print(f"Force create mode: {args.force_create}")
    print("=========================================\n")

    results = {}
    failed = False

    for name in pipelines_to_run:
        print(f"--> Running pipeline: {name} ...")
        try:
            run_pipeline_by_name(name, force_create_mode=args.force_create)
            print(f"--> Pipeline {name} completed successfully!\n")
            results[name] = "SUCCESS"
        except Exception as e:
            print(f"--> Pipeline {name} FAILED: {e}\n", file=sys.stderr)
            results[name] = f"FAILED: {e}"
            failed = True

    print("=========================================")
    print("MFL DLT Pipeline Run Summary:")
    for name, status in results.items():
        print(f"  {name}: {status}")
    print("=========================================")

    if failed:
        print("One or more pipelines failed. Exiting with error.", file=sys.stderr)
        sys.exit(1)
    else:
        print("All pipelines completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
