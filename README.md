# OpenHands Custom Sandbox Images

Custom sandbox images let you preload the repo, dependencies, docs, and test harness your agent needs, so your agent starts the task instead of spending minutes provisioning a workspace.

![VS Code benchmark results](assets/vscode-benchmark-results-v2.svg)

## Why use a custom image

- `Faster path to useful work`
  The agent can reach the real task quickly instead of burning time on clone, install, transpile, and bootstrap steps.
- `Easier monorepo workflows`
  Repo checkout, dependencies, transpiled output, and helper tooling can already be present.
- `Easier complex test harness workflows`
  Native packages, headless browser support, Electron artifacts, and org-specific wrappers can be prebaked.
- `Lower setup variance and better reliability`
  Each run does not need to rediscover the same bootstrap steps, which reduces stalls, OOMs, and half-finished setup.

## Published benchmark

This repo includes a public VS Code benchmark where the agent fixes a bug and validates it with a real test suite. These results used the sandbox inside the [Enterprise OpenHands](https://docs.openhands.dev/enterprise) Replicated VM setup.

Biggest results:

- `43.1x` faster harness bootstrap after repo access
- `8.8x` faster repo availability
- `3.6x` faster end to end

| Elapsed work | Stock image | Custom image | Speedup |
| --- | ---: | ---: | ---: |
| Repo setup until available in workspace | `115.2s` | `13.1s` | `8.8x` |
| Bootstrap from repo-ready to first useful test | `581.4s` | `13.5s` | `43.1x` |
| Fix, rerun, and final response after first useful test | `152.2s` | `212.4s` | `0.7x` |
| Full end-to-end task | `848.7s` | `238.9s` | `3.6x` |

What these metrics mean:

Each row is an elapsed interval. The first three rows add up to the full task duration, modulo rounding. The custom image made the first useful test output appear much sooner because repo setup plus bootstrap dropped from about `696.5s` to `26.5s`.

The `Fix, rerun, and final response` row is conversation-dependent rather than image-dependent. At that point both environments can run the test, so the remaining time mostly reflects agent reasoning, file inspection, edit strategy, retries, and final-response latency. In this run the custom conversation spent longer after the first useful test, but the custom image still won end to end because it removed most of the cold setup work.

### What the results mean

The biggest win is not raw clone speed. The main bottleneck was getting the environment and test harness into a runnable state.

In the completed stock run, the expensive setup looked roughly like this:

- clone and checkout: about `115s`
- `npm install`: about `525s`
- transpile: about `28s`
- Electron prep: about `5s`

Once both environments were ready, the actual bug-fix loop was much smaller than the cold-start setup tax. That is the real value of a custom sandbox image: less environment assembly, faster verification, and more reliable agent runs.

In this benchmark, the stock image required a 6 GB sandbox to complete the install/test flow, while the custom image worked at 2 GB.

## Local agent-server benchmark

The same optimization also helps local OpenHands users who run an agent-server sandbox on their own machine. A local run is faster overall because Docker Desktop on a MacBook has more memory, local image layers, and a fast SSD compared with the Replicated VM benchmark environment, but the shape of the win is the same: the custom image avoids repeated repo and harness bootstrap work.

This local benchmark uses real OpenHands `DockerWorkspace` agent-server containers and runs commands through the agent-server bash API. It is not a dry run. To keep the measurement deterministic, the code edit is scripted rather than LLM-driven.

Local MacBook / Docker Desktop result, using `linux/arm64` images:

| Metric | Stock image | Custom image | Speedup |
| --- | ---: | ---: | ---: |
| Agent-server container ready | `3.3s` | `3.4s` | `1.0x` |
| Repo ready | `6.5s` | `0.1s` | `55.0x` |
| Runtime bootstrap before first test | `206.8s` | prebaked | n/a |
| First targeted test output | `218.1s` | `5.2s` | `42.3x` |
| Full scripted workload | `224.5s` | `14.6s` | `15.3x` |

Run the local benchmark:

```bash
docker build \
  --platform linux/arm64 \
  -f vscode-benchmark/Dockerfile \
  -t openhands-vscode-benchmark:local-arm64 \
  .

~/.local/share/uv/tools/openhands/bin/python \
  benchmarks/compare-vscode-local-agent-server.py
```

The local harness runs the same targeted VS Code Electron test, then applies the benchmark fix, retranspiles, and reruns the test until it passes. It uses `--no-sandbox` for the local Electron invocation because DockerWorkspace containers are not launched with the extra Linux namespace privileges Chromium's sandbox expects. That flag is local benchmark harness behavior and is separate from the Replicated VM benchmark prompts above.

In the stock local run, the expensive install/setup work is inside `Runtime bootstrap before first test`, not `Agent-server container ready`. That bootstrap phase runs the repo-local setup helper, including system package checks, `npm install`, transpile, extension transpile, and Electron prep. The custom image moves that work into Docker build time, so the task-time benchmark starts with the repo and harness already prepared.

## Build your own custom image

Canonical OpenHands sandbox image guide:

- https://docs.openhands.dev/sdk/guides/agent-server/docker-sandbox

The basic pattern is:

1. Start from the OpenHands agent-server base image.
2. Keep the normal OpenHands entrypoint intact.
3. Add your repo, docs, tools, and verification wrappers.
4. Pre-run the expensive setup you do not want to repeat at task time.
5. Publish the image to a registry and point Replicated at it.

The base image used here is:

```dockerfile
FROM ghcr.io/openhands/agent-server:1.23.0-python
```

Important rule:

- preserve normal OpenHands agent-server behavior
- extend the image; do not replace the runtime contract with a custom entrypoint

### Example: VS Code benchmark image

Build and push an amd64 image:

```bash
docker buildx build \
  --platform linux/amd64 \
  -f vscode-benchmark/Dockerfile \
  -t ghcr.io/<owner>/openhands-custom-image:vscode-benchmark \
  --push \
  .
```

That image prebakes:

- pinned repo checkout
- `node_modules`
- transpiled output
- Electron artifacts
- native packages such as `xvfb`, `libkrb5-dev`, `pkg-config`, `libx11-dev`, and `libxkbfile-dev`
- repo-local verification wrappers

### What to bake into local images

For local OpenHands use, a custom image makes sense when the same heavy setup is repeated across many tasks or sessions. Good candidates are pinned repo checkouts, package manager caches, installed dependencies, compiled or transpiled output, native system packages, browser or Electron artifacts, and stable helper scripts such as `prepare-*` and `*-verify` wrappers.

Avoid baking in secrets, personal credentials, machine-specific paths, uncommitted source changes, or task-specific fixes. If the repo or dependencies change constantly, keep a lightweight `prepare-*` command in the image so the agent can refresh only the parts that need to move.

## Configure Replicated VM Installer

In the Replicated installer, set:

- `Use a Custom Sandbox Image`: on
- `Sandbox Image Repository`: your image repository
- `Sandbox Image Tag`: your tag
- `Registry Server`: if required
- `Registry Username`: if required
- `Registry Password or Credentials`: if required

This feature is specifically for the sandbox / agent-server image, not every OpenHands service image.

## Reproduce the VS Code benchmark

### Stock image run

Use the stock sandbox image and this prompt:

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

Before you finish, summarize:
- what bootstrap/setup work was required before the first useful test output
- what code change fixed the bug
- what setup steps were most expensive or fragile
```

### Custom image run

Use the custom sandbox image and this prompt:

```text
Start by running prepare-vscode-benchmark. Then work in /workspace/vscode-benchmark.

Run the verification command first:

vscode-benchmark-verify

Then fix the bug in:
src/vs/platform/configuration/common/configurationModels.ts

Rerun vscode-benchmark-verify until it passes.

Before you finish, summarize which setup steps were already handled by the custom image.
```

### Analyze conversation exports

```bash
python3 benchmarks/analyze_conversation_export.py /path/to/conversation_export --show-events
```

That lets you compare:

- time to repo-ready state
- time to first useful test
- time to passing verification
- total conversation span
