"""WebSocket messages."""
import json
import logging
from types import SimpleNamespace

from cumulus.const import MSG_TYPE
from cumulus.messages.message import Message, NoOperationMessage
from cumulus.messages.message_instance_state import InstanceStateMessage

_LOGGER = logging.getLogger(__name__)

def parse_message(message_json: str) -> Message:
    msg = json.loads(message_json, object_hook=lambda j: SimpleNamespace(**j))

    match msg.type:
        case MSG_TYPE.ERROR:
            _LOGGER.warning("Response msg_id=%s error=%s", msg.id, msg.error)
            return NoOperationMessage()

        case MSG_TYPE.INSTANCE_STATE:
            return InstanceStateMessage(msg)

        case _:
            _LOGGER.warning("Ignore unknown message=%s", message_json)
            return NoOperationMessage()
