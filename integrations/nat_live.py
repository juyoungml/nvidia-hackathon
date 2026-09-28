"""NAT registrations for model-selected reads of a supplied public replay."""

from __future__ import annotations

import json

from nat.plugin_api import (
    Builder,
    FunctionBaseConfig,
    FunctionGroup,
    FunctionGroupBaseConfig,
    FunctionInfo,
    register_function,
    register_function_group,
)

from poc.evidence_contract import SOURCE_TOOLS
from poc.live_investigation import TEMPORAL_TOOLS, _read_tool

READ_NAMES = (*SOURCE_TOOLS, *TEMPORAL_TOOLS)


class LiveReadToolsConfig(FunctionGroupBaseConfig, name="public_predist_live_tools"):
    """Expose the same bounded public readers as the live investigator."""


@register_function_group(config_type=LiveReadToolsConfig)
async def public_predist_live_tools(config: LiveReadToolsConfig, _builder: Builder):
    group = FunctionGroup(config=config)

    def reader_for(reader_name: str):
        async def read(request: str) -> dict:
            payload = json.loads(request)
            if set(payload) != {"replay", "arguments", "temporal_enabled"}:
                raise ValueError("live read requires replay, arguments, temporal_enabled")
            result, facts = _read_tool(
                payload["replay"], reader_name, payload["arguments"], payload["temporal_enabled"]
            )
            return {"result": result, "facts": facts}

        return read

    for name in READ_NAMES:
        group.add_function(name, reader_for(name))
    yield group


class LiveReadWorkflowConfig(FunctionBaseConfig, name="public_predist_live_read"):
    """Route one selected read through a registered NAT function."""


@register_function(config_type=LiveReadWorkflowConfig)
async def public_predist_live_read(_config: LiveReadWorkflowConfig, builder: Builder):
    group = await builder.get_function_group("public_live")
    available = await group.get_accessible_functions()

    async def invoke(input_message: str) -> dict:
        payload = json.loads(input_message)
        if set(payload) != {"name", "replay", "arguments", "temporal_enabled"}:
            raise ValueError("invalid live read request")
        name = payload.pop("name")
        if name not in READ_NAMES:
            raise ValueError(f"unknown public reader: {name}")
        result = await available[f"public_live__{name}"].ainvoke(
            json.dumps(payload, ensure_ascii=False)
        )
        return {"name": name, **result}

    yield FunctionInfo.from_fn(invoke, description="Execute one bounded public replay read")
