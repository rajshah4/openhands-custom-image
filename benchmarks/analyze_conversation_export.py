#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class EventSummary:
    timestamp: datetime
    source: str
    kind: str
    text: str
    path: Path


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def extract_text(payload) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, list):
        parts = []
        for item in payload:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(payload, dict):
        parts = []
        for key in ("text", "reasoning_content", "command", "path"):
            value = payload.get(key)
            if value:
                parts.append(str(value))
        content = payload.get("content")
        if content:
            parts.append(extract_text(content))
        observation = payload.get("observation")
        if observation:
            parts.append(extract_text(observation))
        action = payload.get("action")
        if action:
            parts.append(extract_text(action))
        return "\n".join(part for part in parts if part)
    return str(payload)


def summarize_event(path: Path) -> EventSummary:
    data = json.loads(path.read_text())
    timestamp = parse_timestamp(data["timestamp"])
    source = data.get("source", "unknown")
    kind = data.get("kind", "unknown")

    parts = []
    for key in (
        "llm_message",
        "thought",
        "reasoning_content",
        "tool_name",
        "action",
        "observation",
        "extended_content",
        "system_prompt",
        "value",
    ):
        if key in data:
            parts.append(extract_text(data[key]))
    text = "\n".join(part for part in parts if part).strip()
    return EventSummary(timestamp=timestamp, source=source, kind=kind, text=text, path=path)


def iter_events(export_dir: Path) -> Iterable[EventSummary]:
    for raw_path in sorted(glob.glob(str(export_dir / "event_*.json"))):
        yield summarize_event(Path(raw_path))


def format_elapsed(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.3f}s"


def compile_patterns(pattern_args: list[str]) -> list[tuple[str, re.Pattern[str]]]:
    compiled = []
    for pattern_arg in pattern_args:
        if "::" not in pattern_arg:
            raise SystemExit(
                f"invalid pattern {pattern_arg!r}; expected LABEL::REGEX"
            )
        label, regex = pattern_arg.split("::", 1)
        compiled.append((label, re.compile(regex, re.IGNORECASE | re.MULTILINE)))
    return compiled


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze an exported OpenHands conversation directory."
    )
    parser.add_argument("export_dir", type=Path, help="Path to exported conversation dir")
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Milestone matcher in LABEL::REGEX form. First matching event is reported.",
    )
    parser.add_argument(
        "--show-events",
        action="store_true",
        help="Print a compact timeline of all events.",
    )
    args = parser.parse_args()

    if not args.export_dir.is_dir():
        print(f"export dir not found: {args.export_dir}", file=sys.stderr)
        return 1

    events = list(iter_events(args.export_dir))
    if not events:
        print(f"no event_*.json files found in {args.export_dir}", file=sys.stderr)
        return 1

    first_user = next((event for event in events if event.source == "user"), events[0])
    last_event = events[-1]
    patterns = compile_patterns(args.pattern)

    print(f"Export: {args.export_dir}")
    print(f"Start:  {first_user.timestamp.isoformat()}")
    print(f"End:    {last_event.timestamp.isoformat()}")
    print(
        f"Span:   {format_elapsed((last_event.timestamp - first_user.timestamp).total_seconds())}"
    )

    if patterns:
        print("\nMilestones")
        print("----------")
        for label, pattern in patterns:
            match_event = next(
                (event for event in events if pattern.search(event.text)),
                None,
            )
            if match_event is None:
                print(f"{label}: not found")
                continue
            elapsed = (match_event.timestamp - first_user.timestamp).total_seconds()
            preview = " ".join(match_event.text.split())[:140]
            print(f"{label}: {format_elapsed(elapsed)}")
            print(f"  {match_event.source} {match_event.kind}")
            print(f"  {preview}")

    if args.show_events:
        print("\nTimeline")
        print("--------")
        for event in events:
            elapsed = (event.timestamp - first_user.timestamp).total_seconds()
            preview = " ".join(event.text.split())[:160]
            print(
                f"{format_elapsed(elapsed):>8}  {event.source:<12} {event.kind:<20} {preview}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
