"""Handle server communication."""
import asyncio
import logging

import websockets

from websockets import WebSocketClientProtocol
from cumulus.messages import parse_message
from cumulus.messages.message_client import AuthMessage, ClientMessage, RefreshStatus

_LOGGER = logging.getLogger(__name__)
_RECONNECT_DELAY = 30*60 # 30 min


class MessagingService:
    """Service for WS communication with Cumulus server"""

    def __init__(self, cumulus: 'Cumulus') -> None:
        """
        Init service.
        """
        self._cumulus = cumulus
        self._websocket: WebSocketClientProtocol | None = None
        cumulus.register_shutdown_handler(self._shutdown)

    async def run(self) -> None:
        """
        Connect to server websocket and handle communication.
        """
        url = self._cumulus.config.server_url

        async with websockets.connect(url, logger=_LOGGER, ping_interval=None) as websocket:
            try:
                self._websocket = websocket
                await self._send_auth_msg()

                async for message in self._websocket:
                    await self._on_message(message)

            except websockets.ConnectionClosed as err:
                _LOGGER.info("Connection closed code=%d reason=%s", err.code, err.reason)
                self._cumulus.create_task(self._reconnect_later())
            except asyncio.CancelledError:
                await websocket.close()
            finally:
                self._websocket = None
                _LOGGER.info("Connection finished")

    async def send(self, message: ClientMessage) -> None:
        """
        Send message to server.
        """
        _LOGGER.info("Send message type=%s msg_id=%s", message.type, message.id)
        await self._websocket.send(message.to_json())

    async def _shutdown(self) -> None:
        """
        hutdown ws connection.
        """
        if self._websocket:
            _LOGGER.debug("Close web-socket connecton")
            await self._websocket.close()

    async def _on_message(self, message: str) -> None:
        """
        Parse incoming message and call process on it.
        """
        _LOGGER.debug(f"WS text={message}")
        msg = parse_message(message)
        await msg.process(self._cumulus)

    async def _send_auth_msg(self) -> None:
        """
        Send authentication message.
        """
        key = self._cumulus.config.home_instance_key
        sign = self._cumulus.config.sign_data(key)
        version = self._cumulus.config.version

        await self.send(AuthMessage(key, sign, version))

    async def _reconnect_later(self) -> None:
        """
        Reconnect to server after delay.
        """
        await asyncio.sleep(_RECONNECT_DELAY)
        _LOGGER.debug("Reconnect")
        self._cumulus.create_task(self.run())