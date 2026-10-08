"""system.yaml models and loader. A system is tables (CSV-backed) plus tools (declarative)."""
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(__file__).resolve().parent.parent
SYSTEMS = ROOT / "systems"
WORLD = yaml.safe_load((ROOT / "world.yaml").read_text())
WORLD["data_as_of"] = str(WORLD["as_of"])     # the date generated data is anchored to
SHIFT_DAYS = 0                                # set by set_today(); applied to every date column at view time


def set_today(today: date | None = None):
    """Re-anchor the mock world near `today` (default: real today, or MOCKMCP_TODAY=YYYY-MM-DD).
    Data moves by whole weeks so weekdays (e.g. Monday week starts) are preserved, and the world's "today" moves WITH
    the data: it is the anchor date (world.yaml as_of) plus the same whole weeks plus world.yaml today_offset_days, i.e.
    always the same weekday (the latest one on or before the real date, so up to 6 days behind it). The offset is the
    one every system's scenarios were checked at (check runs them at as_of + 13 weeks + 2 days). Every relative date in the data and in the questions ("yesterday",
    "this week", "last 30 days", "on Friday") therefore holds exactly as authored, on whatever weekday a run happens."""
    global SHIFT_DAYS
    env = os.environ.get("MOCKMCP_TODAY")
    data = date.fromisoformat(WORLD["data_as_of"])
    off = int(WORLD.get("today_offset_days", 0))
    real = today or (data + timedelta(days=off) if env == "data" else date.fromisoformat(env) if env else date.today())
    SHIFT_DAYS = ((real - data).days - off) // 7 * 7
    WORLD["real_today"] = real.isoformat()
    WORLD["as_of"] = (data + timedelta(days=SHIFT_DAYS + off)).isoformat()  # the latest such day on or before `real`


def today() -> date:
    """The mock world's today (see set_today). Use this, never date.today(), for anything the model or a tool sees."""
    return date.fromisoformat(WORLD["as_of"])


set_today()

ColType = Literal["str", "text", "int", "float", "bool", "date", "timestamp", "enum", "list"]
Kind = Literal["select", "sql", "insert", "update", "draft", "py"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Col(Strict):
    type: ColType = "str"
    desc: str = ""
    values: list[str] | None = None


class Table(Strict):
    key: str | list[str]
    desc: str = ""
    shift: bool = True              # false = dates are fixed facts (e.g. the calendar), not moved to today
    cols: dict[str, Col]

    @property
    def keys(self) -> list[str]:
        return [self.key] if isinstance(self.key, str) else self.key


class Arg(Strict):
    type: ColType | None = None
    desc: str | None = None
    values: list[str] | None = None
    required: bool = False
    default: Any = None
    col: str | None = None          # select filters: column to filter (default: arg name)
    op: str = "="                   # select filters: = != > >= < <= like in


class ToolSpec(Strict):
    name: str
    desc: str
    kind: Kind
    example: dict[str, Any] = Field(default_factory=dict)
    args: dict[str, Arg | None] = Field(default_factory=dict)
    # select
    from_: str | None = Field(None, alias="from")
    filters: dict[str, Arg | None] = Field(default_factory=dict)
    columns: list[str] | None = None
    order: str | None = None
    limit: int = 20
    # sql / draft
    sql: str | dict[str, str] | None = None
    template: str | None = None
    # insert / update
    table: str | None = None
    id_prefix: str | None = None
    defaults: dict[str, Any] = Field(default_factory=dict)
    set: dict[str, Any] = Field(default_factory=dict)
    key_arg: str | None = None
    delete: bool = False
    # py
    fn: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _list_args(cls, v):
        # allow `args: [a, b]` and `filters: [a, b]` shorthand
        for k in ("args", "filters"):
            if isinstance(v.get(k), list):
                v[k] = {a: None for a in v[k]}
        return v

    @model_validator(mode="after")
    def _kind_fields(self):
        need = {"select": ["from_"], "sql": ["sql"], "insert": ["table", "id_prefix"], "update": ["table"],
                "draft": ["template"], "py": ["fn"]}[self.kind]
        for f in need:
            if getattr(self, f) in (None, ""):
                raise ValueError(f"tool {self.name}: kind '{self.kind}' needs '{f.rstrip('_')}'")
        if self.kind == "sql" and not isinstance(self.sql, str):
            raise ValueError(f"tool {self.name}: sql must be a string for kind sql")
        return self

    @property
    def writes(self) -> bool:
        return self.kind in ("insert", "update")


class System(Strict):
    id: str
    name: str
    instructions: str
    tables: dict[str, Table] = Field(default_factory=dict)
    tools: list[ToolSpec] = Field(default_factory=list)

    @property
    def dir(self) -> Path:
        return SYSTEMS / ("_master" if self.id == "master" else self.id)


class _StrictLoader(yaml.SafeLoader):
    """Rejects duplicate keys, which plain YAML silently resolves to the last one."""

    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(k, deep=deep) for k, _ in node.value]
        dupes = {k for k in keys if keys.count(k) > 1}
        if dupes:
            raise ValueError(f"duplicate YAML key(s) {sorted(map(str, dupes))} near line {node.start_mark.line + 1}")
        return super().construct_mapping(node, deep)


def load_system(system_id: str) -> System:
    d = SYSTEMS / ("_master" if system_id == "master" else system_id)
    raw = yaml.load((d / "system.yaml").read_text(), Loader=_StrictLoader)
    return System.model_validate(raw)


def system_ids() -> list[str]:
    """Ids of systems that have a system.yaml (master excluded)."""
    return sorted(p.parent.name for p in SYSTEMS.glob("*/system.yaml") if p.parent.name != "_master")
