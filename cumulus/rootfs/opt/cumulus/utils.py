"""Utility helpers."""
import contextlib
import ctypes
import inspect
import logging
import sys
import time
import traceback
import subprocess
import asyncio
import os

from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from typing import Any

EXECUTOR_SHUTDOWN_TIMEOUT = 10
MAX_LOG_ATTEMPTS = 2
JOIN_ATTEMPTS = 10
ALPINE_RELEASE_FILE = "/etc/alpine-release"
MAX_EXECUTOR_WORKERS = 16

_LOGGER = logging.getLogger(__name__)


def _log_thread_running_at_shutdown(name: str, ident: int) -> None:
    """
    Log the stack of a thread that was still running at shutdown.
    """
    frames = sys._current_frames()  # pylint: disable=protected-access
    stack = frames.get(ident)
    formatted_stack = traceback.format_stack(stack)
    _LOGGER.warning(
        "Thread[%s] is still running at shutdown: %s",
        name,
        "".join(formatted_stack).strip(),
    )


def async_raise(tid: int, exctype: Any) -> None:
    """
    Raise an exception in the threads with id tid.
    """
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")

    c_tid = ctypes.c_ulong(tid)  # changed in python 3.7+
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(c_tid, ctypes.py_object(exctype))

    if res == 1:
        return

    # "if it returns a number greater than one, you're in trouble,
    # and you should call it again with exc=NULL to revert the effect"
    ctypes.pythonapi.PyThreadState_SetAsyncExc(c_tid, None)
    raise SystemError("PyThreadState_SetAsyncExc failed")


def join_or_interrupt_threads(threads: set[Thread], timeout: float, log: bool
) -> set[Thread]:
    """
    Attempt to join or interrupt a set of threads.
    """
    joined = set()
    timeout_per_thread = timeout / len(threads)

    for thread in threads:
        thread.join(timeout=timeout_per_thread)

        if not thread.is_alive() or thread.ident is None:
            joined.add(thread)
            continue

        if log:
            _log_thread_running_at_shutdown(thread.name, thread.ident)

        with contextlib.suppress(SystemError):
            # SystemError at this stage is usually a race condition
            # where the thread happens to die right before we force
            # it to raise the exception
            async_raise(thread.ident, SystemExit)

    return joined


class InterruptibleThreadPoolExecutor(ThreadPoolExecutor):
    """A ThreadPoolExecutor instance that will not deadlock on shutdown."""

    def shutdown(self, *args: Any, **kwargs: Any) -> None:
        """
        Shutdown with interrupt support added.
        """
        super().shutdown(wait=False, cancel_futures=True)
        self.join_threads_or_timeout()

    def join_threads_or_timeout(self) -> None:
        """
        Join threads or timeout.
        """
        remaining_threads = set(self._threads)
        start_time = time.monotonic()
        timeout_remaining: float = EXECUTOR_SHUTDOWN_TIMEOUT
        attempt = 0

        while True:
            if not remaining_threads:
                return

            attempt += 1

            remaining_threads -= join_or_interrupt_threads(
                remaining_threads,
                timeout_remaining / JOIN_ATTEMPTS,
                attempt <= MAX_LOG_ATTEMPTS,
            )

            timeout_remaining = EXECUTOR_SHUTDOWN_TIMEOUT - (time.monotonic() - start_time)
            if timeout_remaining <= 0:
                return


class CumulusEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """Event loop policy for Cumulus Add-on."""

    def __init__(self, log_level: str) -> None:
        """
        Init the event loop policy.
        """
        super().__init__()
        self.debug = log_level == "debug"

    def new_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get the event loop.
        """
        loop: asyncio.AbstractEventLoop = super().new_event_loop()
        loop.set_exception_handler(_async_loop_exception_handler)
        loop.set_debug(self.debug)

        executor = InterruptibleThreadPoolExecutor(
            thread_name_prefix="Worker",
            max_workers=MAX_EXECUTOR_WORKERS
        )
        loop.set_default_executor(executor)
        return loop


def _async_loop_exception_handler(loop: asyncio.AbstractEventLoop, context: dict[str, Any]) -> None:
    """
    Handle all exception inside the core loop.
    """

    kwargs = {}
    if exception := context.get("exception"):
        kwargs["exc_info"] = (type(exception), exception, exception.__traceback__)

    if source_traceback := context.get("source_traceback"):
        stack_summary = "".join(traceback.format_list(source_traceback))
        _LOGGER.error("Error doing job: %s: %s", context["message"], stack_summary, **kwargs)
        loop.stop()
        return

    loop.stop()
    _LOGGER.error("Error doing job: %s", context["message"], **kwargs)


def enable_posix_spawn() -> None:
    """
    Enable posix_spawn on Alpine Linux.
    """
    # pylint: disable=protected-access
    if subprocess._USE_POSIX_SPAWN:
        return

    # The subprocess module does not know about Alpine Linux/musl
    # and will use fork() instead of posix_spawn() which significantly
    # less efficient. This is a workaround to force posix_spawn()
    # on Alpine Linux which is supported by musl.
    subprocess._USE_POSIX_SPAWN = os.path.exists(ALPINE_RELEASE_FILE)