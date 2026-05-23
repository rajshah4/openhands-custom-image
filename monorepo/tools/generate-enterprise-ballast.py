#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

PROFILE_MB = {
    "light": 128,
    "medium": 512,
    "heavy": 2048,
    "xlarge": 5120,
}

FILE_SIZE_BYTES = 256 * 1024


def build_payload(label: str, index: int) -> bytes:
    header = (
        f"enterprise-ballast label={label} file={index}\n"
        "This synthetic repository ballast exists to model large enterprise monorepos,\n"
        "vendor trees, fixtures, generated SDKs, and internal reference materials.\n"
    ).encode("utf-8")
    pattern = (header + (b"MONOREPO-BALLAST-" * 256))[:4096]
    repeats = math.ceil(FILE_SIZE_BYTES / len(pattern))
    payload = (pattern * repeats)[:FILE_SIZE_BYTES]
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=sorted(PROFILE_MB), default="medium")
    parser.add_argument("--target-mb", type=int, default=None)
    args = parser.parse_args()

    target_mb = args.target_mb if args.target_mb is not None else PROFILE_MB[args.profile]
    target_bytes = target_mb * 1024 * 1024
    file_count = max(1, math.ceil(target_bytes / FILE_SIZE_BYTES))

    repo_root = Path(__file__).resolve().parents[1]
    ballast_root = repo_root / "fixtures" / "enterprise-ballast"
    ballast_root.mkdir(parents=True, exist_ok=True)

    shard_count = 16
    for shard in range(shard_count):
        (ballast_root / f"shard-{shard:02d}").mkdir(parents=True, exist_ok=True)

    payload_cache = build_payload(args.profile, 0)
    for index in range(file_count):
        shard_dir = ballast_root / f"shard-{index % shard_count:02d}"
        path = shard_dir / f"blob-{index:05d}.dat"
        if index == 0:
            payload = payload_cache
        else:
            payload = build_payload(args.profile, index)
        path.write_bytes(payload)

    manifest = ballast_root / "MANIFEST.txt"
    manifest.write_text(
        "\n".join(
            [
                f"profile={args.profile}",
                f"target_mb={target_mb}",
                f"file_size_bytes={FILE_SIZE_BYTES}",
                f"file_count={file_count}",
                f"estimated_total_bytes={file_count * FILE_SIZE_BYTES}",
            ]
        )
        + "\n"
    )

    print(f"wrote ballast to {ballast_root}")
    print(f"profile={args.profile} target_mb={target_mb} file_count={file_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
