from __future__ import annotations

import inspect
import threading
from typing import List, Optional

from pymodbus.client import ModbusTcpClient


class ModbusTcpClientCompat:
    """Thread-safe sync Modbus TCP client with pymodbus unit/slave/device_id compatibility."""

    def __init__(self, host: str, port: int, timeout: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._client = ModbusTcpClient(host=host, port=port, timeout=timeout)
        self._lock = threading.Lock()

    def close(self) -> None:
        with self._lock:
            try:
                self._client.close()
            except Exception:
                pass

    def _ensure_connected(self) -> None:
        if not self._client.connect():
            raise ConnectionError(f"Cannot connect to {self._host}:{self._port}")

    def _unit_kw(self, func, slave_id: int) -> dict:
        sig = inspect.signature(func)
        if "slave" in sig.parameters:
            return {"slave": slave_id}
        if "device_id" in sig.parameters:
            return {"device_id": slave_id}
        if "unit" in sig.parameters:
            return {"unit": slave_id}
        return {}

    def read_coils(self, address: int, count: int, slave_id: int) -> List[bool]:
        with self._lock:
            self._ensure_connected()
            kw = self._unit_kw(self._client.read_coils, slave_id)
            rr = self._client.read_coils(address, count=count, **kw)
            if rr is None:
                self._client.close()
                raise ConnectionError("No response (None) from read_coils")
            if rr.isError():
                raise RuntimeError(f"Modbus read_coils error: {rr}")
            return list(rr.bits[:count])

    def write_coil(self, address: int, value: bool, slave_id: int) -> None:
        with self._lock:
            self._ensure_connected()
            kw = self._unit_kw(self._client.write_coil, slave_id)
            rr = self._client.write_coil(address, value, **kw)
            if rr is None:
                self._client.close()
                raise ConnectionError("No response (None) from write_coil")
            if rr.isError():
                raise RuntimeError(f"Modbus write_coil error: {rr}")

    def write_register(self, address: int, value: int, slave_id: int) -> None:
        with self._lock:
            self._ensure_connected()
            kw = self._unit_kw(self._client.write_register, slave_id)
            rr = self._client.write_register(address, value, **kw)
            if rr is None:
                self._client.close()
                raise ConnectionError("No response (None) from write_register")
            # Broadcast (unit/slave 0) usually returns no response; pymodbus may return None/timeout.
            # If we got a response object, validate it.
            if hasattr(rr, "isError") and rr.isError():
                raise RuntimeError(f"Modbus write_register error: {rr}")
