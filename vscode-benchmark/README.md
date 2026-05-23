# VS Code Benchmark Image

This image is a prewarmed OpenHands sandbox variant for benchmarking against a large public repository with real setup and real test infrastructure.

## Prebaked contents

- VS Code benchmark repo:
  - `https://github.com/rajshah4/vscode-benchmark-repo`
- Benchmark branch:
  - `openhands-benchmark-01`
- Benchmark commit:
  - `d2164c509e77cfc67fe51ced55e16af95e2d416b`
- Installed dependencies
- Transpiled output needed for the benchmark task
- Electron download artifacts
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

The exact command is:

```bash
./scripts/test.sh --run src/vs/platform/configuration/test/common/configurationModels.test.ts --grep "excluded restricted properties"
```
