FROM ghcr.io/openhands/agent-server:1.23.0-python

ARG DEMO_PROFILE=medium
ARG ENTERPRISE_BALLAST_MB=

ENV FINTECH_MONOREPO_ROOT=/workspace/fintech-monorepo
ENV FINTECH_MONOREPO_SEED_ROOT=/opt/fintech-monorepo-seed

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        fd-find \
        git \
        jq \
        npm \
        ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/fdfind /usr/local/bin/fd \
    && python3 -m pip install --no-cache-dir bm25s

COPY monorepo /opt/fintech-monorepo-seed
COPY bin/company-verify /usr/local/bin/company-verify
COPY bin/company-doc-search /usr/local/bin/company-doc-search
COPY bin/prepare-fintech-monorepo /usr/local/bin/prepare-fintech-monorepo
COPY bin/demo-blank-start.sh /usr/local/bin/demo-blank-start.sh
COPY bin/demo-prewarmed-start.sh /usr/local/bin/demo-prewarmed-start.sh

RUN chmod +x \
        /usr/local/bin/company-verify \
        /usr/local/bin/company-doc-search \
        /usr/local/bin/prepare-fintech-monorepo \
        /usr/local/bin/demo-blank-start.sh \
        /usr/local/bin/demo-prewarmed-start.sh \
    && cd /opt/fintech-monorepo-seed \
    && python3 tools/generate-large-corpus.py \
    && python3 tools/generate-enterprise-ballast.py --profile "$DEMO_PROFILE" ${ENTERPRISE_BALLAST_MB:+--target-mb "$ENTERPRISE_BALLAST_MB"} \
    && npm install \
    && python3 tools/build-doc-index.py \
    && chown -R openhands:openhands /opt/fintech-monorepo-seed

USER openhands
