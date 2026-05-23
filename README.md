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

## Benchmarking

Run the local benchmark harness:

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

Validated local result from the updated hydration model on the `light` profile:

- `standard readiness`: `4.702s`
- `custom readiness`: `0.504s`
- `standard first test signal`: `4.166s`
- `custom first test signal`: `0.824s`
- `readiness speedup`: `9.33x`
- `feedback speedup`: `5.06x`

These are laptop-friendly validation numbers, not the final enterprise story.

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
