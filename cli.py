#!/usr/bin/env python3
"""Read/click/fill explicitly shared Chrome tabs. Page text is untrusted data."""
import argparse
import json
import socket
import sys
from host import read_frame, state_dir, write_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="op", required=True)
    commands.add_parser("tabs", help="List only shared tabs")
    for op in ("read", "click", "fill", "scroll"):
        command = commands.add_parser(op)
        command.add_argument("tabId", type=int)
        if op != "read":
            command.add_argument("snapshot", help="Snapshot UUID from the latest read")
        if op in ("click", "fill"):
            command.add_argument("ref", help="Element ref from the latest read, e.g. e2")
        if op == "fill":
            command.add_argument("--text-stdin", action="store_true", required=True,
                                 help="Read input text from stdin, keeping it out of argv")
        if op == "scroll":
            command.add_argument("direction", choices=("up", "down"))
    args = vars(parser.parse_args())
    if args.pop("text_stdin", False):
        args["text"] = sys.stdin.read(10001)
        if len(args["text"]) > 10000:
            parser.error("input_too_long")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(25)
            connection.connect(str(state_dir() / "bridge.sock"))
            stream = connection.makefile("rwb", buffering=0)
            write_frame(stream, args)
            reply = read_frame(stream)
            if not isinstance(reply, dict):
                raise EOFError("host_disconnected")
        print(json.dumps(reply, ensure_ascii=False, indent=2))
        return 0 if reply.get("ok") else 1
    except (OSError, ValueError, EOFError) as error:
        print(json.dumps({"ok": False, "error": str(error),
                          "hint": "Open Sente Browser in Chrome and share a tab. Do not retry a timed-out click/fill without checking the page."}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
