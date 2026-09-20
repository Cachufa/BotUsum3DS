"""UDP RPC client for Azahar (port 45987)."""

from __future__ import annotations

import socket
import time

from botusum.citra import CITRA_PORT, Citra

RPC_HOST = "127.0.0.1"
RPC_PORT = CITRA_PORT
RPC_PROBE_TIMEOUT_S = 1.0
RPC_WAIT_TIMEOUT_S = 90.0

RPC_DISABLED_MESSAGE = (
    f"Azahar RPC did not answer on {RPC_HOST}:{RPC_PORT}. "
    "Enable Emulation → Configuration → Debug → Enable RPC Server, "
    "quit Azahar, and run this command again."
)


class RpcError(Exception):
    """RPC server missing, disabled, or timed out."""


class RpcClient:
    def __init__(self, host: str = RPC_HOST, port: int = RPC_PORT) -> None:
        self.host = host
        self.port = port
        self._citra = Citra(address=host, port=port)
        self._citra.socket.settimeout(RPC_PROBE_TIMEOUT_S)

    def process_list(self) -> dict[int, tuple[int, str]]:
        try:
            return self._citra.process_list()
        except (TimeoutError, socket.timeout, OSError) as exc:
            raise RpcError(RPC_DISABLED_MESSAGE) from exc

    def read_memory(self, address: int, size: int) -> bytes:
        try:
            data = self._citra.read_memory(address, size)
        except (TimeoutError, socket.timeout, OSError) as exc:
            raise RpcError(RPC_DISABLED_MESSAGE) from exc
        if data is None:
            raise RpcError(f"RPC read_memory returned no data at 0x{address:08X}")
        return data

    def set_process(self, process_id: int) -> None:
        try:
            self._citra.set_process(process_id)
        except (TimeoutError, socket.timeout, OSError) as exc:
            raise RpcError(RPC_DISABLED_MESSAGE) from exc

    def wait_until_ready(self, timeout_s: float = RPC_WAIT_TIMEOUT_S) -> dict[int, tuple[int, str]]:
        deadline = time.time() + timeout_s
        last_error: BaseException | None = None
        while time.time() < deadline:
            try:
                return self.process_list()
            except RpcError as exc:
                last_error = exc
                time.sleep(0.4)
        raise RpcError(RPC_DISABLED_MESSAGE) from last_error
