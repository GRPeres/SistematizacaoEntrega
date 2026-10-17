"""The deployment gate must reject a healthy but stale version."""

import pytest

from scripts.wait_for_deployment import verify_payloads


@pytest.mark.parametrize(
    "health,version,cafes,expected,result",
    [
        ({"status": "ok"}, {"version": "abc"}, [1] * 5, "abc", True),
        ({"status": "ok"}, {"version": "old"}, [1] * 5, "abc", False),
        ({"status": "down"}, {"version": "abc"}, [1] * 5, "abc", False),
        ({"status": "ok"}, {"version": "abc"}, [], "abc", False),
        ([], {"version": "abc"}, [1] * 5, "abc", False),
    ],
)
def test_deployment_gate(health, version, cafes, expected, result):
    assert verify_payloads(health, version, cafes, expected) is result
