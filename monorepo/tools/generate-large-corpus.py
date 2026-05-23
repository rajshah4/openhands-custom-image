#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

SERVICES = [
    "payments",
    "accounts",
    "risk",
    "ledger",
    "identity",
    "treasury",
]

SECTIONS = [
    "architecture",
    "ownership",
    "testing",
    "release",
    "operability",
    "compliance",
]


def make_doc(service: str, section: str, ordinal: int) -> str:
    title = f"{service.title()} {section.title()} Reference {ordinal:03d}"
    return f"""# {title}

Service: `{service}`
Section: `{section}`
Reference ID: `REF-{service[:3].upper()}-{ordinal:03d}`

## Context

This synthetic enterprise document is part of the large internal reference corpus used to demonstrate pre-warmed OpenHands sandboxes. Agents searching for architecture, testing, ownership, release guidance, policy checks, premium discount updates, and payments fee rules should be able to retrieve this file quickly from the prebuilt index.

## Details

The {service} domain shares contracts with the payments platform and follows company verification guidance. Every implementation touching premium pricing, contract enforcement, CI policy, or release guidance must run `company-verify` before completion.

For benchmark realism, this file intentionally contains enough prose to make cold doc-index generation non-trivial in a blank sandbox while remaining deterministic for demo builds. The internal teams maintain service maps, runbooks, interface notes, compliance mappings, release gates, and owner rosters in this corpus.

## Operational Notes

- owner group: `{service}-platform@company.example`
- escalation path: `{service}-oncall@company.example`
- verification requirement: `company-verify`
- search hint: use `company-doc-search "premium discount payments"`
- release policy: pricing changes require contract alignment and passing verification
"""


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    generated_root = repo_root / "docs" / "reference" / "generated"
    generated_root.mkdir(parents=True, exist_ok=True)

    for service in SERVICES:
        for section in SECTIONS:
            section_dir = generated_root / service / section
            section_dir.mkdir(parents=True, exist_ok=True)
            for ordinal in range(1, 21):
                path = section_dir / f"{section}-{ordinal:03d}.md"
                path.write_text(make_doc(service, section, ordinal))

    summary = generated_root / "README.md"
    summary.write_text(
        "# Generated Reference Corpus\n\n"
        "This directory is intentionally large enough to make cold documentation indexing measurable.\n"
    )
    print(f"wrote generated corpus to {generated_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
