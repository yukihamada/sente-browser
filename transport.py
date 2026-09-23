"""Local IPC: Unix sockets, or authenticated Windows named pipes (never TCP)."""
import hashlib
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys


def state_dir():
    default = (Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "Sente Browser"
               if sys.platform == "win32" else Path.home() / ".local/share/sente-browser")
    return Path(os.environ.get("SENTE_BROWSER_STATE", str(default)))


def prepare_directory(directory):
    if directory.is_symlink():
        raise ValueError("unsafe_state_directory")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if sys.platform == "win32":
        # Restrict the authentication key and runtime to this user and SYSTEM.
        import csv
        identity = subprocess.check_output(["whoami", "/user", "/fo", "csv", "/nh"], text=True)
        sid = next(csv.reader(identity.splitlines()))[1]
        subprocess.run(["icacls", str(directory), "/inheritance:r", "/grant:r",
                        f"*{sid}:(OI)(CI)F", "*S-1-5-18:(OI)(CI)F"], check=True, capture_output=True)
    else:
        if directory.stat().st_uid != os.getuid():
            raise ValueError("unsafe_state_directory")
        directory.chmod(0o700)


def acquire_lock(directory):
    lock = (directory / "host.lock").open("a+b")
    try:
        if sys.platform == "win32":
            import msvcrt
            if not lock.seek(0, 2):
                lock.write(b"\0")
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        raise RuntimeError("another_browser_connected")
    return lock


def pipe_address(directory):
    digest = hashlib.sha256(str(directory.resolve()).casefold().encode()).hexdigest()
    return r"\\.\pipe\sente-browser-" + digest


class PipeStream:
    def __init__(self, connection):
        self.connection = connection
        self.buffer = bytearray()

    def read(self, count):
        if not self.buffer:
            if not self.connection.poll(25):
                raise TimeoutError("local_pipe_timeout")
            self.buffer.extend(self.connection.recv_bytes(512 * 1024 + 4))
        value = bytes(self.buffer[:count])
        del self.buffer[:count]
        return value

    def write(self, data):
        self.connection.send_bytes(data)
        return len(data)

    def flush(self):
        pass  # send_bytes sends the whole message synchronously.


def stream_for(connection):
    if sys.platform == "win32":
        return PipeStream(connection)
    connection.settimeout(25)
    return connection.makefile("rwb", buffering=0)


def listen(directory):
    if sys.platform == "win32":
        from multiprocessing.connection import Listener
        key = secrets.token_bytes(32)
        (directory / "pipe.key").write_bytes(key)
        return Listener(pipe_address(directory), family="AF_PIPE", authkey=key)
    path = directory / "bridge.sock"
    path.unlink(missing_ok=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    path.chmod(0o600)
    server.listen(8)
    return server


def connect(directory):
    if sys.platform == "win32":
        from multiprocessing.connection import Client
        return Client(pipe_address(directory), family="AF_PIPE", authkey=(directory / "pipe.key").read_bytes())
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(25)
    try:
        connection.connect(str(directory / "bridge.sock"))
    except OSError:
        connection.close()
        raise
    return connection
