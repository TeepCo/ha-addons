import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class CumulusConfig:
    """App configuration"""

    config_dir: Path
    log_level: str
    server_url: str
    home_instance_key: str
    home_instance_secret: Ed25519PrivateKey
    ha_ip_address: str
    ha_port: str
    version: str

    def __init__(self, config_dir: str):
        """
        Load configuration file.
        """
        self.config_dir = Path(config_dir).resolve()
        config_file_path = self.config_dir / "options.json"

        with open(config_file_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            self.log_level = config.get("log_level", "info")
            self.server_url = config["server_url"]
            self.home_instance_key = config["home_key"]
            self.home_instance_secret = Ed25519PrivateKey.from_private_bytes(base64.b64decode(config["home_secret"]))

        self.ha_ip_address = os.environ["ENV_HA_IP_ADDRESS"]
        self.ha_port = os.environ["ENV_HA_PORT"]
        self.version = os.environ["ENV_BUILD_VERSION"]

    def sign_data(self, data: str) -> str:
        ascii_data = data.encode("ascii")
        signed_key = self.home_instance_secret.sign(ascii_data)
        encoded_key = base64.b64encode(signed_key)

        return encoded_key.decode("ascii")