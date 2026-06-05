from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from afritech.cli.commands.inspect_chain import run as inspect_chain
from afritech.cli.commands.run_pilot_check import run as run_pilot_check
from afritech.cli.commands.simulate_network import run as simulate_network
from afritech.cli.commands.simulate_network import run_five_node as simulate_five_node
from afritech.cli.commands.simulate_network import run_twenty_node as simulate_twenty_node
from afritech.cli.commands.start_node import run as start_node


COMMANDS = {
    "start-node": start_node,
    "inspect-chain": inspect_chain,
    "run-pilot-check": run_pilot_check,
    "simulate-5-node": simulate_five_node,
    "simulate-20-node": simulate_twenty_node,
    "simulate-network": simulate_network,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser("AfriTech CLI")
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    result = COMMANDS[args.command]()
    _emit(result, as_json=args.json)
    return 0


def _emit(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        print(result.get("summary", json.dumps(result, sort_keys=True, default=str)))


if __name__ == "__main__":
    raise SystemExit(main())
