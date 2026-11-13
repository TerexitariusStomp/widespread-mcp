"""widespread-mcp — local stdio MCP server for the Widespread protocol.

Holds an Ed25519 agent keypair in ~/.config/widespread/ on THIS machine —
keys are generated and stored client-side, never sent anywhere. Wraps the
same wide_* toolset as the Hermes catalog plugin (vendored _widespread.py).

Run:  uvx widespread-mcp   |   widespread-mcp serve   |   widespread-mcp <tool> <json>
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import _widespread as w

# Redirect key/state storage out of the hermes fallback path.
_DATA = os.path.expanduser(os.environ.get("WIDE_DATA", "~/.config/widespread"))
w._data_path = lambda name: os.path.join(_DATA, name)  # noqa: SLF001


def _tools() -> dict:
    return w._BINDINGS  # noqa: SLF001


def make_server():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("widespread", instructions=(
        "Earn verified-work bounties on the Widespread protocol. Your "
        "Ed25519 key lives locally in ~/.config/widespread/ — never shared. "
        "Start with wide_bounties (open funded work), then wide_claim, "
        "wide_ship, wide_verdict, wide_payout."))
    for name, fn in _tools().items():
        desc = w._SCHEMAS.get(name, {}).get("description", name)  # noqa: SLF001

        def _mk(fn=fn):
            def call(arguments: str = "{}") -> str:
                try:
                    args = json.loads(arguments) if isinstance(arguments, str) else arguments
                except json.JSONDecodeError:
                    return json.dumps({"error": "arguments must be a JSON object string"})
                return fn(args if isinstance(args, dict) else {})
            return call
        mcp.tool(name=name, description=desc)(_mk())
    return mcp


def main() -> None:
    p = argparse.ArgumentParser(prog="widespread-mcp",
        description="Local MCP server + CLI for Widespread bounties")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="stdio MCP server (default)")
    for name in _tools():
        sp = sub.add_parser(name, help=w._SCHEMAS.get(name, {}).get("description", "")[:80])  # noqa: SLF001
        sp.add_argument("args", nargs="?", default="{}", help="JSON arguments")
    a = p.parse_args()
    if a.cmd in (None, "serve"):
        make_server().run(transport="stdio")
        return
    fn = _tools()[a.cmd]
    print(fn(json.loads(a.args)))


if __name__ == "__main__":
    main()
