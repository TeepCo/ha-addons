"""Constants used by Cumulus components."""
from types import SimpleNamespace
from typing import Final


REQUIRED_PYTHON_VER: Final[tuple[int, int, int]] = (3, 10, 0)

REFRESH_KEYS_AFTER_DAYS = 30

MSG_TYPE = SimpleNamespace()
MSG_TYPE.ERROR = "error"
MSG_TYPE.CLIENT_AUTH = "client_auth"
MSG_TYPE.INSTANCE_STATE = "instance_state"
MSG_TYPE.SET_SSH_KEY = "set_ssh_key"
MSG_TYPE.REFRESH_STATUS = "refresh_status"