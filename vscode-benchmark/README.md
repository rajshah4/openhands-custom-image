# VS Code Benchmark Image

This image is the public benchmark used in the main README.

It is meant to show that custom sandbox images do more than speed up clone time. They can also pre-package:

- repo checkout
- dependency install
- transpiled output
- Electron/runtime artifacts
- native packages needed by the test harness
- benchmark-specific helper scripts

That moves the agent from environment assembly to actual debugging much faster.

Canonical OpenHands sandbox image guide:

- https://docs.openhands.dev/sdk/guides/agent-server/docker-sandbox

Published benchmark image tag used in the custom run:

- `ghcr.io/rajshah4/openhands-custom-image:vscode-benchmark-2026-05-23-v2`

Latest rebuilt benchmark image with the current helper scripts:

- `ghcr.io/rajshah4/openhands-custom-image:vscode-benchmark-2026-05-23-v3`

## Prebaked contents

- VS Code benchmark repo:
  - `https://github.com/rajshah4/vscode-benchmark-repo`
- Benchmark branch:
  - `openhands-benchmark-01`
- Benchmark commit:
  - `9d16a199035b6640b955a21f1dddd1604ab3fe29`
- Installed dependencies
- Transpiled output needed for the benchmark task
- Electron download artifacts
- Headless test support via `xvfb`
- Native packages needed by the benchmark harness
- Helper tools:
  - `git`
  - `jq`
  - `rg`
  - `fd`
  - `curl`

## Benchmark task

Investigate the intentionally broken behavior for excluded restricted properties in configuration models and make the narrow verification command pass.

Relevant files:

- `src/vs/platform/configuration/common/configurationModels.ts`
- `src/vs/platform/configuration/test/common/configurationModels.test.ts`

## Workspace helpers

Hydrate the mounted OpenHands workspace path:

```bash
prepare-vscode-benchmark
```

That creates:

- `/workspace/vscode-benchmark -> /opt/vscode-benchmark-repo`

Run the narrow verification:

```bash
vscode-benchmark-verify
```

The helper runs the exact benchmark command with `VSCODE_SKIP_PRELAUNCH=1` so it does not redo Electron prelaunch work unnecessarily:

```bash
./scripts/test.sh --run src/vs/platform/configuration/test/common/configurationModels.test.ts --grep "excluded restricted properties"
```

## Build your own image

Build and push an amd64 image:

```bash
docker buildx build \
  --platform linux/amd64 \
  -f vscode-benchmark/Dockerfile \
  -t ghcr.io/<owner>/openhands-custom-image:vscode-benchmark \
  --push \
  .
```

Useful build args:

- `VSCODE_BENCHMARK_REPO`
- `VSCODE_BENCHMARK_REF`
- `VSCODE_BENCHMARK_COMMIT`

Example with an explicit branch and commit:

```bash
docker buildx build \
  --platform linux/amd64 \
  -f vscode-benchmark/Dockerfile \
  --build-arg VSCODE_BENCHMARK_REF=openhands-benchmark-01 \
  --build-arg VSCODE_BENCHMARK_COMMIT=9d16a199035b6640b955a21f1dddd1604ab3fe29 \
  -t ghcr.io/<owner>/openhands-custom-image:vscode-benchmark \
  --push \
  .
```

## Reproduce the benchmark

### Stock sandbox prompt

```text
Clone https://github.com/rajshah4/vscode-benchmark-repo.git into /workspace/project/vscode-benchmark, checkout branch openhands-benchmark-01, and work there.

Do not guess at bootstrap steps. Run the repo-local bootstrap helper first:

./scripts/openhands-stock-bootstrap.sh

If progress is unclear or something seems stuck, check:

./scripts/openhands-benchmark-status.sh

After bootstrap finishes, run:

./scripts/openhands-benchmark-verify.sh

Then fix the bug in:
src/vs/platform/configuration/common/configurationModels.ts

Rerun ./scripts/openhands-benchmark-verify.sh until it passes.
```

### Custom sandbox prompt

```text
Start by running prepare-vscode-benchmark. Then work in /workspace/vscode-benchmark.

Run the verification command first:

vscode-benchmark-verify

Then fix the bug in:
src/vs/platform/configuration/common/configurationModels.ts

Rerun vscode-benchmark-verify until it passes.
```

## Why the stock helper matters

The benchmark branch includes repo-local helpers that make the stock path more reproducible:

- `./scripts/openhands-stock-bootstrap.sh`
- `./scripts/openhands-benchmark-status.sh`
- `./scripts/openhands-benchmark-verify.sh`

These are useful because a large repo with a real harness is not just a clone problem. It is also:

- a dependency-install problem
- a transpile/build problem
- a native-package problem
- a “what exact test command should I run?” problem

The helper scripts reduce guesswork and emit phase logs, but they do not remove the fundamental cold-start setup cost. That is still what the custom image avoids.
