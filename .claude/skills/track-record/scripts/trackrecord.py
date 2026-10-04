#!/usr/bin/env python3
"""Track Record helper CLI.

A helper, not a format police. It does mechanical work that an agent should
not spend tokens on (create starters, search by date, move material into the
archive, mirror the skill) and reports observations. It never rejects a record
for its shape. Exit code 1 means likely secrets or broken links, nothing else.

Python 3.9+ standard library only. No network access. Works with or without git.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

RECORD_DIR = ".trackrecord"
SKILL_NAME = "track-record"
LEGACY_DIR = "railway-track"
FALLBACK_VERSION = "1.0.0"
# Claude Code replaces hook output over 10,000 characters with a file path and
# a preview, so session-start output stays just under that platform cap.
HOOK_OUTPUT_BUDGET = 9500
CORE_FILES = ("STATE.md", "vision.md", "architecture.md", "change.md", "IMPACT.md")
CORE_DIRS = ("decisions", "work", "work/done", "archive")
IGNORED_NAMES = {".DS_Store", "__pycache__"}

EXAMPLES_HINT = "examples: .agents/skills/track-record/examples.md"
STARTERS = {
    "STATE.md": (
        "<!-- STATE.md: \"you are here\". What the project is, what's in progress and where it "
        "stopped, the next steps, the decisions that matter now, the last few changes. "
        f"Read first; keep it current and quick to read. {EXAMPLES_HINT} -->\n\n# State\n"
    ),
    "vision.md": (
        "<!-- vision.md: why the project exists, who it's for, and the rules the owner cares "
        "about. Rules change only with the owner's approval; point each to its decision. "
        f"{EXAMPLES_HINT} -->\n\n# Vision\n"
    ),
    "architecture.md": (
        "<!-- architecture.md: how it's built or organized. Invariants, boundaries, "
        "non-obvious flows and gotchas; only what the files themselves can't tell. "
        f"{EXAMPLES_HINT} -->\n\n# Architecture\n"
    ),
    "change.md": (
        "<!-- change.md: one line per meaningful change, starting with its date (YYYY-MM-DD) "
        "and linking to the work item or decision behind it. Search it; don't read it whole. "
        f"{EXAMPLES_HINT} -->\n\n# Changes\n"
    ),
    "IMPACT.md": (
        "<!-- IMPACT.md: one honest line each time these records helped (a guard catch, a "
        "smooth handover, a \"why\" answered) or failed to help (MISS). Name the agent; never "
        f"inflate. {EXAMPLES_HINT} -->\n\n# Impact\n"
    ),
}

DATE_LINE = re.compile(r"^\s*(?:[-*+]\s+)?(?:\[[ xX]\]\s+)?(\d{4}-\d{2}-\d{2})(?!\d)")
ANY_DATE = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)")
LINK = re.compile(r"\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^)\s]+)(?:\s+\"[^\"\n]*\")?\s*\)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
INLINE_CODE = re.compile(r"(`+)(.+?)\1")
FENCE = re.compile(r"^\s*(```|~~~)")

SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[0-9A-Z]{16}(?![A-Z0-9])")),
    ("GitHub token", re.compile(r"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{30,}")),
    ("GitHub token", re.compile(r"(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{30,}")),
    ("API key", re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}")),
    ("Slack token", re.compile(r"(?<![A-Za-z0-9_])xox[abposr]-[A-Za-z0-9-]{10,}")),
    ("Stripe key", re.compile(r"(?<![A-Za-z0-9_])[rs]k_live_[A-Za-z0-9]{16,}")),
    ("Google API key", re.compile(r"(?<![A-Za-z0-9_])AIza[0-9A-Za-z_-]{35}")),
    ("GitLab token", re.compile(r"(?<![A-Za-z0-9_])glpat-[A-Za-z0-9_-]{20,}")),
    ("JSON web token", re.compile(
        r"(?<![A-Za-z0-9_])eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("assigned secret", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"][^'\"\s]{12,}['\"]")),
]
APPROVAL_WORD = re.compile(r"(?i)\b(approved|approval|accepted)\b")
NOT_APPROVED = re.compile(
    r"(?i)(?:\b(?:not|never|no|pending|awaiting|needs?|without|until|unless|if)\b\W+(?:\w+\W+){0,2}"
    r"(?:approved|approval|accepted)\b|\b(?:approval|approved)\b\W+(?:\w+\W+){0,1}"
    r"(?:pending|awaiting|none|not|needed|required|tbd)\b|\bunapproved\b|\bpropos(?:al|ed)\b)")
QUOTED = re.compile(r"\"[^\"\n]{3,}\"|“[^”\n]{3,}”|^\s*>\s*\S", re.M)
EMAIL = re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
PLACEHOLDER_EMAIL = re.compile(r"(?i)@(?:example\.(?:com|org|net)|users\.noreply\.github\.com|"
                               r"noreply\.[a-z.]+|localhost)\b|^(?:noreply|no-reply)@")


# ---------------------------------------------------------------- utilities

def say(text: str = "") -> None:
    print(text)


def fail(message: str) -> None:
    """Usage problems exit 2; exit 1 is reserved for likely secrets or broken links."""
    sys.stderr.write(message + "\n")
    raise SystemExit(2)


def rel(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    """Write via a temp file in the same folder so a crash never leaves half a record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        mode = path.stat().st_mode & 0o777
    else:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tr-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def walk_files(base: Path) -> List[Path]:
    if not base.is_dir():
        return []
    found = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_NAMES)
        for name in sorted(filenames):
            if name in IGNORED_NAMES or name.endswith(".pyc") or name.startswith(".tr-"):
                continue
            found.append(Path(dirpath) / name)
    return found


def is_text(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return b"\0" not in handle.read(4096)
    except OSError:
        return False


def count(path: Path) -> Tuple[int, int]:
    text = read_text(path)
    return len(text.splitlines()), len(text.split())


def parse_date(value: str) -> dt.date:
    value = value.strip().lower()
    today = dt.date.today()
    if value == "today":
        return today
    if value == "yesterday":
        return today - dt.timedelta(days=1)
    match = re.fullmatch(r"(\d+)([dw])", value)
    if match:
        days = int(match.group(1)) * (7 if match.group(2) == "w" else 1)
        return today - dt.timedelta(days=days)
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        fail(f"Can't read date {value!r}; use YYYY-MM-DD, today, yesterday, 7d or 2w.")
        raise AssertionError("unreachable")


def to_date(text: str) -> Optional[dt.date]:
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def git(root: Path, *args: str) -> Optional[str]:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


# ------------------------------------------------------------ finding roots

def script_root() -> Optional[Path]:
    """Project root when this script runs from an installed skill copy."""
    here = Path(__file__).resolve()
    parents = here.parents
    if len(parents) > 4 and parents[2].name == "skills" and parents[3].name in (".agents", ".claude"):
        return parents[4]
    return None


def nearest_records(start: Path) -> Optional[Path]:
    """The closest folder at or above start that holds .trackrecord/."""
    start = start.expanduser().resolve()
    for folder in (start, *start.parents):
        if (folder / RECORD_DIR).is_dir():
            return folder
    return None


def find_root(explicit: Optional[str] = None, start: Optional[Path] = None,
              fallback: bool = True, hook: bool = False) -> Optional[Path]:
    if explicit:
        return Path(explicit).expanduser().resolve()
    candidates = [Path(start)] if start is not None else []
    candidates.append(Path.cwd())
    if hook and os.environ.get("CLAUDE_PROJECT_DIR"):
        candidates.append(Path(os.environ["CLAUDE_PROJECT_DIR"]))
    for begin in candidates:
        found = nearest_records(begin)
        if found is not None:
            return found
    if not fallback:
        return None
    return script_root() or Path.cwd().resolve()


def require_records(root: Path) -> Path:
    records = root / RECORD_DIR
    if not records.is_dir():
        fail(f"No {RECORD_DIR}/ in {root}. Run `trackrecord.py init` first (or pass --root).")
    return records


# ----------------------------------------------------------------- links

def masked_lines(text: str):
    """Yield (index, original line, line with code masked); fenced blocks are skipped."""
    in_fence = None
    for index, line in enumerate(text.split("\n")):
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if in_fence is None:
                in_fence = marker
            elif marker == in_fence:
                in_fence = None
            continue
        if in_fence is not None:
            continue
        masked = INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line)
        yield index, line, masked


def local_target(raw: str) -> Optional[Tuple[str, str]]:
    """Split a link target into (path, suffix) when it points at a local file."""
    target = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
    if not target or target.startswith("#") or target.startswith("/") or SCHEME.match(target):
        return None
    cut = len(target)
    for mark in ("#", "?"):
        pos = target.find(mark)
        if pos != -1:
            cut = min(cut, pos)
    return target[:cut], target[cut:]


def find_links(text: str) -> List[Tuple[int, str, str]]:
    """Return (line number, raw target, decoded local path) for local links."""
    links = []
    for index, line, masked in masked_lines(text):
        for match in LINK.finditer(masked):
            raw = line[match.start(1):match.end(1)]
            parts = local_target(raw)
            if parts and parts[0]:
                links.append((index + 1, raw, unquote(parts[0])))
    return links


def broken_links(path: Path, records: Path) -> List[str]:
    problems = []
    for line_no, raw, target in find_links(read_text(path)):
        if not (path.parent / target).exists():
            problems.append(f"broken link in {rel(path, records)}:{line_no} -> {raw}")
    return problems


def encode_target(path_text: str, original: str, suffix: str = "") -> str:
    if original.startswith("<"):
        return f"<{path_text}{suffix}>"
    return quote(path_text, safe="/._-~") + suffix


def link_for(path_text: str) -> str:
    return quote(path_text, safe="/._-~")


def rewrite_links(text: str, old_dir: Path, new_dir: Path, moved: Dict[Path, Path]) -> str:
    """Keep local links pointing at the same files after a move.

    old_dir is where the text lived, new_dir is where it will live, and moved maps
    old absolute file paths to new ones. Links that were already broken are left alone.
    """
    lines = text.split("\n")
    for index, line, masked in list(masked_lines(text)):
        pieces = []
        last = 0
        for match in LINK.finditer(masked):
            start, end = match.start(1), match.end(1)
            raw = line[start:end]
            parts = local_target(raw)
            if not parts or not parts[0]:
                continue
            path_part, suffix = parts
            old_target = Path(os.path.normpath(old_dir / unquote(path_part)))
            new_target = moved.get(old_target, old_target)
            if old_target not in moved and not old_target.exists():
                continue
            if new_target == old_target and old_dir == new_dir:
                continue
            new_rel = Path(os.path.relpath(new_target, new_dir)).as_posix()
            if new_rel == unquote(path_part):
                continue
            pieces.append(line[last:start])
            pieces.append(encode_target(new_rel, raw, suffix))
            last = end
        if pieces:
            pieces.append(line[last:])
            lines[index] = "".join(pieces)
    return "\n".join(lines)


# ---------------------------------------------------------------- checking

def secret_findings(records: Path) -> List[str]:
    findings = []
    for path in walk_files(records):
        try:
            if path.stat().st_size > 5_000_000 or not is_text(path):
                continue
        except OSError:
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), 1):
            for label, pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if match:
                    shown = match.group(0)[:4] + "..."
                    findings.append(f"likely secret ({label}) in {rel(path, records)}:{line_no}: {shown}")
                    break
    return findings


def undated_change_lines(change: Path) -> List[str]:
    notes = []
    in_comment = False
    for index, line, _ in masked_lines(read_text(change)):
        stripped = line.strip()
        if in_comment:
            in_comment = "-->" not in stripped
            continue
        if stripped.startswith("<!--"):
            in_comment = "-->" not in stripped
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if not DATE_LINE.match(line):
            notes.append(f"change.md:{index + 1} doesn't start with a date (YYYY-MM-DD): "
                         f"{stripped[:70]}")
    return notes


def approval_warnings(records: Path) -> List[str]:
    notes = []
    for path in walk_files(records / "decisions"):
        if path.suffix.lower() != ".md":
            continue
        lines = read_text(path).splitlines()
        for index, line in enumerate(lines):
            if not APPROVAL_WORD.search(line) or NOT_APPROVED.search(line):
                continue
            paragraph = [line]
            for following in lines[index + 1:index + 4]:
                if not following.strip():
                    break
                paragraph.append(following)
            nearby = "\n".join(paragraph)
            if not QUOTED.search(nearby):
                notes.append(f"{rel(path, records)}:{index + 1} reads as approved but quotes no "
                             "owner words there; without them it is a proposal")
                break
    return notes


def personal_data_notes(records: Path) -> List[str]:
    notes = []
    for path in walk_files(records):
        if not is_text(path):
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), 1):
            found = [m for m in EMAIL.findall(line) if not PLACEHOLDER_EMAIL.search(m)]
            if found:
                notes.append(f"possible personal data (email address) in {rel(path, records)}:"
                             f"{line_no}; records shouldn't hold personal data")
                break
    return notes


def other_link_notes(records: Path) -> List[str]:
    """Broken links outside change.md and STATE.md are worth knowing, not worth failing on."""
    paths = [records / "vision.md", records / "architecture.md"]
    paths += walk_files(records / "decisions") + walk_files(records / "work")
    notes = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".md":
            notes.extend(broken_links(path, records))
    return notes


def skill_drift(root: Path) -> List[str]:
    agents = root / ".agents" / "skills" / SKILL_NAME
    claude = root / ".claude" / "skills" / SKILL_NAME
    if not (agents.is_dir() and claude.is_dir()):
        return []
    left = {rel(p, agents): p for p in walk_files(agents)}
    right = {rel(p, claude): p for p in walk_files(claude)}
    differing = sorted(name for name in set(left) | set(right)
                       if name not in left or name not in right
                       or left[name].read_bytes() != right[name].read_bytes())
    if not differing:
        return []
    shown = ", ".join(differing[:6]) + (" ..." if len(differing) > 6 else "")
    return [f".claude/skills/{SKILL_NAME} differs from .agents/skills/{SKILL_NAME} "
            f"({shown}); run `trackrecord.py install-sync`"]


def size_rows(records: Path) -> List[Tuple[str, str]]:
    rows = []
    for name in CORE_FILES:
        path = records / name
        if path.is_file():
            lines, words = count(path)
            rows.append((name, f"{lines} lines, {words} words"))
    for folder in ("decisions", "work", "work/done", "archive"):
        base = records / folder
        if not base.is_dir():
            continue
        if folder == "work":
            files = [p for p in walk_files(base) if "done" not in p.relative_to(base).parts[:1]]
        else:
            files = walk_files(base)
        text_files = [p for p in files if is_text(p)]
        words = sum(count(p)[1] for p in text_files)
        rows.append((folder + "/", f"{len(files)} files, {words} words"))
    for path in sorted(records.iterdir()):
        if path.is_file() and path.name not in CORE_FILES and path.name not in IGNORED_NAMES:
            lines, words = count(path) if is_text(path) else (0, 0)
            rows.append((path.name, f"{lines} lines, {words} words"))
    return rows


def size_line(records: Path) -> str:
    return " | ".join(f"{name} {value}" for name, value in size_rows(records)
                      if not value.startswith("0 files"))


def run_checks(root: Path) -> Dict[str, List[str]]:
    records = root / RECORD_DIR
    problems: List[str] = []
    notes: List[str] = []
    link_files = [records / "change.md", records / "STATE.md"]
    link_files += [p for p in walk_files(records / "archive") if p.name == "SUMMARY.md"]
    for path in link_files:
        if path.is_file():
            problems.extend(broken_links(path, records))
    problems.extend(secret_findings(records))
    if (records / "change.md").is_file():
        notes.extend(undated_change_lines(records / "change.md"))
    notes.extend(other_link_notes(records))
    notes.extend(approval_warnings(records))
    notes.extend(personal_data_notes(records))
    notes.extend(skill_drift(root))
    if (root / LEGACY_DIR).is_dir():
        notes.append(f"legacy layout found at {LEGACY_DIR}/; run `trackrecord.py migrate-legacy`")
    for name in CORE_FILES:
        if not (records / name).is_file():
            notes.append(f"{name} doesn't exist yet")
    return {"problems": problems, "notes": notes}


# ---------------------------------------------------------------- commands

def create_starters(records: Path, dry_run: bool = False) -> Tuple[List[str], List[str]]:
    created, kept = [], []
    for folder in CORE_DIRS:
        path = records / folder
        if path.is_dir():
            kept.append(folder + "/")
        else:
            created.append(folder + "/")
            if not dry_run:
                path.mkdir(parents=True, exist_ok=True)
    for name, text in STARTERS.items():
        path = records / name
        if path.exists():
            kept.append(name)
        else:
            created.append(name)
            if not dry_run:
                write_text(path, text)
    return created, kept


def cmd_init(args) -> int:
    if args.root:
        root = Path(args.root).expanduser().resolve()
    else:
        root = Path.cwd().resolve()
        above = nearest_records(root)
        if above is not None and above != root:
            say(f"A Track Record already exists at {above / RECORD_DIR}.")
            say("Run commands from there, or pass --root . to start a separate one here.")
            return 1
    records = root / RECORD_DIR
    created, kept = create_starters(records)
    say(f"Track Record at {records}")
    if created:
        say("Created: " + ", ".join(created))
    if kept:
        say("Already there (left untouched): " + ", ".join(kept))
    if (root / LEGACY_DIR).is_dir():
        say(f"Found a legacy {LEGACY_DIR}/ folder. Run `trackrecord.py migrate-legacy` "
            "to archive it and follow its checklist.")
    say("Next: draft vision.md and STATE.md with the owner (purpose, audience, rules that "
        "need approval). Good examples are in the skill's examples.md.")
    return 0


def cmd_since(args) -> int:
    root = find_root(args.root)
    records = require_records(root)
    start = parse_date(args.date)
    until = parse_date(args.until) if args.until else None
    topic = args.topic.lower() if args.topic else None
    entries: List[Tuple[dt.date, int, str, str]] = []
    order = 0

    sources = []
    for name in ("change.md", "IMPACT.md"):
        if (records / name).is_file():
            sources.append(records / name)
    for path in walk_files(records / "archive"):
        lower = path.name.lower()
        if lower.endswith(".md") and (lower.startswith("change") or lower.startswith("impact")):
            sources.append(path)

    linked = set()

    def keep(day: dt.date) -> bool:
        return day >= start and (until is None or day <= until)

    for path in sources:
        for line in read_text(path).splitlines():
            match = DATE_LINE.match(line)
            if not match:
                continue
            day = to_date(match.group(1))
            if day is None or not keep(day):
                continue
            if topic and topic not in line.lower():
                continue
            text = line[match.end():].strip(" -:–—\t")
            order += 1
            entries.append((day, order, rel(path, records), text))
            for _, _, target in find_links(line):
                linked.add(os.path.normpath(path.parent / target))

    for path in walk_files(records / "decisions"):
        if path.suffix.lower() != ".md":
            continue
        text = read_text(path)
        if topic and topic not in text.lower():
            continue
        if os.path.normpath(path) in linked:
            continue
        days = [d for d in (to_date(m) for m in ANY_DATE.findall(text)) if d and keep(d)]
        if not days:
            continue
        title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("#")),
                     path.stem)
        order += 1
        entries.append((days[0], order, rel(path, records), title))

    entries.sort(key=lambda item: (item[0], item[1]))
    if not entries:
        span = f"since {start}" + (f" until {until}" if until else "")
        say(f"Nothing recorded {span}" + (f" about {args.topic!r}." if topic else "."))
        return 0
    for day, _, source, text in entries:
        say(f"{day}  {source}  {text}")
    return 0


def cmd_check(args) -> int:
    root = find_root(args.root)
    records = require_records(root)
    result = run_checks(root)
    say(f"Track Record check: {records}")
    if result["problems"]:
        say("\nProblems (fix these):")
        for line in result["problems"]:
            say(f"  - {line}")
    if result["notes"]:
        say("\nNotes:")
        for line in result["notes"]:
            say(f"  - {line}")
    say("\nSizes (for your own judgment about compacting):")
    for name, value in size_rows(records):
        say(f"  {name:<16} {value}")
    say("\n" + ("No likely secrets or broken links." if not result["problems"]
               else f"{len(result['problems'])} problem(s) found."))
    return 1 if result["problems"] else 0


def resolve_archive_label(records: Path, to: str) -> Path:
    raw = Path(to)
    if raw.is_absolute():
        target = raw.resolve()
    else:
        parts = raw.parts
        if parts and parts[0] == RECORD_DIR:
            raw = Path(*parts[1:]) if len(parts) > 1 else Path()
        target = (records / raw).resolve()
    archive = (records / "archive").resolve()
    if target == archive or archive not in target.parents:
        fail("--to must be a folder inside archive/, for example archive/2026-09")
    return target


def resolve_move_path(records: Path, arg: str) -> Path:
    """Accept paths relative to the current folder or to .trackrecord/."""
    raw = Path(arg).expanduser()
    candidates = [raw] if raw.is_absolute() else [Path.cwd().resolve() / raw, records / raw]
    candidates = [Path(os.path.normpath(c)) for c in candidates]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    for candidate in candidates:
        if records in candidate.parents:
            return candidate
    return candidates[0]


def bullet_style(lines: List[str]) -> str:
    """Match how existing change lines are written: '- 2026-...' or bare '2026-...'."""
    dated = [line for line in lines if DATE_LINE.match(line)]
    bare = sum(1 for line in dated if line.lstrip()[:1].isdigit())
    return "" if dated and bare > len(dated) - bare else "- "


def summary_stub(label: str) -> str:
    label = label[len("archive/"):] if label.startswith("archive/") else label
    return (f"# Archive: {label}\n\n"
            "<!-- Summary: in a few lines, say what was moved here, why the next agent "
            "won't need it day to day, and anything from it that still matters. -->\n\n"
            "## Moved here\n")


def cmd_compact_move(args) -> int:
    root = find_root(args.root)
    records = require_records(root).resolve()
    dest = resolve_archive_label(records, args.to)
    label = rel(dest, records)
    moved: Dict[Path, Path] = {}
    skipped: List[str] = []
    already: List[str] = []

    protected = {(records / name).resolve() for name in CORE_FILES}
    for arg in args.paths:
        path = resolve_move_path(records, arg)
        if records not in path.parents:
            skipped.append(f"{arg}: not inside {RECORD_DIR}/ (or is the whole folder)")
            continue
        inner = path.relative_to(records)
        if inner.parts[0] == "archive":
            skipped.append(f"{arg}: already in archive/")
            continue
        if inner.parts[0] == "decisions":
            skipped.append(f"{arg}: decisions stay in decisions/ (supersede them instead)")
            continue
        if path in protected:
            skipped.append(f"{arg}: {inner.as_posix()} stays in place; compact it by editing, "
                           "and use --change-before for change.md lines")
            continue
        if not path.exists():
            if (dest / inner).exists():
                already.append(inner.as_posix())
            else:
                skipped.append(f"{arg}: not found")
            continue
        files = walk_files(path) if path.is_dir() else [path]
        for source in files:
            target = dest / source.relative_to(records)
            if target.exists():
                if target.read_bytes() == source.read_bytes():
                    already.append(rel(source, records) + " (identical copy already archived)")
                else:
                    skipped.append(f"{rel(source, records)}: {rel(target, records)} exists "
                                   "with different content; not overwriting")
                continue
            moved[source] = target

    change = records / "change.md"
    change_text = read_text(change) if change.is_file() else ""
    archived_change = dest / "change.md"
    archived_text = read_text(archived_change) if archived_change.is_file() else ""
    moving_lines: List[str] = []
    remaining_lines: List[str] = change_text.split("\n") if change_text else []
    if args.change_before:
        cutoff = parse_date(args.change_before)
        existing = set(archived_text.split("\n"))
        remaining_lines = []
        for line in change_text.split("\n"):
            match = DATE_LINE.match(line)
            day = to_date(match.group(1)) if match else None
            if day is not None and day < cutoff:
                rebased = rewrite_links(line, records, archived_change.parent, moved)
                if rebased not in existing and line not in existing:
                    moving_lines.append(rebased)
                continue
            remaining_lines.append(line)

    summary = dest / "SUMMARY.md"
    summary_text = read_text(summary) if summary.is_file() else summary_stub(label)
    linked = {target for _, _, target in find_links(summary_text)}
    new_links: List[str] = []
    for target in sorted(moved.values()):
        link = rel(target, dest)
        if link not in linked:
            new_links.append(f"- [{link}]({link_for(link)})")
            linked.add(link)
    if moving_lines and "change.md" not in linked:
        new_links.append(f"- [change.md](change.md): change lines before {args.change_before}")
        linked.add("change.md")
    if args.summary_stub and dest.is_dir():
        for path in walk_files(dest):
            link = rel(path, dest)
            if link != "SUMMARY.md" and link not in linked and path not in moved.values():
                new_links.append(f"- [{link}]({link_for(link)})")
                linked.add(link)

    changed_lines = len(change_text.split("\n")) - len(remaining_lines) if change_text else 0
    nothing = not moved and not moving_lines and not new_links and changed_lines == 0
    verb = "Would move" if args.dry_run else "Moved"
    for source, target in moved.items():
        say(f"{verb} {rel(source, records)} -> {rel(target, records)}")
    if changed_lines:
        say(f"{verb} {changed_lines} change.md line(s) dated before {args.change_before} "
            f"-> {rel(archived_change, records)}")
    for line in new_links:
        say(("Would link" if args.dry_run else "Linking") + f" in {rel(summary, records)}: {line[2:]}")
    for line in already:
        say(f"Already archived: {line}")
    for line in skipped:
        say(f"Skipped {line}")
    if nothing:
        say("Nothing to move; nothing changed.")
        return 0

    compact_line = None
    if moved or changed_lines or new_links:
        what = []
        if moved:
            what.append(f"{len(moved)} file(s)")
        if changed_lines:
            what.append(f"{changed_lines} change line(s)")
        description = args.note or ("Moved " + " and ".join(what or ["notes"]) + f" to {label}/")
        summary_link = link_for(rel(summary, records))
        bullet = bullet_style(change_text.split("\n"))
        compact_line = (f"{bullet}{dt.date.today().isoformat()} [COMPACT] {description.rstrip('.')} "
                        f"([summary]({summary_link}))")
        say(("Would append" if args.dry_run else "Appended") + f" to change.md: {compact_line}")
    if args.dry_run:
        say("Dry run: nothing was changed.")
        return 0

    # Write everything new first, then update links, then remove the moved originals.
    for source, target in moved.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() == ".md" and is_text(source):
            write_text(target, rewrite_links(read_text(source), source.parent, target.parent, moved))
            shutil.copystat(source, target)
        else:
            shutil.copy2(source, target)
    if moving_lines:
        base = archived_text if archived_text else f"# Changes archived in {label}\n"
        write_text(archived_change, base.rstrip("\n") + "\n" + "\n".join(moving_lines) + "\n")
    if new_links:
        write_text(summary, summary_text.rstrip("\n") + "\n" + "\n".join(new_links) + "\n")

    decision_notes = []
    for path in walk_files(records):
        if path.suffix.lower() != ".md" or path in moved or path == change or not is_text(path):
            continue
        if dest in path.parents and path.name in ("SUMMARY.md", "change.md"):
            continue
        text = read_text(path)
        updated = rewrite_links(text, path.parent, path.parent, moved)
        if updated == text:
            continue
        if (records / "decisions") in path.parents:
            decision_notes.append(rel(path, records))
            continue
        write_text(path, updated)
    if change.is_file() or compact_line:
        new_change = rewrite_links("\n".join(remaining_lines), records, records, moved)
        if not new_change.strip():
            new_change = STARTERS["change.md"]
        if compact_line:
            new_change = new_change.rstrip("\n") + "\n" + compact_line + "\n"
        write_text(change, new_change)
    for source in moved:
        source.unlink()
    for source in moved:
        folder = source.parent
        while folder != records and rel(folder, records) not in CORE_DIRS:
            try:
                folder.rmdir()
            except OSError:
                break
            folder = folder.parent
    for name in decision_notes:
        say(f"Note: {name} links to a moved file; decisions aren't rewritten, so that link "
            "now points at the old path (the file is listed in the archive summary).")
    say(f"Done. Fill in the summary at {rel(summary, records)}.")
    return 0


def legacy_leftovers(root: Path) -> List[str]:
    leftovers = []
    for skill_dir in (".agents/skills/railway-track", ".claude/skills/railway-track"):
        if (root / skill_dir).exists():
            leftovers.append(f"{skill_dir}/ (old skill folder)")
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = root / name
        if path.is_file():
            hits = [str(i) for i, line in enumerate(read_text(path).splitlines(), 1)
                    if "railway-track" in line.lower() or "railway track" in line.lower()]
            if hits:
                leftovers.append(f"{name} lines {', '.join(hits)} mention the legacy layout")
    return leftovers


def cmd_migrate_legacy(args) -> int:
    root = find_root(args.root)
    legacy = root / LEGACY_DIR
    records = root / RECORD_DIR
    dest = records / "archive" / "legacy"
    if not legacy.is_dir():
        if dest.is_dir():
            say(f"Already migrated: legacy records are in {rel(dest, root)}/. Nothing changed.")
        else:
            say(f"No legacy {LEGACY_DIR}/ folder in {root}. Nothing changed.")
        return 0

    plan: List[Tuple[Path, Path]] = []
    conflicts: List[str] = []
    duplicates: List[Path] = []
    for source in walk_files(legacy):
        target = dest / source.relative_to(legacy)
        if target.exists():
            if target.read_bytes() == source.read_bytes():
                duplicates.append(source)
            else:
                conflicts.append(rel(source, root))
            continue
        plan.append((source, target))

    verb = "Would move" if args.dry_run else "Moved"
    if not records.is_dir():
        say(("Would create" if args.dry_run else "Creating") + f" {RECORD_DIR}/ with starter files.")
    if not args.dry_run:
        create_starters(records)
    say(f"{verb} {len(plan)} legacy file(s) from {LEGACY_DIR}/ to {rel(dest, root)}/.")
    for item in conflicts:
        say(f"Left in place (a different file already exists in the archive): {item}")
    if not args.dry_run:
        for source, target in plan:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
        for source in duplicates:
            source.unlink()
        for folder in sorted((p for p in legacy.rglob("*") if p.is_dir()), reverse=True):
            try:
                folder.rmdir()
            except OSError:
                pass
        try:
            legacy.rmdir()
        except OSError:
            pass
        summary = dest / "SUMMARY.md"
        if not summary.exists():
            lines = ["# Archive: legacy records", "",
                     "<!-- Summary: in a few lines, say what these legacy records cover, what was "
                     "carried into the new records, and what is only here. -->", "",
                     "## Moved here"]
            for name in sorted(p.name for p in dest.iterdir() if p.name != "SUMMARY.md"):
                path = dest / name
                if path.is_dir():
                    lines.append(f"- [{name}/]({link_for(name)}/) "
                                 f"({len(walk_files(path))} files)")
                else:
                    lines.append(f"- [{name}]({link_for(name)})")
            write_text(summary, "\n".join(lines) + "\n")
    leftovers = legacy_leftovers(root)
    if args.dry_run:
        if leftovers:
            say("It would leave these for you to raise with the owner:")
            for item in leftovers:
                say(f"   - {item}")
        say("Dry run: nothing was changed.")
        return 0

    today = dt.date.today().isoformat()
    say("")
    say("Nothing was deleted. Next, as the agent:")
    say("1. Read archive/legacy/vision.md, architecture.md and change.md. Search the older "
        "files for what you need; don't bulk-read them.")
    say("2. Draft vision.md and architecture.md from them (purpose, audience, rules; only "
        "what the files themselves can't tell).")
    say("3. Draft decisions from the legacy records and show the owner the list before writing "
        "any. Where the owner's original words weren't recorded, say so in the decision; "
        "never invent a quote.")
    say("4. Create work/ items only for legacy work that is genuinely unfinished. Check git: "
        "old statuses often went stale after merges.")
    say("5. Write STATE.md.")
    say("6. Fill in archive/legacy/SUMMARY.md and add one change.md line, for example:")
    say(f"   - {today} [MIGRATED] Archived the legacy records in archive/legacy/ "
        "([summary](archive/legacy/SUMMARY.md))")
    if leftovers:
        say("Not touched (ask the owner before removing; archive old text rather than deleting it):")
        for item in leftovers:
            say(f"   - {item}")
        say("Until the owner answers, add one line at the top of any old AGENTS.md section saying "
            f"it is superseded by the Track Record section, so no agent writes to {LEGACY_DIR}/ again.")
    return 0


def cmd_install_sync(args) -> int:
    root = find_root(args.root)
    source = root / ".agents" / "skills" / SKILL_NAME
    target = root / ".claude" / "skills" / SKILL_NAME
    if not (source / "SKILL.md").is_file():
        say(f"No skill at {rel(source, root)}/SKILL.md; install it there first.")
        return 1
    actions: List[str] = []
    if target.is_symlink():
        actions.append(f"replace symlink {rel(target, root)} with a copy")
        if not args.dry_run:
            target.unlink()
    wanted = {rel(p, source): p for p in walk_files(source)}
    present = {rel(p, target): p for p in walk_files(target)} if target.is_dir() else {}
    for name, path in wanted.items():
        mirror = target / name
        if name not in present:
            actions.append(f"add {name}")
        elif present[name].read_bytes() != path.read_bytes():
            actions.append(f"update {name}")
        else:
            continue
        if not args.dry_run:
            mirror.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, mirror)
    for name, path in present.items():
        if name not in wanted:
            actions.append(f"remove {name} (not in the canonical copy)")
            if not args.dry_run:
                path.unlink()
    if not args.dry_run and target.is_dir():
        for folder in sorted((p for p in target.rglob("*") if p.is_dir()), reverse=True):
            try:
                folder.rmdir()
            except OSError:
                pass
    if not actions:
        say(f"{rel(target, root)} already matches {rel(source, root)}.")
        return 0
    prefix = "Would " if args.dry_run else ""
    for action in actions:
        say(prefix + action)
    say(("Dry run: nothing was changed." if args.dry_run
         else f"{rel(target, root)} now matches {rel(source, root)}."))
    return 0


def hook_session_start(args) -> int:
    root = find_root(args.root, fallback=False, hook=True)
    if root is None:
        say("Track Record: no .trackrecord/ for this folder.")
        return 0
    records = root / RECORD_DIR
    state = records / "STATE.md"
    sizes = "Track Record sizes: " + size_line(records)
    if not state.is_file():
        say("Track Record: .trackrecord/ exists but has no STATE.md yet. Write one after this "
            "session's work (see the track-record skill).")
        say(sizes)
        return 0
    header = ("Track Record: .trackrecord/STATE.md is below. Read it first and follow the "
              "track-record skill; search change.md and decisions/ for detail.\n")
    text = read_text(state).strip("\n")
    budget = HOOK_OUTPUT_BUDGET - len(header) - len(sizes) - 200
    if len(text) > budget:
        cut = text.rfind("\n", 0, budget)
        text = text[: cut if cut > 0 else budget] + (
            "\n\n[STATE.md continues; open it for the rest. It has grown long enough that "
            "compacting it may help.]")
    sys.stdout.write(f"{header}\n{text}\n\n{sizes}\n")
    return 0


def records_changed_without_state(root: Path) -> bool:
    records = root / RECORD_DIR
    ignored = git(root, "check-ignore", "-q", RECORD_DIR) is not None
    status = None if ignored else git(root, "status", "--porcelain", "--untracked-files=all",
                                      "--", RECORD_DIR)
    if status is not None:
        changed = [line[3:].strip().strip('"') for line in status.splitlines() if len(line) > 3]
        if not changed:
            return False
        return not any(path.endswith(f"{RECORD_DIR}/STATE.md") for path in changed)
    state = records / "STATE.md"
    if not state.is_file():
        return False
    recent = dt.datetime.now().timestamp() - 2 * 3600
    state_time = state.stat().st_mtime
    for path in walk_files(records):
        if path == state:
            continue
        mtime = path.stat().st_mtime
        if mtime > state_time and mtime > recent:
            return True
    return False


def hook_stop(args) -> int:
    try:
        raw = "" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except (ValueError, OSError):
        data = {}
    if data.get("stop_hook_active"):
        return 0
    try:
        start = Path(data["cwd"]) if isinstance(data.get("cwd"), str) else None
        root = find_root(args.root, start=start, fallback=False, hook=True)
        if root is None:
            return 0
        result = run_checks(root)
        if result["problems"]:
            sys.stderr.write("Track Record found problems in .trackrecord/ that need fixing "
                             "before you finish:\n")
            for line in result["problems"]:
                sys.stderr.write(f"  - {line}\n")
            sys.stderr.write("Remove any secret from the records (never store secrets there) "
                             "and fix or remove broken links. Run `trackrecord.py check` to confirm.\n")
            return 2
        if args.agent == "claude" and records_changed_without_state(root):
            sys.stdout.write(json.dumps({"systemMessage": (
                "Track Record: records changed but STATE.md didn't. Update it if where things "
                "stand has changed.")}) + "\n")
    except Exception:  # A broken helper must never trap an agent in its turn.
        return 0
    return 0


def cmd_hook(args) -> int:
    if args.event == "session-start":
        return hook_session_start(args)
    return hook_stop(args)


def skill_version() -> str:
    skill = Path(__file__).resolve().parent.parent / "SKILL.md"
    if skill.is_file():
        text = read_text(skill)
        if text.startswith("---"):
            front = text.split("---", 2)[1]
            match = re.search(r"^\s+version:\s*[\"']?([0-9][^\"'\s]*)", front, re.M)
            if match:
                return match.group(1)
    return FALLBACK_VERSION


def cmd_version(args) -> int:
    say(skill_version())
    return 0


# --------------------------------------------------------------------- main

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trackrecord.py",
        description="Track Record helper: mechanical work and observations for .trackrecord/. "
                    "It never rejects a record for its shape.")
    parser.add_argument("--root", help="project folder that holds .trackrecord/ "
                        "(default: the nearest one above the current folder)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create .trackrecord/ with brief starter files; never overwrites")

    since = sub.add_parser("since", help="what happened since a date, in date order")
    since.add_argument("date", help="YYYY-MM-DD, today, yesterday, 7d or 2w")
    since.add_argument("--topic", help="only entries mentioning this word (case-insensitive)")
    since.add_argument("--until", help="last date to include (YYYY-MM-DD)")

    sub.add_parser("check", help="report likely secrets, broken links and observations; "
                   "exit 1 only for secrets or broken links")

    compact = sub.add_parser("compact-move", help="move files or old change lines into the "
                             "archive; never deletes")
    compact.add_argument("paths", nargs="*", help="files or folders inside .trackrecord/ to move")
    compact.add_argument("--to", required=True, help="archive folder, for example archive/2026-09")
    compact.add_argument("--change-before", metavar="DATE",
                         help="also move change.md lines dated before DATE")
    compact.add_argument("--summary-stub", action="store_true",
                         help="also list in SUMMARY.md any files already in the archive folder "
                              "that it doesn't link yet (use after moving text by hand)")
    compact.add_argument("--note", help="wording for the COMPACT line in change.md")
    compact.add_argument("--dry-run", action="store_true", help="show the plan; change nothing")

    legacy = sub.add_parser("migrate-legacy", help=f"archive a legacy {LEGACY_DIR}/ folder and "
                            "print a checklist")
    legacy.add_argument("--dry-run", action="store_true", help="show the plan; change nothing")

    sync = sub.add_parser("install-sync", help="mirror .agents/skills/track-record into "
                          ".claude/skills/track-record exactly")
    sync.add_argument("--dry-run", action="store_true", help="show the plan; change nothing")

    hook = sub.add_parser("hook", help="entry points for agent hooks")
    hook.add_argument("event", choices=["session-start", "stop"])
    hook.add_argument("--agent", choices=["claude", "codex"], default="claude",
                      help="which agent runs the hook (Codex stop hooks must print nothing)")

    sub.add_parser("version", help="print the skill version")
    return parser


COMMANDS = {
    "init": cmd_init,
    "since": cmd_since,
    "check": cmd_check,
    "compact-move": cmd_compact_move,
    "migrate-legacy": cmd_migrate_legacy,
    "install-sync": cmd_install_sync,
    "hook": cmd_hook,
    "version": cmd_version,
}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
