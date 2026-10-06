"""One test per built system: lint, every tool's example, every scenario. Same as `python -m mockmcp check`."""
import pytest

from mockmcp.check import check
from mockmcp.spec import system_ids


@pytest.mark.parametrize("sid", system_ids())
def test_system(sid):
    problems = check(sid)
    assert not problems, "\n".join(problems)
