"""Handle client states."""
import logging
from types import SimpleNamespace

from .message import Message
from .message_client import SetSSHKey

_LOGGER = logging.getLogger(__name__)

class InstanceStateMessage(Message):
    """Message with client instance state registered on server."""
    
    _state: str
    _parameters: SimpleNamespace
    
    def __init__(self, msg: SimpleNamespace) -> None:
        """
        Create message with `parameters`.
        """
        self._state = msg.state
        self._parameters = msg

    async def process(self, cumulus: 'Cumulus') -> None:
        _LOGGER.debug(f"Process instance_state message with params={self._parameters}")
        
        match self._state:
            case "registered":
                _LOGGER.debug("Instance state is %s", self._state)
            case "wait_for_key":
                public_key = cumulus.tunnel.init_ssh_keys()
                await cumulus.msg.send(SetSSHKey(public_key))
            case "ready":
                user = self._parameters.user
                port = self._parameters.port
                host = self._parameters.host
                forwarding_port = self._parameters.forwarding_port
                cumulus.tunnel.open(host, user, port, forwarding_port)
            case _:
                _LOGGER.error("I don't know how to handle state=", self._state)