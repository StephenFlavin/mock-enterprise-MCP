"""Bring-up / tear-down: without MOCKMCP_STATE every process gets a fresh write overlay that is removed on exit."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = "from mockmcp import db; print(db.STATE)"


def _state_dir(env):
    out = subprocess.run([sys.executable, "-c", PROBE], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    return Path(out.stdout.strip())


def test_default_state_is_fresh_and_removed():
    env = {k: v for k, v in os.environ.items() if k != "MOCKMCP_STATE"}
    a, b = _state_dir(env), _state_dir(env)
    assert a != b
    assert not a.exists() and not b.exists()


def test_mockmcp_state_persists(tmp_path):
    env = dict(os.environ, MOCKMCP_STATE=str(tmp_path / "s"))
    assert _state_dir(env) == tmp_path / "s"
