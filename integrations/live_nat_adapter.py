"""Optional synchronous bridge to the NAT 1.8.0 live read workflow."""

from __future__ import annotations

import asyncio
import importlib.metadata
import json
from pathlib import Path

CONFIG = Path(__file__).with_name("nat_live.yml")


class NatLiveReader:
    """Run every selected read through a registered NAT function."""

    def __init__(self) -> None:
        try:
            from nat.runtime.loader import load_workflow

            import integrations.nat_live  # noqa: F401  registration side effect
        except ImportError as error:
            raise RuntimeError("NAT backend requires integrations/requirements.lock") from error
        self._load_workflow = load_workflow
        self.version = importlib.metadata.version("nvidia-nat")
        if self.version != "1.8.0":
            raise RuntimeError(f"NAT live adapter was verified with 1.8.0, found {self.version}")

    def read(
        self, replay: dict, name: str, arguments: dict, temporal_enabled: bool
    ) -> tuple[dict, list[dict]]:
        request = json.dumps(
            {
                "name": name,
                "replay": replay,
                "arguments": arguments,
                "temporal_enabled": temporal_enabled,
            },
            ensure_ascii=False,
        )

        async def invoke() -> dict:
            async with self._load_workflow(CONFIG) as workflow:
                async with workflow.run(request) as runner:
                    return await runner.result()

        output = asyncio.run(invoke())
        if output.get("name") != name or not isinstance(output.get("facts"), list):
            raise RuntimeError("NAT returned an invalid live reader result")
        return output["result"], output["facts"]
