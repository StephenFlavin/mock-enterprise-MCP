"""Data generation: run systems/<id>/gen.py, overlay seed/*.csv by key, write data/*.csv in spec column order."""
import csv
import importlib.util
import random
import zlib
from datetime import date, timedelta
from functools import cache

from faker import Faker

from .spec import SYSTEMS, WORLD, System, load_system

MAX_ROWS = 60000


class Gen:
    """Handed to generate(g). Seeded, so output is identical on every run."""

    def __init__(self, system_id: str):
        seed = WORLD["seed"] + zlib.crc32(system_id.encode())
        self.rng = random.Random(seed)
        self.fake = Faker("en_GB")
        self.fake.seed_instance(seed)
        self.world = WORLD
        self.as_of = date.fromisoformat(WORLD["data_as_of"])

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


def generate(system_id: str) -> dict[str, int]:
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
        (s.dir / "data").mkdir(exist_ok=True)
        with open(s.dir / "data" / f"{name}.csv", "w", newline="") as fh:
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
