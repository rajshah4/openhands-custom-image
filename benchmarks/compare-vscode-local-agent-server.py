#!/usr/bin/env python3
"""Benchmark VS Code setup through a local OpenHands DockerWorkspace.

This measures a deterministic local agent-server workload:

- start a real OpenHands agent-server container
- run commands through the agent-server bash API
- compare stock cold setup with a prebaked VS Code custom image
- run the same failing targeted test, apply the benchmark fix, and rerun it

Run with a Python environment that has the OpenHands SDK installed, for example:

    ~/.local/share/uv/tools/openhands/bin/python benchmarks/compare-vscode-local-agent-server.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

try:
    from openhands.workspace.docker import DockerWorkspace
except ImportError as exc:  # pragma: no cover - operator environment guard
    raise SystemExit(
        "OpenHands SDK import failed. Run this with the OpenHands tool Python, "
        "for example ~/.local/share/uv/tools/openhands/bin/python"
    ) from exc


BENCHMARK_REPO = "https://github.com/rajshah4/vscode-benchmark-repo.git"
BENCHMARK_BRANCH = "openhands-benchmark-01"
BENCHMARK_COMMIT = "9d16a199035b6640b955a21f1dddd1604ab3fe29"

STOCK_WORKDIR = "/workspace/project/vscode-benchmark"
CUSTOM_WORKDIR = "/workspace/vscode-benchmark"


@dataclass
class PhaseResult:
    name: str
    seconds: float
    exit_code: int | None = None
    expected_exit_codes: list[int] = field(default_factory=list)
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class RunResult:
    label: str
    image: str
    platform: str
    started_at: str
    phases: list[PhaseResult] = field(default_factory=list)
    total_seconds: float = 0.0
    failed: bool = False


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def tail(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def time_call(name: str, fn) -> tuple[float, object]:
    start = time.perf_counter()
    result = fn()
    seconds = time.perf_counter() - start
    print(f"{name}: {seconds:.1f}s", flush=True)
    return seconds, result


def run_command(
    run: RunResult,
    workspace: DockerWorkspace,
    name: str,
    command: str,
    *,
    timeout: float,
    cwd: str | None = None,
    expected_exit_codes: tuple[int, ...] = (0,),
) -> None:
    print(f"[{run.label}] {name}...", flush=True)
    start = time.perf_counter()
    result = workspace.execute_command(command, cwd=cwd, timeout=timeout)
    seconds = time.perf_counter() - start
    phase = PhaseResult(
        name=name,
        seconds=seconds,
        exit_code=result.exit_code,
        expected_exit_codes=list(expected_exit_codes),
        stdout_tail=tail(result.stdout),
        stderr_tail=tail(result.stderr),
    )
    run.phases.append(phase)
    print(f"[{run.label}] {name}: {seconds:.1f}s exit={result.exit_code}", flush=True)
    if result.exit_code not in expected_exit_codes:
        run.failed = True
        print(result.stdout[-2000:], file=sys.stderr)
        print(result.stderr[-2000:], file=sys.stderr)
        raise RuntimeError(
            f"{run.label}:{name} exited {result.exit_code}, "
            f"expected one of {expected_exit_codes}"
        )


def fix_command(workdir: str) -> str:
    return f"""
set -euo pipefail
cd {workdir}
python3 - <<'PY'
from pathlib import Path

path = Path('src/vs/platform/configuration/common/configurationModels.ts')
text = path.read_text()
text = text.replace(
    "\\n\\t\\tconst schema = propertySchema ?? excludedConfigurationProperties[key];\\n\\n\\t\\tif (options.exclude?.includes(key)) {{",
    "\\n\\t\\tif (options.exclude?.includes(key)) {{",
)
text = text.replace(
    "if (options.skipRestricted && schema?.restricted) {{",
    "if (options.skipRestricted && propertySchema?.restricted) {{",
)
text = text.replace(
    "\\n\\t\\tconst scope = schema ? typeof schema.scope !== 'undefined' ? schema.scope : ConfigurationScope.WINDOW : undefined;",
    "\\n\\t\\tconst schema = propertySchema ?? excludedConfigurationProperties[key];\\n\\t\\tconst scope = schema ? typeof schema.scope !== 'undefined' ? schema.scope : ConfigurationScope.WINDOW : undefined;",
)
path.write_text(text)
PY
git diff -- src/vs/platform/configuration/common/configurationModels.ts
"""


def transpile_command(workdir: str) -> str:
    return f"""
set -euo pipefail
cd {workdir}
node --experimental-strip-types --max-old-space-size=4096 \
  ./node_modules/gulp/bin/gulp.js transpile-client-esbuild
"""


def targeted_test_command(workdir: str) -> str:
    return f"""
set -euo pipefail
cd {workdir}
name="$(node -p "require('./product.json').applicationName")"
code=".build/electron/${{name}}"
crash_dir="${{PWD}}/.build/crashes"
xvfb-run -a -s "-screen 0 1280x1024x24" \
  env ELECTRON_ENABLE_LOGGING=1 VSCODE_SKIP_PRELAUNCH=1 \
  "${{code}}" test/unit/electron/index.js --no-sandbox \
    --crash-reporter-directory="${{crash_dir}}" \
    --run src/vs/platform/configuration/test/common/configurationModels.test.ts \
    --grep "excluded restricted properties"
"""


def run_stock(args: argparse.Namespace) -> RunResult:
    run = RunResult(
        label="stock",
        image=args.base_image,
        platform=args.platform,
        started_at=now(),
    )
    total_start = time.perf_counter()
    print(f"[stock] starting DockerWorkspace image={args.base_image}", flush=True)
    start = time.perf_counter()
    with DockerWorkspace(
        server_image=args.base_image,
        platform=args.platform,
        detach_logs=False,
        read_timeout=args.read_timeout,
    ) as workspace:
        run.phases.append(
            PhaseResult(
                name="agent_server_ready",
                seconds=time.perf_counter() - start,
                expected_exit_codes=[0],
            )
        )
        clone = f"""
set -euo pipefail
mkdir -p /workspace/project
cd /workspace/project
git clone --depth 1 --branch {BENCHMARK_BRANCH} {BENCHMARK_REPO} vscode-benchmark
cd vscode-benchmark
test "$(git rev-parse HEAD)" = "{BENCHMARK_COMMIT}"
"""
        run_command(
            run,
            workspace,
            "repo_ready_clone",
            clone,
            timeout=args.clone_timeout,
        )
        run_command(
            run,
            workspace,
            "bootstrap",
            "OPENHANDS_BENCHMARK_FORCE=1 ./scripts/openhands-stock-bootstrap.sh",
            cwd=STOCK_WORKDIR,
            timeout=args.bootstrap_timeout,
        )
        run_command(
            run,
            workspace,
            "first_targeted_test",
            targeted_test_command(STOCK_WORKDIR),
            timeout=args.test_timeout,
            expected_exit_codes=(1,),
        )
        run_command(
            run,
            workspace,
            "scripted_fix",
            fix_command(STOCK_WORKDIR),
            timeout=args.fix_timeout,
        )
        run_command(
            run,
            workspace,
            "transpile_after_fix",
            transpile_command(STOCK_WORKDIR),
            timeout=args.transpile_timeout,
        )
        run_command(
            run,
            workspace,
            "passing_targeted_test",
            targeted_test_command(STOCK_WORKDIR),
            timeout=args.test_timeout,
        )
    run.total_seconds = time.perf_counter() - total_start
    return run


def run_custom(args: argparse.Namespace) -> RunResult:
    run = RunResult(
        label="custom",
        image=args.custom_image,
        platform=args.platform,
        started_at=now(),
    )
    total_start = time.perf_counter()
    print(f"[custom] starting DockerWorkspace image={args.custom_image}", flush=True)
    start = time.perf_counter()
    with DockerWorkspace(
        server_image=args.custom_image,
        platform=args.platform,
        detach_logs=False,
        read_timeout=args.read_timeout,
    ) as workspace:
        run.phases.append(
            PhaseResult(
                name="agent_server_ready",
                seconds=time.perf_counter() - start,
                expected_exit_codes=[0],
            )
        )
        run_command(
            run,
            workspace,
            "repo_ready_prepare",
            f"""
set -euo pipefail
prepare-vscode-benchmark
cd {CUSTOM_WORKDIR}
test "$(git rev-parse HEAD)" = "{BENCHMARK_COMMIT}"
test -d node_modules
test -d out
""",
            timeout=args.prepare_timeout,
        )
        run_command(
            run,
            workspace,
            "first_targeted_test",
            targeted_test_command(CUSTOM_WORKDIR),
            timeout=args.test_timeout,
            expected_exit_codes=(1,),
        )
        run_command(
            run,
            workspace,
            "scripted_fix",
            fix_command(CUSTOM_WORKDIR),
            timeout=args.fix_timeout,
        )
        run_command(
            run,
            workspace,
            "transpile_after_fix",
            transpile_command(CUSTOM_WORKDIR),
            timeout=args.transpile_timeout,
        )
        run_command(
            run,
            workspace,
            "passing_targeted_test",
            targeted_test_command(CUSTOM_WORKDIR),
            timeout=args.test_timeout,
        )
    run.total_seconds = time.perf_counter() - total_start
    return run


def phase_map(run: RunResult) -> dict[str, float]:
    return {phase.name: phase.seconds for phase in run.phases}


def summarize(runs: list[RunResult]) -> dict[str, object]:
    stock = next(run for run in runs if run.label == "stock")
    custom = next(run for run in runs if run.label == "custom")
    stock_phases = phase_map(stock)
    custom_phases = phase_map(custom)
    pairs = {
        "agent_server_ready": ("agent_server_ready", "agent_server_ready"),
        "repo_ready": ("repo_ready_clone", "repo_ready_prepare"),
        "first_targeted_test": ("first_targeted_test", "first_targeted_test"),
        "transpile_after_fix": ("transpile_after_fix", "transpile_after_fix"),
        "passing_targeted_test": ("passing_targeted_test", "passing_targeted_test"),
    }
    comparisons: dict[str, dict[str, float]] = {}
    for label, (stock_key, custom_key) in pairs.items():
        stock_seconds = stock_phases[stock_key]
        custom_seconds = custom_phases[custom_key]
        comparisons[label] = {
            "stock_seconds": stock_seconds,
            "custom_seconds": custom_seconds,
            "speedup": stock_seconds / custom_seconds if custom_seconds else 0.0,
        }
    stock_to_first = (
        stock_phases["agent_server_ready"]
        + stock_phases["repo_ready_clone"]
        + stock_phases["bootstrap"]
        + stock_phases["first_targeted_test"]
    )
    custom_to_first = (
        custom_phases["agent_server_ready"]
        + custom_phases["repo_ready_prepare"]
        + custom_phases["first_targeted_test"]
    )
    comparisons["start_to_first_targeted_test"] = {
        "stock_seconds": stock_to_first,
        "custom_seconds": custom_to_first,
        "speedup": stock_to_first / custom_to_first if custom_to_first else 0.0,
    }
    comparisons["total_scripted_workload"] = {
        "stock_seconds": stock.total_seconds,
        "custom_seconds": custom.total_seconds,
        "speedup": stock.total_seconds / custom.total_seconds
        if custom.total_seconds
        else 0.0,
    }
    return {"comparisons": comparisons}


def print_summary(summary: dict[str, object]) -> None:
    comparisons = summary["comparisons"]
    assert isinstance(comparisons, dict)
    print()
    print("Results")
    print("-------")
    for name, values in comparisons.items():
        assert isinstance(values, dict)
        stock_seconds = float(values["stock_seconds"])
        custom_seconds = float(values["custom_seconds"])
        speedup = float(values["speedup"])
        print(
            f"{name:32s} stock={stock_seconds:7.1f}s "
            f"custom={custom_seconds:7.1f}s speedup={speedup:5.2f}x"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-image",
        default="ghcr.io/openhands/agent-server:1.23.0-python",
    )
    parser.add_argument(
        "--custom-image",
        default="openhands-vscode-benchmark:local-arm64",
    )
    parser.add_argument(
        "--platform",
        choices=("linux/amd64", "linux/arm64"),
        default="linux/arm64",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks/results"),
    )
    parser.add_argument("--read-timeout", type=float, default=1800.0)
    parser.add_argument("--clone-timeout", type=float, default=600.0)
    parser.add_argument("--prepare-timeout", type=float, default=120.0)
    parser.add_argument("--bootstrap-timeout", type=float, default=1800.0)
    parser.add_argument("--transpile-timeout", type=float, default=600.0)
    parser.add_argument("--test-timeout", type=float, default=900.0)
    parser.add_argument("--fix-timeout", type=float, default=120.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    runs: list[RunResult] = []
    failed = False
    try:
        runs.append(run_stock(args))
        runs.append(run_custom(args))
    except Exception as exc:
        failed = True
        print(f"benchmark failed: {exc}", file=sys.stderr)
    finally:
        summary: dict[str, object] = {}
        if len(runs) == 2:
            summary = summarize(runs)
            print_summary(summary)
        payload = {
            "created_at": now(),
            "benchmark": "local-vscode-agent-server",
            "failed": failed,
            "config": {
                "base_image": args.base_image,
                "custom_image": args.custom_image,
                "platform": args.platform,
                "benchmark_repo": BENCHMARK_REPO,
                "benchmark_branch": BENCHMARK_BRANCH,
                "benchmark_commit": BENCHMARK_COMMIT,
            },
            "runs": [asdict(run) for run in runs],
            "summary": summary,
        }
        output_path = args.output_dir / (
            "local-vscode-agent-server-"
            f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        output_path.write_text(json.dumps(payload, indent=2))
        print(f"\nwrote {output_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
