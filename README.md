# OpenHands Custom Sandbox Benchmark Demo

This repo is a customer-shareable benchmark for demonstrating the value of custom OpenHands sandbox images.

It gives you two comparison modes:

- `blank sandbox`
  - clone or copy the seed repo into a fresh workspace
  - install dependencies
  - install doc-search dependencies
  - build the documentation index
  - run verification to get the first useful failure
- `custom sandbox`
  - start from an image that already contains the repo seed, dependencies, docs corpus, verification tooling, and a prebuilt search index
  - hydrate the live OpenHands workspace from the prebaked seed
  - get to the first useful failure much faster

## Results at a glance

The strongest benchmark in this repo is the public-repo VS Code comparison.

We ran the same bug-fix task in two environments:

- `stock sandbox image`
  - clone the benchmark repo
  - bootstrap the repo
  - reach the requested test command the hard way
- `custom sandbox image`
  - start with the pinned repo, dependencies, transpiled output, Electron artifacts, and native test dependencies already baked in

The benchmark task was:

- repo:
  - pinned VS Code benchmark fork
- bug location:
  - `src/vs/platform/configuration/common/configurationModels.ts`
- requested verification command:
  - `./scripts/test.sh --run src/vs/platform/configuration/test/common/configurationModels.test.ts --grep "excluded restricted properties"`

Benchmark repo shape for context:

- checked-out working tree: about `408 MB`
- files in the shallow benchmark checkout: about `14.8k`
- directories in the shallow benchmark checkout: about `4.3k`

These numbers are for the pinned benchmark repo before stock-image dependency installation, transpilation, or extra test artifacts.

Observed timings:

| Metric | Stock image | Custom image | Savings |
| --- | ---: | ---: | ---: |
| Repo available in workspace | `100.8s` | `13.1s` | `87.7s` |
| First targeted test execution | `279.4s` | `26.5s` | `252.9s` |
| Test bootstrap after repo access, before any code fix | `178.6s` | `13.5s` | `165.1s` |
| Engineering loop after first test: diagnosis, code fix, reruns | incomplete in captured run | `212.4s` | n/a |
| Completed task span | incomplete in captured run | `238.9s` | n/a |

What `First targeted test execution` means:

- this is the first point where the agent actually reached the specific benchmark test command above and got useful output from it
- it is the clearest “time to real work” metric in this README
- it is not just “the repo exists”
- it is not just “the agent started thinking”

What `Test bootstrap after repo access, before any code fix` means:

- this is not the bug-fix phase
- it is only the setup gap between “the repo is accessible” and “the requested benchmark test is actually running”
- it covers things like test discovery, dependency/bootstrap work, and getting the test runner into a usable state

What `Engineering loop after first test` means:

- this is the actual bug-fix phase
- it starts only after the agent has already reached the requested test and seen useful output
- it includes diagnosis, code edits, rerunning verification, and final reporting

What `Completed task span` means:

- this is the full wall-clock duration of the custom run
- it includes reading the repo, diagnosing the bug, editing files, rerunning verification, and writing the final summary
- it is a different phase from “time to first targeted test execution”
- the stock run did not complete, so there is no apples-to-apples total-span comparison yet

What the numbers show:

- the savings are not mainly about `git clone`
- the bigger win is avoiding the environment/bootstrap work between “repo exists” and “the agent can run the requested test”
- in this benchmark, the custom image saved about `4m 13s` to the first targeted test execution
- it also saved about `2m 45s` of test bootstrap work after the repo was already available
- the custom run still spent about `3m 32s` after the first test on the actual engineering loop: diagnosis, edits, and reruns

Why the stock run slowed down:

- clone and branch checkout
- repo inspection and test-runner discovery
- dependency/test bootstrap from `scripts/test.sh`
- then repeated missing-environment discovery across stock-image reruns:
  - first missing native dependency:
    - `gssapi/gssapi.h`
    - required package:
      - `libkrb5-dev`
  - next missing test/runtime dependencies:
    - `xvfb`
    - `pkg-config`
    - `libx11-dev`
    - `libxkbfile-dev`
  - after those packages were installed, the repo still was not in a runnable test state because the compiled output tree was missing:
    - `out/vs/base/common/`

What this means for the stock-image path:

- the stock baseline had to pay three separate bootstrap costs:
  - clone and checkout
  - install native/system dependencies
  - generate the transpiled/build output needed for the requested VS Code test path
- the benchmark did not stall on the bug itself
- it stalled because the repo environment was still being assembled

Why the custom run started faster:

- pinned repo checkout already present
- `node_modules` already present
- transpiled output already present
- Electron artifacts already present
- native packages already present
- headless test support via `xvfb` already present

Stock benchmark helper now available:

- the benchmark branch now includes repo-local helpers to reduce agent guesswork on the stock image:
  - `./scripts/openhands-stock-bootstrap.sh`
  - `./scripts/openhands-benchmark-status.sh`
  - `./scripts/openhands-benchmark-verify.sh`
- those scripts make the stock path more reproducible by emitting phase logs, skipping already-completed bootstrap phases, and wrapping the exact targeted verification command

Important caveat:

- the captured stock run was enough to show the setup penalty, but it did not complete end-to-end
- the custom run completed, but the agent used a pragmatic shortcut by editing the compiled JS under `out/` after confirming the TS-side root cause
- a stricter future benchmark should add a faster explicit recompilation path so the agent can fix TypeScript source and rerun verification without that detour
- if you want a fully guided stock baseline, the stock prompt should explicitly permit:
  - system package installs with `sudo`
  - `npm install`
  - `npm run gulp transpile-client-esbuild transpile-extensions`
  - `npm run electron`

## What is public and safe to share

Everything in this demo is synthetic:

- the monorepo
- the internal docs corpus
- the benchmark ballast
- the tests and verification workflow

There is no customer or internal production data in this repo.

That makes it suitable for:

- sharing with customers
- publishing as a public GitHub repo
- using as the seed workload for a blank-sandbox `git clone` comparison

## Repo layout

- `monorepo/`
  - the synthetic enterprise workload
- `Dockerfile`
  - builds the custom sandbox image on top of `ghcr.io/openhands/agent-server:1.23.0-python`
- `bin/company-verify`
  - company verification wrapper
- `bin/company-doc-search`
  - `bm25s`-backed doc search wrapper
- `bin/prepare-fintech-monorepo`
  - hydrates `/workspace/fintech-monorepo` from the prebaked seed
- `benchmarks/compare-image-startup.sh`
  - local benchmark harness
- `vscode-benchmark/`
  - VS Code-specific custom image variant and helpers for the public repo benchmark

## Why the repo is hydrated at runtime

OpenHands sandboxes mount a live workspace at runtime, so files baked directly under `/workspace/...` may not be visible when the sandbox starts.

To handle that cleanly:

- the image stores the prebaked seed at `/opt/fintech-monorepo-seed`
- the helper script `prepare-fintech-monorepo` copies that seed into `/workspace/fintech-monorepo`
- `company-doc-search` and `company-verify` call that hydration step automatically

This preserves normal OpenHands behavior while still giving you a realistic prewarmed environment.

## Search implementation

Doc search uses [`bm25s`](https://bm25s.github.io/), a lightweight Python BM25 library.

The image and benchmark both build a local lexical index from:

- `docs/**/*.md`
- `AGENTS.md`

Generated artifacts:

- `tools/doc-search-index/`
  - saved `bm25s` index
  - metadata for titles and snippets

The relevant files are:

- `monorepo/tools/build-doc-index.py`
- `bin/company-doc-search`
- `monorepo/tools/requirements-doc-search.txt`

## Demo task

Suggested OpenHands prompt:

```text
In /workspace/fintech-monorepo, update the payments fee calculation so premium customers receive the new discount described in the docs. Use company-doc-search if needed. Before you finish, run company-verify and fix any failures.
```

Expected flow:

- doc search points to the payments pricing docs
- the current code fails verification because it still uses the stale premium discount
- after the fix, `company-verify` passes

## Verification commands inside the sandbox

Hydrate the workspace explicitly if you want:

```bash
prepare-fintech-monorepo
```

Search docs:

```bash
company-doc-search "premium discount payments"
```

Run the verification suite:

```bash
company-verify
```

Show the repo contents:

```bash
fd . /workspace/fintech-monorepo
```

## Local build instructions

Build a local image:

```bash
docker build -t openhands-custom-image:latest /Users/rajiv.shah/Code/install_replicate/openhands-custom-image
```

Build with a specific size profile:

```bash
docker build \
  --build-arg DEMO_PROFILE=medium \
  -t openhands-custom-image:medium \
  /Users/rajiv.shah/Code/install_replicate/openhands-custom-image
```

Open a shell in the image:

```bash
docker run --rm -it --entrypoint bash openhands-custom-image:latest
```

## Publish instructions for Replicated

Example amd64 build for AWS-hosted OpenHands:

```bash
docker buildx build \
  --platform linux/amd64 \
  --build-arg DEMO_PROFILE=heavy \
  -t ghcr.io/<owner>/openhands-custom-image:<tag> \
  --push \
  /Users/rajiv.shah/Code/install_replicate/openhands-custom-image
```

Then configure Replicated with:

- `Sandbox Image Repository`: `ghcr.io/<owner>/openhands-custom-image`
- `Sandbox Image Tag`: `<tag>`
- `Registry Server`: only if needed
- `Registry Username`: only if needed
- `Registry Password or Credentials`: only if needed

## Local smoke check

The local harness is optional.

It is useful for quickly validating that:

- workspace hydration works
- doc search works
- verification works
- the custom image is meaningfully faster on the synthetic demo

It is not the main customer-facing proof point. The stronger benchmark is the public-repo VS Code comparison later in this README.

Run the local harness if you want a fast sanity check while developing the image:

```bash
/Users/rajiv.shah/Code/install_replicate/openhands-custom-image/benchmarks/compare-image-startup.sh \
  ghcr.io/<owner>/openhands-custom-image:<tag>
```

What it measures:

- `standard readiness`
  - time to prepare a blank sandbox until repo contents, dependencies, and searchable docs are usable
- `custom readiness`
  - time to hydrate the prebaked workspace and use the existing doc search
- `standard first test signal`
  - time until the blank sandbox can produce the first failing test signal
- `custom first test signal`
  - time until the prewarmed image can produce that same failing signal

Example local result from the updated hydration model on the `light` profile:

- `standard readiness`: `4.702s`
- `custom readiness`: `0.504s`
- `standard first test signal`: `4.166s`
- `custom first test signal`: `0.824s`
- `readiness speedup`: `9.33x`
- `feedback speedup`: `5.06x`

These are laptop-friendly validation numbers, not the primary enterprise benchmark.

## Public repo benchmark

For a real public-repo credibility benchmark, use the VS Code plan in:

- `benchmarks/vscode-benchmark-plan.md`
- `vscode-benchmark/README.md`

That benchmark is designed to show the value of a prewarmed sandbox on a large public repo with real setup and real test infrastructure, rather than just synthetic ballast.

Benchmark artifacts used for the published results above:

- custom-image export:
  - `conversation_cc6728d1578d429fa1cd78dc7015b8a5`
- stock-image export:
  - `conversation_42eb101dba684742871cfc19849a75fb`
- custom image tag:
  - `ghcr.io/rajshah4/openhands-custom-image:vscode-benchmark-2026-05-23-v2`

## Replicated A/B test protocol

To compare the stock sandbox image against the custom sandbox image in a live Replicated install:

1. Run a `baseline` conversation with the custom image feature turned off.
2. Run a `custom-image` conversation with the custom image feature turned on.
3. Export both conversations from OpenHands.
4. Analyze both exports with the included script.

Suggested baseline prompt:

```text
Clone https://github.com/rajshah4/openhands-custom-image into /workspace/project/openhands-custom-image. Work in the monorepo/ directory as your repo root. Update the payments fee calculation so premium customers receive the new discount described in the docs. Before you finish, run the repo verification flow and fix any failures.
```

Suggested custom-image prompt:

```text
In /workspace/fintech-monorepo, update the payments fee calculation so premium customers receive the new discount described in the docs. Use company-doc-search if needed. Before you finish, run company-verify and fix any failures.
```

Useful milestone patterns for the export analyzer:

```bash
python3 benchmarks/analyze_conversation_export.py /path/to/conversation_export \
  --pattern 'first_failure::FAIL|AssertionError|doc index not found' \
  --pattern 'verification_passed::company-verify passed|Tests .* passed'
```

You can also dump the full timeline:

```bash
python3 benchmarks/analyze_conversation_export.py /path/to/conversation_export --show-events
```

Primary metrics to compare:

- time to first meaningful verification failure
- time to passing verification
- total conversation span

## Size profiles

The demo supports scalable ballast profiles:

- `light`
  - quick local validation
- `medium`
  - laptop-friendly demo default
- `heavy`
  - stronger enterprise demo
- `xlarge`
  - only for bigger builders and longer pushes

You can also override ballast size directly:

```bash
docker build \
  --build-arg DEMO_PROFILE=medium \
  --build-arg ENTERPRISE_BALLAST_MB=10240 \
  -t openhands-custom-image:10gb \
  /Users/rajiv.shah/Code/install_replicate/openhands-custom-image
```

## Recommended customer-facing setup

For a clean customer comparison:

1. Publish this repo publicly.
2. Use the same repo as the canonical benchmark workload.
3. For the blank-sandbox path, clone or download the repo into the workspace and prepare the `monorepo/` seed.
4. For the custom-sandbox path, use the published image built from this repo.
5. Run the same prompt in both environments and compare:
   - time to usable workspace
   - time to first failing verification signal
   - time to green after the fix

If you want a stronger enterprise narrative, build a heavier image profile on a more powerful builder and rerun the same benchmark flow.
