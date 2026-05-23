# OpenHands Custom Sandbox Images

This repo is a customer-shareable benchmark for showing why custom OpenHands sandbox images matter.

The core idea is simple:

- a stock sandbox spends agent time on environment assembly
- a custom sandbox starts much closer to meaningful engineering work

That matters most when you have:

- large monorepos
- complicated test harnesses
- internal CLIs, policy checks, or SDKs
- docs and runbooks the agent needs to search
- expensive or fragile bootstrap steps

## Why you want a custom image

Custom images are useful when the problem is not just “can the agent edit code,” but “how much setup must happen before the agent can even start.”

The practical benefits are:

- `Faster time to first useful test`
  The agent reaches a failing verification step much sooner.
- `Easier monorepo workflows`
  Repo checkout, dependencies, transpiled output, and helper tooling can already be present.
- `Easier test harness workflows`
  Native packages, headless browser support, Electron artifacts, or org-specific wrappers can be prebaked.
- `Lower setup variance`
  Each run does not need to rediscover the same bootstrap steps.
- `Better reliability`
  Removing cold-start setup reduces the odds of agent stalls, OOMs, and half-finished bootstrap work.
- `Better use of agent time`
  The agent spends more time debugging and less time acting like a provisioning script.

## Published benchmark

The strongest benchmark in this repo is a public-repo comparison built around a pinned VS Code fork:

- repo: `https://github.com/rajshah4/vscode-benchmark-repo`
- branch: `openhands-benchmark-01`
- bug location:
  - `src/vs/platform/configuration/common/configurationModels.ts`
- targeted verification:
  - `./scripts/test.sh --run src/vs/platform/configuration/test/common/configurationModels.test.ts --grep "excluded restricted properties"`

Benchmark repo shape:

- checked-out working tree: about `408 MB`
- files: about `14.8k`
- directories: about `4.3k`

These numbers are before stock-image dependency installation, transpilation, and extra runtime artifacts.

Published custom image tag used for the custom run:

- `ghcr.io/rajshah4/openhands-custom-image:vscode-benchmark-2026-05-23-v2`

### Results

The completed stock run and successful custom run produced these timings:

| Metric | Stock image | Custom image | Savings |
| --- | ---: | ---: | ---: |
| Repo available in workspace | `115.2s` | `13.1s` | `102.1s` |
| First targeted test output | `696.5s` | `26.5s` | `670.0s` |
| Bootstrap after repo access, before first useful test | `581.4s` | `13.5s` | `567.9s` |
| End-to-end task completion | `848.7s` | `238.9s` | `609.8s` |

What these metrics mean:

- `Repo available in workspace`
  The repo exists and is accessible where the agent expects to work.
- `First targeted test output`
  The agent has reached the exact requested verification command and received useful output from it.
- `Bootstrap after repo access`
  The setup gap between “repo exists” and “the real test is running.”
- `End-to-end task completion`
  Full task span, including setup, diagnosis, edits, reruns, and final summary.

### What the results mean

The biggest win was not raw clone speed.

The biggest win was avoiding test-harness bootstrap:

- stock image needed about `9m 41s` after checkout just to reach the first useful test output
- custom image reached the same point in about `26.5s`

The stock bootstrap was dominated by:

- `npm install`: about `525s`
- transpile step: about `28s`
- Electron prep: about `5s`

Once both environments reached the actual bug-fix loop, the gap was much smaller:

- stock run:
  - about `132.7s` from first failing test to passing verification
- custom run:
  - about `181.6s` from first failing test to passing verification

That is the point of the benchmark:

- the hard part was not the code fix
- the hard part was getting the environment and harness into a runnable state

### Operational story

This benchmark also exposed a reliability point, not just a speed point.

Earlier stock-image runs hit runtime restarts because the sandbox was cold-starting a heavy repo and test stack inside a smaller memory limit. The stable stock comparison only became reliable after increasing sandbox memory to `6 GiB`.

That is part of the value story:

- stock image pushed more setup work into the live sandbox
- custom image removed much of that work up front
- that reduced both elapsed time and runtime pressure

## What this repo demonstrates

This repo now supports two useful stories.

### 1. Public credibility benchmark

The VS Code benchmark demonstrates:

- a real public repo
- a real contributor-style setup path
- a real targeted verification command
- a measurable difference between cold stock bootstrap and prebaked custom setup

Relevant files:

- [vscode-benchmark/README.md](/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/vscode-benchmark/README.md)
- [benchmarks/vscode-benchmark-plan.md](/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/benchmarks/vscode-benchmark-plan.md)
- [benchmarks/analyze_conversation_export.py](/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/benchmarks/analyze_conversation_export.py)

### 2. Synthetic enterprise demo

The synthetic fintech demo demonstrates:

- prebaked repo contents
- prebaked docs search
- prebaked org-style verification tooling
- large-workspace simulation

That demo is useful for local iteration and for showing how to package your own internal tooling.

Relevant files:

- [Dockerfile](/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/Dockerfile)
- [README-demo.md](/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/README-demo.md)
- Canonical OpenHands sandbox image guide: https://docs.openhands.dev/sdk/guides/agent-server/docker-sandbox

## Build your own custom image

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
- for the canonical base-image and sandbox-image guidance, use:
  https://docs.openhands.dev/sdk/guides/agent-server/docker-sandbox

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

### Example: synthetic enterprise image

Build the synthetic demo image:

```bash
docker buildx build \
  --platform linux/amd64 \
  --build-arg DEMO_PROFILE=heavy \
  -t ghcr.io/<owner>/openhands-custom-image:enterprise-demo \
  --push \
  .
```

## Configure Replicated

In the Replicated installer, set:

- `Use a Custom Sandbox Image`: on
- `Sandbox Image Repository`: your image repository
- `Sandbox Image Tag`: your tag
- `Registry Server`: if required
- `Registry Username`: if required
- `Registry Password or Credentials`: if required

This feature is specifically for the sandbox / agent-server image, not every OpenHands service image.

## Reproduce the published VS Code benchmark

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

## Additional docs

- [vscode-benchmark/README.md](/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/vscode-benchmark/README.md)
  VS Code-specific image build and reproduction details.
- [benchmarks/vscode-benchmark-plan.md](/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/benchmarks/vscode-benchmark-plan.md)
  Benchmark design notes and task choices.
- [README-demo.md](/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/README-demo.md)
  Synthetic enterprise demo details.

## Safe to share

Everything in this repo is synthetic or public-benchmark-oriented:

- synthetic docs and workload for the fintech demo
- public pinned benchmark fork for the VS Code comparison
- no customer or production data

That makes the repo suitable for:

- sharing with customers
- using as a benchmark reference
- adapting into your own custom sandbox image workflow
