from unittest.mock import MagicMock

from notifications.utils import run_async


def test_run_async_calls_function():
    mock_func = MagicMock()

    run_async(mock_func, 1, 2, test="ok")

    # On laisse un tout petit délai au thread
    import time

    time.sleep(0.1)

    mock_func.assert_called_once_with(1, 2, test="ok")
