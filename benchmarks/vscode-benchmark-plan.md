# VS Code Benchmark Plan

## Goal

Use `microsoft/vscode` as a public credibility benchmark for custom OpenHands sandbox images.

The point is not to prove that `git clone` is slow by itself. The point is to prove that a large public repo with real setup and real test infrastructure gets to a useful debugging loop materially faster when the sandbox is prewarmed.

Primary metrics:

- `time to repo ready`
- `time to first meaningful failing test`
- `time to passing targeted verification`
- `total conversation span`

## Why VS Code

`microsoft/vscode` is a strong benchmark target because it has:

- a large TypeScript-heavy codebase
- non-trivial contributor setup
- multiple official test layers:
  - unit tests
  - integration tests
  - extension tests
  - smoke tests
- documented build and test entrypoints

This makes it a better public benchmark than the synthetic repo alone.

## Source-backed constraints

Official VS Code docs indicate:

- a full build wants at least `4 cores` and `6 GB RAM`, with `8 GB` recommended
- unit tests are typically run with:
  - `./scripts/test.sh`
- integration tests are typically run with:
  - `./scripts/test-integration.sh`

Relevant source and docs:

- https://github.com/microsoft/vscode
- https://github.com/microsoft/vscode/wiki/How-to-Contribute
- https://github.com/microsoft/vscode/wiki/Writing-Tests

Local repo inspection also showed:

- `scripts/test.sh` installs dependencies if needed, ensures Electron is present, and runs unit/electron tests
- `scripts/test-integration.sh` supports narrow targeting with `--run`, `--runGlob`, `--grep`, and `--suite`
- CI compiles and transpiles code before many test flows

## What to benchmark

Do not benchmark raw clone time alone.

For VS Code, the real setup pain is a combination of:

- cloning the repo
- installing dependencies
- transpiling or compiling testable output
- downloading Electron
- discovering the right test command
- finding the right test scope

That means the benchmark should measure:

1. time until the repo is actually runnable for the chosen task
2. time until the agent gets the first useful failing test signal
3. time until that exact targeted verification passes

## Benchmark shape

### Stock image run

The stock sandbox should have to do the real setup work:

1. clone a pinned benchmark fork of VS Code
2. install dependencies
3. build or transpile the needed outputs
4. download Electron if required
5. discover and run the narrow test command
6. make the fix
7. rerun verification until it passes

### Custom image run

The custom sandbox should already contain:

1. the pinned benchmark fork checked out locally
2. installed `node_modules`
3. the relevant transpiled output
4. Electron already downloaded if the task needs it
5. a short repo-local note with:
  - repo path
  - benchmark task
  - exact verification command

That gives a clean “prewarmed enterprise repo” story.

## Important benchmark rule

Do not run against moving `microsoft/vscode` `main`.

Create a pinned benchmark fork and branch, then inject a small known regression into that branch.

Recommended structure:

- fork: `rajshah4/vscode-benchmark`
- branch: `openhands-benchmark-01`
- pin to a specific upstream commit
- add one intentional regression
- keep the test command and expected fix stable across stock and custom runs

This makes the benchmark repeatable.

## Recommended first task

Start with a targeted unit-test task, not a smoke test.

Best first candidate:

- source file:
  - `src/vs/platform/configuration/common/configurationModels.ts`
- test file:
  - `src/vs/platform/configuration/test/common/configurationModels.test.ts`
- target command:
  - `./scripts/test.sh --run src/vs/platform/configuration/test/common/configurationModels.test.ts --grep "excluded restricted properties"`

Why this is the best first task:

- bounded scope
- real VS Code code and real tests
- still requires meaningful setup before the test is runnable
- less brittle than UI or smoke flows

Suggested injected regression:

- break the handling of excluded restricted properties when `skipRestricted` is enabled
- expected outcome:
  - the targeted test fails first
  - a small code fix in `configurationModels.ts` makes it pass

## Secondary task options

### Option 2: search integration test

- source file:
  - `src/vs/workbench/services/search/node/textSearchAdapter.ts`
- test file:
  - `src/vs/workbench/services/search/test/node/textSearch.integrationTest.ts`
- target command:
  - `./scripts/test-integration.sh --run src/vs/workbench/services/search/test/node/textSearch.integrationTest.ts --grep "Text: e \\(with excludes\\)|Text: sibling exclude|Text: e \\(with includes and exclude\\)"`

Why use it:

- more “enterprise” than the unit test
- still narrower than a broad integration sweep

Tradeoff:

- heavier runtime and more moving parts

### Option 3: Git extension benchmark

- source area:
  - `extensions/git/src/`
- lighter unit-style command:
  - `cd extensions/git && npm test src/test/repositoryCache.test.ts`
- heavier integration-style command:
  - `./scripts/test-integration.sh --suite git --grep "reflects working tree changes|stages correctly"`

Why use it:

- feels very real to developers
- demonstrates extension compilation and extension-host testing

Tradeoff:

- more setup overhead
- slightly more brittle

## What the custom image should prebake

For the VS Code benchmark image, prebake:

- the pinned benchmark repo checkout
- `node_modules`
- transpiled output needed for the chosen task
- Electron download artifacts if the task uses `scripts/test.sh`
- helper tooling:
  - `git`
  - `jq`
  - `rg`
  - `fd`
  - `curl`
- a small operator note such as `/opt/vscode-benchmark/README-benchmark.md`

For the first unit-test benchmark, the image should likely pre-run:

- `npm install`
- `npm run gulp transpile-client-esbuild transpile-extensions`
- `npm run electron`

If the benchmark targets the Git extension, also pre-run the relevant extension compile step.

## Prompt templates

### Stock image prompt

```text
Clone the VS Code benchmark repo into /workspace/project/vscode-benchmark and work there. The benchmark branch contains a small intentional regression. Find the failing behavior related to excluded restricted properties in configuration models, run the narrow verification command for that area, fix the bug, and rerun the same verification until it passes. Before finishing, summarize the exact setup work you had to do before you could get the first useful failing test signal.
```

### Custom image prompt

```text
In the prewarmed VS Code benchmark repo, find the failing behavior related to excluded restricted properties in configuration models, run the narrow verification command for that area, fix the bug, and rerun the same verification until it passes. Before finishing, summarize which setup steps were already handled by the custom image.
```

## What to record from each run

For both stock and custom runs, capture:

- conversation export from OpenHands
- total conversation span
- first timestamp showing repo-ready state
- first timestamp showing the targeted failing test
- first timestamp showing the targeted test passing
- final completion timestamp
- any manual detours or agent confusion

The same export-analysis script already used for the synthetic benchmark can be reused here.

## Success criteria

The benchmark is successful if:

- the stock sandbox has to do real setup work before useful testing starts
- the custom sandbox avoids most of that setup work
- both runs use the same pinned repo state and same targeted verification command
- the custom run reaches first failure and passing verification materially faster
- the task remains small enough that the benchmark is reproducible

## Recommended rollout order

1. Build the pinned VS Code benchmark fork and branch.
2. Start with the unit-test task in `configurationModels`.
3. Run the stock-image benchmark once and confirm the setup pain is real.
4. Build a prewarmed custom image for that same repo state.
5. Run the custom-image benchmark.
6. If the delta is strong, optionally add the heavier search or Git-extension benchmark as a second proof point.
