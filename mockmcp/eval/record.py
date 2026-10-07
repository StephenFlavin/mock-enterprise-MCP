"""Recording hub: every tool call an Engine serves is appended to a JSONL file as one schema.TraceCall.

Enabled by `serve --record PATH` or env MOCKMCP_RECORD=PATH. rw comes from catalog/tools.csv (the source of truth),
falling back to the tool's own `writes` flag for tools the catalogue does not list."""
import csv
import json
import os
import threading
import time
from pathlib import Path

from ..spec import ROOT


class Recorder:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch()
        self.lock = threading.Lock()
        with open(ROOT / "catalog" / "tools.csv", newline="") as fh:
            self.rw = {(r["system"], r["tool"]): r["rw"] for r in csv.DictReader(fh)}

    @classmethod
    def make(cls, path=None):
        path = path or os.environ.get("MOCKMCP_RECORD")
        return cls(path) if path else None

    def add(self, sid: str, tool: str, args: dict, text: str, is_error: bool, ts: float, writes: bool = False):
        rec = {"ts": ts, "server": sid, "tool": tool, "args": args or {},
               "rw": self.rw.get((sid, tool)) or ("W" if writes else "R"), "is_error": is_error, "result": text}
        line = json.dumps(rec, default=str) + "\n"
        with self.lock, open(self.path, "a") as fh:
            fh.write(line)
