#!/usr/bin/env bash
set -euo pipefail

BASE_IMAGE="${BASE_IMAGE:-ghcr.io/openhands/agent-server:1.23.0-python}"
CUSTOM_IMAGE="${1:-${CUSTOM_IMAGE:-}}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SEED_DIR="${SEED_DIR:-$SCRIPT_DIR/../monorepo}"

if [[ -z "$CUSTOM_IMAGE" ]]; then
  echo "usage: compare-image-startup.sh <custom-image-ref>" >&2
  echo "example: compare-image-startup.sh ghcr.io/rajshah4/openhands-custom-image:latest" >&2
  exit 1
fi

if [[ ! -d "$SEED_DIR" ]]; then
  echo "seed monorepo not found at $SEED_DIR" >&2
  exit 1
fi

prepare_standard_repo() {
  rm -rf /tmp/fintech-monorepo
  cp -R /seed /tmp/fintech-monorepo
  cd /tmp/fintech-monorepo
  rm -rf node_modules
  rm -rf tools/doc-search-index
  python3 -m pip install --quiet --disable-pip-version-check -r tools/requirements-doc-search.txt >/dev/null 2>&1
  python3 tools/build-doc-index.py >/dev/null
  npm install >/dev/null 2>&1
}

measure_seconds() {
  local start
  local end
  start="$(python3 -c 'import time; print(time.perf_counter())')"
  "$@"
  end="$(python3 -c 'import time; print(time.perf_counter())')"
  python3 -c "start=$start; end=$end; print(f'{end - start:.3f}')"
}

run_standard_readiness() {
  docker run --rm \
    --entrypoint bash \
    -v "$SEED_DIR:/seed:ro" \
    "$BASE_IMAGE" \
    -lc '
      set -euo pipefail
      '"$(declare -f prepare_standard_repo)"'
      prepare_standard_repo
      test -d node_modules
      test -d tools/doc-search-index
    '
}

run_custom_readiness() {
  docker run --rm \
    --entrypoint bash \
    "$CUSTOM_IMAGE" \
    -lc '
      set -euo pipefail
      prepare-fintech-monorepo >/dev/null
      cd /workspace/fintech-monorepo
      test -d node_modules
      test -d tools/doc-search-index
      company-doc-search "premium discount payments" >/dev/null
    '
}

run_standard_feedback() {
  docker run --rm \
    --entrypoint bash \
    -v "$SEED_DIR:/seed:ro" \
    "$BASE_IMAGE" \
    -lc '
      set -euo pipefail
      '"$(declare -f prepare_standard_repo)"'
      prepare_standard_repo
      npm test >/tmp/standard-test.log 2>&1 || true
      grep -q "FAIL" /tmp/standard-test.log
    '
}

run_custom_feedback() {
  docker run --rm \
    --entrypoint bash \
    "$CUSTOM_IMAGE" \
    -lc '
      set -euo pipefail
      prepare-fintech-monorepo >/dev/null
      cd /workspace/fintech-monorepo
      npm test >/tmp/custom-test.log 2>&1 || true
      grep -q "FAIL" /tmp/custom-test.log
    '
}

echo "Benchmarking sandbox preparation..."
echo "  base image:   $BASE_IMAGE"
echo "  custom image: $CUSTOM_IMAGE"
echo

standard_readiness_seconds="$(measure_seconds run_standard_readiness)"
custom_readiness_seconds="$(measure_seconds run_custom_readiness)"
standard_feedback_seconds="$(measure_seconds run_standard_feedback)"
custom_feedback_seconds="$(measure_seconds run_custom_feedback)"

echo "Results"
echo "-------"
printf "standard readiness:          %ss\n" "$standard_readiness_seconds"
printf "custom readiness:            %ss\n" "$custom_readiness_seconds"
printf "standard first test signal:  %ss\n" "$standard_feedback_seconds"
printf "custom first test signal:    %ss\n" "$custom_feedback_seconds"
echo

if awk "BEGIN { exit !($custom_readiness_seconds > 0) }"; then
  printf "readiness speedup:           %.2fx\n" "$(awk "BEGIN { print $standard_readiness_seconds / $custom_readiness_seconds }")"
fi

if awk "BEGIN { exit !($custom_feedback_seconds > 0) }"; then
  printf "feedback speedup:            %.2fx\n" "$(awk "BEGIN { print $standard_feedback_seconds / $custom_feedback_seconds }")"
fi

echo
echo "Interpretation"
echo "--------------"
echo "Readiness measures how long it takes before the environment has repo contents,"
echo "installed dependencies, and searchable docs available."
echo
echo "First test signal measures how long it takes before an agent can get useful"
echo "verification feedback from the failing premium-discount task."
