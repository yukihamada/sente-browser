#!/usr/bin/env python3
"""Chrome native messaging to same-user local IPC. No TCP listener."""
import concurrent.futures
import json
from multiprocessing import AuthenticationError
import os
import struct
import sys
import threading
import uuid
from transport import state_dir, prepare_directory, acquire_lock, listen, stream_for

MAX_BYTES = 512 * 1024
EXTENSION_ID = "jnnfblhbdlgofcadhgaicafimchnbdnl"
ALLOWED_EXTENSION_IDS = (EXTENSION_ID, "ndpogcpncelkickingfpfdbajchdbnim")


def read_exact(stream, count):
    parts = bytearray()
    while len(parts) < count:
        chunk = stream.read(count - len(parts))
        if not chunk:
            if not parts:
                return None
            raise EOFError("incomplete_frame")
        parts.extend(chunk)
    return bytes(parts)


def read_frame(stream):
    prefix = read_exact(stream, 4)
    if prefix is None:
        return None
    size = struct.unpack("<I", prefix)[0]
    if size > MAX_BYTES:
        raise ValueError("frame_too_large")
    payload = read_exact(stream, size)
    if payload is None:
        raise EOFError("incomplete_frame")
    return json.loads(payload)


def write_frame(stream, value):
    data = json.dumps(value, ensure_ascii=False).encode("utf-8")
    if len(data) > MAX_BYTES:
        raise ValueError("frame_too_large")
    frame = memoryview(struct.pack("<I", len(data)) + data)
    while frame:
        written = stream.write(frame)
        if written is None or written <= 0:
            raise EOFError("incomplete_write")
        frame = frame[written:]
    stream.flush()


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {"chrome-extension://" + ident + "/" for ident in ALLOWED_EXTENSION_IDS}:
        raise SystemExit("extension_origin_required")
    os.umask(0o077)
    if sys.platform == "win32":
        import msvcrt
        for stream in (sys.stdin, sys.stdout):
            msvcrt.setmode(stream.fileno(), os.O_BINARY)
    directory = state_dir()
    prepare_directory(directory)
    try:
        lock = acquire_lock(directory)
    except RuntimeError as error:
        raise SystemExit(str(error))
    server = listen(directory)
    write_lock = threading.Lock()
    pending_lock = threading.Lock()
    pending = {}
    slots = threading.BoundedSemaphore(8)

    def reply(value):
        with write_lock:
            write_frame(sys.stdout.buffer, value)

    def client(connection):
        try:
            with connection:
                stream = stream_for(connection)
                request = read_frame(stream)
                if not isinstance(request, dict) or request.get("op") not in {"tabs", "read", "fill", "click", "scroll"}:
                    write_frame(stream, {"ok": False, "error": "unsupported_operation"})
                    return
                ident = uuid.uuid4().hex
                future = concurrent.futures.Future()
                with pending_lock:
                    pending[ident] = future
                try:
                    reply({"type": "request", "id": ident, "request": request})
                    value = future.result(timeout=20)
                except concurrent.futures.TimeoutError:
                    value = {"ok": False, "error": "timeout_result_unknown_do_not_retry_mutations"}
                finally:
                    with pending_lock:
                        pending.pop(ident, None)
                write_frame(stream, value)
        except (OSError, ValueError, EOFError):
            pass  # A malformed/disconnected local client cannot stop Chrome's host.
        finally:
            slots.release()

    def accept():
        while True:
            try:
                accepted = server.accept()
                connection = accepted if sys.platform == "win32" else accepted[0]
            except AuthenticationError:
                continue  # A rejected local peer must not stop future valid connections.
            except OSError:
                return
            if slots.acquire(blocking=False):
                threading.Thread(target=client, args=(connection,), daemon=True).start()
            else:
                connection.close()

    threading.Thread(target=accept, daemon=True).start()
    reply({"type": "ready"})
    try:
        while True:
            value = read_frame(sys.stdin.buffer)
            if value is None:
                break
            if not isinstance(value, dict):
                continue
            with pending_lock:
                future = pending.get(value.get("id"))
                if future and not future.done():
                    future.set_result(value)
    finally:
        server.close()
        (directory / ("pipe.key" if sys.platform == "win32" else "bridge.sock")).unlink(missing_ok=True)
        lock.close()


if __name__ == "__main__":
    main()
