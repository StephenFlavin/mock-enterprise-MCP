"""Whole-catalogue coverage: every catalogued system is built and the hub loads them all together."""
from mockmcp import catalog
from mockmcp.spec import system_ids


def test_every_system_built():
    missing = sorted(set(catalog.systems()) - set(system_ids()))
    assert not missing, f"{len(missing)} systems not built: {missing}"


def test_hub_loads_everything():
    from mockmcp.server import Engine, hub_app
    eng = Engine()
    hub_app(eng)
    n = sum(len(s.tools) for s in eng.systems.values())
    assert n == len(catalog.load())
