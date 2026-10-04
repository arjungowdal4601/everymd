"""Write a conversion into a hidden staging folder and swap it into place only when it is complete.

A conversion can run for an hour and spend money, so it must never leave a half-written folder behind:
the previous result stays untouched until the new one is finished. If the conversion fails, the staging
folder is kept as `.name.failed/` with a report.json that says what went wrong and what was spent. A run
that was killed (out of memory, SIGKILL) can't do that itself; the next run of the same name finds its
staging folder by its released lock and keeps it as `.name.failed/` the same way.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
from pathlib import Path
from typing import Callable

from . import report as report_file

try:
    import fcntl
except ImportError:  # Windows: no stale-run detection, everything else works
    fcntl = None

LOCK = ".lock"


class Stage:
    """A staging folder next to the final output folder (same filesystem, so the swap is a rename)."""

    def __init__(self, output_dir: Path, name: str, *, owns: Callable[[Path], bool], fallback: str):
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir, self.final, self.fallback, self.owns = output_dir, output_dir / name, fallback, owns
        while True:  # a plain mkdir keeps the usual permissions (mkdtemp would make it private, 0700)
            candidate = output_dir / f".{name}.partial-{secrets.token_hex(4)}"
            try:
                candidate.mkdir()
                break
            except FileExistsError:
                continue
        self.dir = candidate
        self._lock = None
        if fcntl is not None:
            self._lock = open(self.dir / LOCK, "w")
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self._keep_killed_runs(name)

    def path(self, filename: str) -> Path:
        return self.dir / filename

    def final_path(self, path: Path) -> Path:
        """Where a file written in the staging folder is once published."""
        return self.final / path.relative_to(self.dir)

    def progress(self, report: dict) -> None:
        """Keep a running report.json in the staging folder, so even a killed run shows its spend."""
        report_file.write(self.dir / "report.json", report)

    def publish(self) -> Path:
        """Swap the finished staging folder into place, then delete this input's previous result.
        A folder that turned out not to be this input's (another run took the name meanwhile, or it is
        not everymd's) is never touched: the result goes to the fallback name instead."""
        if self.final.exists() and not self.owns(self.final):
            self.final = self.output_dir / self.fallback
            if self.final.exists() and not self.owns(self.final):
                raise FileExistsError(f"'{self.final}' exists and is not this input's output.")
        self._release()
        previous = None
        if self.final.exists():
            previous = self.output_dir / f".{self.final.name}.old-{os.getpid()}"
            shutil.rmtree(previous, ignore_errors=True)
            os.replace(self.final, previous)
        try:
            os.replace(self.dir, self.final)
        except BaseException:
            if previous is not None:
                os.replace(previous, self.final)
            raise
        if previous is not None:
            shutil.rmtree(previous, ignore_errors=True)
        return self.final

    def fail(self, report: dict) -> Path:
        """Keep the staging folder as `.name.failed/` with a report of the failure; the previous result
        is untouched."""
        try:
            report_file.write(self.dir / "report.json", report)
        except OSError:
            pass
        self._release()
        return self._keep_as_failed(self.dir, self.final.name)

    def _release(self) -> None:
        if self._lock is not None:
            self._lock.close()
            (self.dir / LOCK).unlink(missing_ok=True)
            self._lock = None

    def _keep_as_failed(self, folder: Path, name: str) -> Path:
        failed = self.output_dir / f".{name}.failed"
        try:
            shutil.rmtree(failed, ignore_errors=True)
            os.replace(folder, failed)
        except OSError:
            return folder
        return failed

    def _keep_killed_runs(self, name: str) -> None:
        """Staging folders whose lock is free belong to runs that died without cleaning up."""
        if fcntl is None:
            return
        for folder in sorted(self.output_dir.glob(f".{name}.partial-*"), key=lambda p: p.stat().st_mtime):
            if folder == self.dir or not (folder / LOCK).exists():
                continue
            with open(folder / LOCK) as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    continue  # still running in another process
            _mark_killed(folder / "report.json")
            (folder / LOCK).unlink(missing_ok=True)
            self._keep_as_failed(folder, name)


def _mark_killed(path: Path) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data["status"] = "killed"
    data["error"] = "The process stopped without finishing (for example out of memory)."
    try:
        report_file.write(path, data)
    except OSError:
        pass
