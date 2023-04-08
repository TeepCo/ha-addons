"""Run Cumulus."""
import asyncio
import concurrent
import logging
import os
import signal
import subprocess
import traceback
import inspect
from typing import Any, Coroutine, TypeVar, Callable

from .config import CumulusConfig
from .messaging import MessagingService
from .tunnel import TunnelService
from .utils import InterruptibleThreadPoolExecutor, CumulusEventLoopPolicy, enable_posix_spawn

_R = TypeVar("_R")
_LOGGER = logging.getLogger(__name__)

class Cumulus:
    """Root object of the Cumulus Add-on."""

    def __init__(self, config: CumulusConfig, loop: asyncio.AbstractEventLoop, shutdown_future: asyncio.Future):
        """
        Create instance of main handler.

        :param config: The configuration
        """
        self._tasks: set[asyncio.Future[Any]] = set()
        self._shutdown_callbacks: set[Callable[[], None]] = set()
        self._shutdown_future = shutdown_future
        self._loop = loop

        self.config = config
        self.msg = MessagingService(self)
        self.tunnel = TunnelService(self)

    def bootstrap(self) -> None:
        """
        Bootstrap services.
        """
        self._add_signal_handlers()
        self.create_task(self.msg.run(), "msg-service")

    def create_task(self, target: Coroutine[Any, Any, Any], name: str = None) -> None:
        """
        Add task to the executor pool.
        """
        self._loop.call_soon_threadsafe(self._async_create_task, target, name)

    def register_shutdown_handler(self, callback: Callable[[], None]) -> None:
        """
        Register callback to run before shutdown.
        """
        self._shutdown_callbacks.add(callback)

    def _async_create_task(self, target: Coroutine[Any, Any, _R], name: str) -> asyncio.Task[_R]:
        """
        Create a task from within the event loop.
        """
        task = self._loop.create_task(target, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def stop(self, exit_code: int = 0) -> None:
        """
        Stop client and shutdown all tasks.
        """
        for callback in self._shutdown_callbacks:
            future = callback()
            if inspect.isawaitable(future):
                await future

        await asyncio.sleep(1)
        for task in self._tasks:
            _LOGGER.warning("Cancel task %s", task.get_name())
            task.cancel()

        self._shutdown_future.set_result(exit_code)

    def _add_signal_handlers(self) -> None:
        """
        Register system signal handler.
        """

        def _handle_signal(signal, _) -> None:
            """
            Wrap signal handling. Queue task to stop execution.
            """
            _LOGGER.debug("Handle signal %d", signal)
            asyncio.run_coroutine_threadsafe(self.stop(), self._loop)

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)


def run(config: CumulusConfig) -> int:
    """
    Run Cumulus client.
    """
    enable_posix_spawn()
    asyncio.set_event_loop_policy(CumulusEventLoopPolicy(config.log_level))
    loop = asyncio.new_event_loop()

    try:
        asyncio.set_event_loop(loop)

        shutdown_future = loop.create_future()
        cumulus = Cumulus(config, loop, shutdown_future)
        cumulus.bootstrap()

        return loop.run_until_complete(shutdown_future)
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            asyncio.set_event_loop(None)
            loop.close()
