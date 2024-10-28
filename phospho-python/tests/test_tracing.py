import pytest
import phospho


def test_tracing():
    phospho.init(tick=0.05, raise_error_on_fail_to_send=True, tracing=True)
