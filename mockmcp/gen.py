"""Data generation: run systems/<id>/gen.py, overlay seed/*.csv by key, write data/*.csv in spec column order."""
import csv
import importlib.util
import random
import re
import tempfile
import zlib
from datetime import date, timedelta
from functools import cache
from pathlib import Path

from faker import Faker

from .spec import SYSTEMS, WORLD, System, load_system

MAX_ROWS = 60000
WALL_CLOCK = re.compile(r"datetime\.now\(|date\.today\(|time\.time\(|fake\.(?:date_this_\w+|date_time_this_\w+|past_\w+|future_\w+|"
                        r"date_time_between\(\s*start_date\s*=\s*['\"]|date_between\(\s*start_date\s*=\s*['\"]|date_time\(|date_object\(|year\(|month\()")


class Gen:
    """Handed to generate(g). Seeded, so output is identical on every run."""

    def __init__(self, system_id: str):
        seed = WORLD["seed"] + zlib.crc32(system_id.encode())
        self.seed = seed
        self.rng = random.Random(seed)
        self.fake = Faker("en_GB")
        self.fake.seed_instance(seed)
        self.world = WORLD
        self.as_of = date.fromisoformat(WORLD["data_as_of"])

    def rng_for(self, *key) -> random.Random:
        """An independent stream per entity (e.g. g.rng_for("sku", sku)). Use it when looping over master rows,
        so adding rows to master data never shifts what other rows get."""
        return random.Random(f"{self.seed}:" + ":".join(map(str, key)))

    def days_ago(self, n: int) -> date:
        return self.as_of - timedelta(days=n)

    def date_between(self, start_days_ago: int, end_days_ago: int = 0) -> date:
        return self.as_of - timedelta(days=self.rng.randint(end_days_ago, start_days_ago))

    def weeks(self, n: int) -> list[date]:
        """Week-start Mondays for the last n weeks, oldest first."""
        monday = self.as_of - timedelta(days=self.as_of.weekday())
        return [monday - timedelta(weeks=i) for i in range(n, 0, -1)]

    def master(self, table: str) -> list[dict]:
        return read_rows(SYSTEMS / "_master" / "data" / f"{table}.csv")

    def pick(self, seq, k: int | None = None):
        return self.rng.choice(seq) if k is None else self.rng.sample(seq, k)


@cache
def _read(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def read_rows(path) -> list[dict]:
    return [dict(r) for r in _read(str(path))] if path.exists() else []


def generate(system_id: str, out_dir=None) -> dict[str, int]:
    """Write data/*.csv (or into out_dir) from gen.py + seed/*.csv."""
    s: System = load_system(system_id)
    out: dict[str, list[dict]] = {}
    g = s.dir / "gen.py"
    if g.exists():
        spec = importlib.util.spec_from_file_location(f"gen_{system_id}", g)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = mod.generate(Gen(system_id)) or {}
    unknown = set(out) - set(s.tables)
    if unknown:
        raise ValueError(f"gen.py returned tables not in system.yaml: {sorted(unknown)}")
    counts = {}
    for name, t in s.tables.items():
        rows = [dict(r) for r in out.get(name, [])]
        for r in rows:
            extra = set(r) - set(t.cols)
            if extra:
                raise ValueError(f"{name}: generated columns not in system.yaml: {sorted(extra)}")
        seed = read_rows(s.dir / "seed" / f"{name}.csv")
        if seed:
            extra = set(seed[0]) - set(t.cols)
            if extra:
                raise ValueError(f"seed/{name}.csv: columns not in system.yaml: {sorted(extra)}")
            k = lambda r: tuple(str(r.get(c, "")) for c in t.keys)
            seeded = {k(r) for r in seed}
            rows = [r for r in rows if k(r) not in seeded] + seed
        if len(rows) > MAX_ROWS:
            raise ValueError(f"{name}: {len(rows)} rows exceeds budget of {MAX_ROWS}")
        dest = Path(out_dir) if out_dir else s.dir / "data"
        dest.mkdir(parents=True, exist_ok=True)
        with open(dest / f"{name}.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(t.cols)
            for r in rows:
                w.writerow([_fmt(r.get(c)) for c in t.cols])
        counts[name] = len(rows)
    _read.cache_clear()
    return counts


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, (list, tuple)):
        return ";".join(map(str, v))
    return v


def verify(system_id: str) -> list[str]:
    """Regenerate into a temp dir and compare with the committed data/*.csv. Servers serve data/ as is, so data/
    must be exactly what gen.py + seed/ produce: otherwise a regen (or a master change) silently moves answers."""
    s = load_system(system_id)
    g = s.dir / "gen.py"
    if g.exists():  # wall-clock reads make data depend on the day you regenerate
        bad = WALL_CLOCK.findall(g.read_text())
        if bad:
            return [f"gen.py reads the wall clock ({', '.join(sorted(set(bad)))}); anchor dates on g.as_of"]
    with tempfile.TemporaryDirectory() as tmp:
        try:
            generate(system_id, tmp)
        except Exception as e:  # noqa: BLE001
            return [f"gen failed: {type(e).__name__}: {e}"]
        probs = []
        for name in s.tables:
            a, b = s.dir / "data" / f"{name}.csv", Path(tmp) / f"{name}.csv"
            if not a.exists():
                probs.append(f"data/{name}.csv missing (run gen)")
            elif a.read_bytes() != b.read_bytes():
                old, new = a.read_text().splitlines(), b.read_text().splitlines()
                diff = sum(1 for x, y in zip(old, new) if x != y) + abs(len(old) - len(new))
                probs.append(f"data/{name}.csv differs from gen output ({diff} lines; {len(old) - 1} vs {len(new) - 1} rows)")
        return probs
