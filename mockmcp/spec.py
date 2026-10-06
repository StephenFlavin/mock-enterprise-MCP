"""system.yaml models and loader. A system is tables (CSV-backed) plus tools (declarative)."""
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(__file__).resolve().parent.parent
SYSTEMS = ROOT / "systems"
WORLD = yaml.safe_load((ROOT / "world.yaml").read_text())

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


def load_system(system_id: str) -> System:
    d = SYSTEMS / ("_master" if system_id == "master" else system_id)
    raw = yaml.safe_load((d / "system.yaml").read_text())
    return System.model_validate(raw)


def system_ids() -> list[str]:
    """Ids of systems that have a system.yaml (master excluded)."""
    return sorted(p.parent.name for p in SYSTEMS.glob("*/system.yaml") if p.parent.name != "_master")
