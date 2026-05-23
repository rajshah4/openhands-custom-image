#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import bm25s


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def first_meaningful_line(lines: list[str]) -> str:
    for line in lines:
      stripped = line.strip("# ").strip()
      if stripped:
        return stripped
    return "Untitled"


def build_index(repo_root: Path) -> dict:
    documents = []
    paths = sorted((repo_root / "docs").rglob("*.md"))
    paths.append(repo_root / "AGENTS.md")

    for path in paths:
        text = path.read_text()
        lines = text.splitlines()
        title = first_meaningful_line(lines)
        snippet = " ".join(line.strip() for line in lines[1:6] if line.strip())
        documents.append(
            {
                "path": str(path.relative_to(repo_root)),
                "title": title,
                "snippet": snippet[:220],
                "text": text,
            }
        )
    return {"documents": documents}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    index = build_index(repo_root)
    output_dir = repo_root / "tools" / "doc-search-index"
    metadata_path = output_dir / "metadata.json"

    shutil.rmtree(output_dir, ignore_errors=True)

    corpus_text = [doc["text"] for doc in index["documents"]]
    corpus_paths = [doc["path"] for doc in index["documents"]]
    retriever = bm25s.BM25(corpus=corpus_paths, method="lucene")
    retriever.index(bm25s.tokenize(corpus_text))
    retriever.save(str(output_dir))

    metadata = {
        "documents": [
            {
                "path": doc["path"],
                "title": doc["title"],
                "snippet": doc["snippet"],
            }
            for doc in index["documents"]
        ]
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True))
    print(f"wrote {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
