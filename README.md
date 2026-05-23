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

Benchmark repo shape for context:

- checked-out working tree: about `408 MB`
- files in the shallow benchmark checkout: about `14.8k`
- directories in the shallow benchmark checkout: about `4.3k`

These numbers are for the pinned benchmark repo before stock-image dependency installation, transpilation, or extra test artifacts. The custom image also prebakes `node_modules`, transpiled output, Electron artifacts, and native packages needed for the test flow.

### VS Code benchmark results

We validated the public-repo benchmark against a pinned VS Code fork and a small intentional regression in:

- `src/vs/platform/configuration/common/configurationModels.ts`
- verification command:
  - `./scripts/test.sh --run src/vs/platform/configuration/test/common/configurationModels.test.ts --grep "excluded restricted properties"`

Custom-image run used:

- image: `ghcr.io/rajshah4/openhands-custom-image:vscode-benchmark-2026-05-23-v2`
- export:
  - `conversation_cc6728d1578d429fa1cd78dc7015b8a5`

Baseline run used:

- stock sandbox image
- export:
  - `conversation_42eb101dba684742871cfc19849a75fb`

Observed timings:

| Metric | Stock image | Custom image | Savings |
| --- | ---: | ---: | ---: |
| Repo available in workspace | `100.8s` | `13.1s` | `87.7s` |
| First meaningful verification attempt | `279.4s` | `26.5s` | `252.9s` |
| Setup between repo-ready and first test | `178.6s` | `13.5s` | `165.1s` |
| Completed task span | incomplete in captured run | `238.9s` | n/a |

How to interpret these numbers:

- `Repo available in workspace`
  - stock image had to clone the benchmark repo and check out the benchmark branch
  - custom image only had to run `prepare-vscode-benchmark`, which links the prebaked repo into the workspace
- `First meaningful verification attempt`
  - this is the first point where the agent actually reached the targeted failing test path
  - this is the strongest headline metric for the benchmark
- `Setup between repo-ready and first test`
  - this isolates the “environment bootstrap” tax after the repo is present
  - it includes dependency discovery, test-runner preparation, and other test readiness work

What the stock run spent time on:

- cloning the repo
- checking out the benchmark branch
- inspecting the repo and test scripts
- letting `scripts/test.sh` bootstrap dependencies and test prerequisites
- then failing on a missing native dependency:
  - `gssapi/gssapi.h`
  - attempted package install:
    - `apt-get install -y libkrb5-dev`

What the custom image already had baked in:

- pinned repo checkout
- `node_modules`
- transpiled output
- Electron artifacts
- native packages needed for the benchmark
- headless test support via `xvfb`

Practical conclusion:

- the validated savings are not “git clone is slow”
- the real win is avoiding the setup tax between “repo exists” and “agent can run the real verification command”
- in this benchmark, the custom image saved about `4m 13s` to first meaningful verification and about `2m 45s` of post-clone test-readiness work

Important caveat:

- the captured stock run was already enough to show the setup penalty, but it did not complete end-to-end
- the custom run completed, but the agent chose a pragmatic shortcut by editing the compiled JS under `out/` after confirming the TS-side root cause
- for a stricter benchmark, we should add a faster explicit recompilation path so the agent can fix the TypeScript source and rerun verification without that detour

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
