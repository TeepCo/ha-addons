"""Handle ssh tunnel between home assistant and cloud."""
import logging
import os
import sys
import asyncio
import time

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cumulus.messages.message_client import RefreshStatus
from cumulus.const import REFRESH_KEYS_AFTER_DAYS

_LOGGER = logging.getLogger(__name__)


class TunnelService:

    def __init__(self, cumulus: 'Cumulus'):
        """
        Init tunnel service.
        """
        self._cumulus = cumulus
        self._process: asyncio.subprocess.Process | None = None
        self._ssh_dir = cumulus.config.config_dir / ".ssh"
        self._ssh_host: str | None = None
        self._ssh_port: int | None = None
        self._ssh_user: str | None = None
        self._forwarding_port: int | None = None
        self._process_terminated = False
        cumulus.register_shutdown_handler(self._shutdown)

    def init_ssh_keys(self) -> str:
        """
        Create .ssh directory and ssh keys if required.

        :returns: ssh public key as string
        """
        TunnelService._check_ssh_directory(self._ssh_dir)
        return TunnelService._check_ssh_keys(self._ssh_dir)

    def open(self, host: str, user: str, port: int, forwarding_port: int):
        """
        Open ssh tunnel.

        :param host: host for ssh connection
        :param user: ssh user
        :param port: ssh port
        :param forwarding_port: port for remote forwarding
        """

        if self._process is not None:
            _LOGGER.debug("Skip open tunnel because is already opened.")
            return

        # TODO: Check if parameters changed then reconnect with new values
        self._ssh_host = host
        self._ssh_user = user
        self._ssh_port = port
        self._forwarding_port = forwarding_port
        self._cumulus.create_task(self._open_tunnel(), "tunnel-service")

    async def _open_tunnel(self):
        _LOGGER.debug(
            "Setup and open ssh tunnel to host=%s with user=%s, port=%d and forwarding_port=%d",
            self._ssh_host, self._ssh_user, self._ssh_port, self._forwarding_port)

        local_ip = self._cumulus.config.ha_ip_address
        local_port = self._cumulus.config.ha_port
        args = [
            "-M", "0", "-vTN", "-4",
            "-p", str(self._ssh_port),
            "-R", f"{self._forwarding_port}:{local_ip}:{local_port}",
            f"{self._ssh_user}@{self._ssh_host}",
        ]

        await self._cumulus.msg.send(RefreshStatus())

        self._process = await asyncio.create_subprocess_exec(
            "autossh", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            # process_group=0
        )

        while self._process.returncode is None:
            log = await self._process.stdout.readline()
            if not log:
                break
            TunnelService._ssh_log(log)

        await self._process.wait()

        if self._process.returncode == 0 or self._process_terminated:
            _LOGGER.info("SSH tunnel successfully exited")
        else:
            _LOGGER.warning("SSH tunnel exited with code=%d", self._process.returncode)
            self._process = None
            await self._cumulus.stop(1)

    async def _shutdown(self) -> None:
        if self._process is not None:
            _LOGGER.debug("Terminate ssh process")
            self._process_terminated = True
            self._process.terminate()
            await self._process.wait()

    @staticmethod
    def _ssh_log(line: bytes) -> None:
        """
        Log line produces by ssh client.
        """
        log = line.strip().decode()
        if log.startswith("debug1: "):
            _LOGGER.debug(log.removeprefix("debug1: "))
        else:
            _LOGGER.info(log)

    @staticmethod
    def _check_ssh_directory(ssh_dir: str) -> None:
        """
        Create .ssh directory if required.
        """
        if not os.path.isdir(ssh_dir):
            try:
                os.mkdir(ssh_dir)
            except OSError:
                _LOGGER.error("Fatal Error: unable to create SSH directory %s", ssh_dir)
                sys.exit(1)

    @staticmethod
    def _check_ssh_keys(ssh_dir: str) -> str:
        """
        Check ssh keys.
        * Create if not exist.
        * If exist check "create time" and re-create if older than `REFRESH_KEYS_AFTER_DAYS`
        * Or only return

        :param ssh_dir: ssh directory
        :returns: content of public key file
        """
        id_key = os.path.join(ssh_dir, "id_key")
        id_pub_key = os.path.join(ssh_dir, "id_key.pub")

        if not os.path.isfile(id_key):
            _LOGGER.debug("Id key not exist.")
            return TunnelService._create_ssh_keys(id_key, id_pub_key)
        elif os.stat(id_key).st_ctime < (time.time() - REFRESH_KEYS_AFTER_DAYS * 86400):
            _LOGGER.debug("Id key is too old.")
            os.remove(id_key)
            os.remove(id_pub_key)
            return TunnelService._create_ssh_keys(id_key, id_pub_key)

        with open(id_pub_key) as key:
            return key.read()

    @staticmethod
    def _create_ssh_keys(id_key, id_pub_key) -> str:
        """
        Create Ed25519 key pair and return public key.
        """
        _LOGGER.info("Refresh SSH ID keys.")
        key = Ed25519PrivateKey.generate()
        private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.OpenSSH,
            crypto_serialization.NoEncryption()
        )
        public_key = key.public_key().public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH
        )

        with open(id_key, "wb") as key_file:
            os.chmod(id_key, 0o600)
            key_file.write(private_key)

        with open(id_pub_key, "wb") as key_file:
            os.chmod(id_pub_key, 0o600)
            key_file.write(public_key)

        return public_key.decode("ascii")
