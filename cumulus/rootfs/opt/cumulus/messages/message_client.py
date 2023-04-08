"""Client messages."""
import dataclasses
import json
import uuid
from json import JSONEncoder

from cumulus.const import MSG_TYPE
from .message import Message


class ClientMessage(Message, JSONEncoder):
    id: str
    type: str

    def __init__(self, msg_type: str):
        self.id = uuid.uuid4().hex[0:6]
        self.type = msg_type

    async def process(self, cumulus: 'Cumulus') -> None:
        """
        Client messages are not processed on client side.
        """
        pass

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__)


class AuthMessage(ClientMessage):
    """Authorization client message."""

    def __init__(self, key: str, signature: str, version: str):
        super().__init__(MSG_TYPE.CLIENT_AUTH)
        self.key = key
        self.signature = signature
        self.client_version = version


class SetSSHKey(ClientMessage):
    """Set ssh client public key."""

    def __init__(self, key: str):
        super().__init__(MSG_TYPE.SET_SSH_KEY)
        self.key = key


class RefreshStatus(ClientMessage):
    """Invoke refresh instance status."""

    def __init__(self):
        super().__init__(MSG_TYPE.REFRESH_STATUS)