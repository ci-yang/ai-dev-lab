import pytest

from task_board.demo_verifier import main


@pytest.mark.parametrize(
    ("result", "expected_code", "expected_stream"),
    [
        ("pass", 0, "out"),
        ("fail", 1, "err"),
        ("environment-error", 2, "err"),
    ],
)
def test_demo_verifier_states_are_explicit(
    result: str,
    expected_code: int,
    expected_stream: str,
    capsys: object,
) -> None:
    code = main([result])

    captured = capsys.readouterr()
    assert code == expected_code
    assert "PEDAGOGICAL_DEMO" in getattr(captured, expected_stream)
    other_stream = "err" if expected_stream == "out" else "out"
    assert getattr(captured, other_stream) == ""
