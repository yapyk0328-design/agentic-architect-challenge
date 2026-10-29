import pytest

from document_agent.cli import calculate


def test_calculator_basic_arithmetic():
    assert calculate("12 * 3") == 36


def test_calculator_rejects_code_execution():
    with pytest.raises(ValueError):
        calculate("__import__('os').system('echo unsafe')")
