FROM ghcr.io/openhands/agent-server:1.23.0-python

ARG VSCODE_BENCHMARK_REPO=https://github.com/rajshah4/vscode-benchmark-repo.git
ARG VSCODE_BENCHMARK_REF=openhands-benchmark-01
ARG VSCODE_BENCHMARK_COMMIT=9d16a199035b6640b955a21f1dddd1604ab3fe29

ENV VSCODE_BENCHMARK_SEED_ROOT=/opt/vscode-benchmark-repo
ENV VSCODE_BENCHMARK_WORKSPACE_ROOT=/workspace/vscode-benchmark
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV PUPPETEER_SKIP_DOWNLOAD=1
ENV CI=true

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fd-find \
        git \
        g++ \
        jq \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libkrb5-dev \
        libnspr4 \
        libnss3 \
        libx11-xcb1 \
        libx11-dev \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbfile-dev \
        libxkbcommon0 \
        libxrandr2 \
        libxshmfence1 \
        libxss1 \
        make \
        npm \
        pkg-config \
        ripgrep \
        xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/fdfind /usr/local/bin/fd

COPY vscode-benchmark/bin/prepare-vscode-benchmark /usr/local/bin/prepare-vscode-benchmark
COPY vscode-benchmark/bin/vscode-benchmark-verify /usr/local/bin/vscode-benchmark-verify
COPY vscode-benchmark/README.md /opt/vscode-benchmark-image/README.md

RUN chmod +x \
        /usr/local/bin/prepare-vscode-benchmark \
        /usr/local/bin/vscode-benchmark-verify \
    && git clone --depth 1 --branch "$VSCODE_BENCHMARK_REF" "$VSCODE_BENCHMARK_REPO" "$VSCODE_BENCHMARK_SEED_ROOT" \
    && cd "$VSCODE_BENCHMARK_SEED_ROOT" \
    && test "$(git rev-parse HEAD)" = "$VSCODE_BENCHMARK_COMMIT" \
    && npm install \
    && node --experimental-strip-types --max-old-space-size=4096 ./node_modules/gulp/bin/gulp.js transpile-client-esbuild transpile-extensions \
    && npm run electron \
    && chown -R openhands:openhands "$VSCODE_BENCHMARK_SEED_ROOT" /opt/vscode-benchmark-image

USER openhands
