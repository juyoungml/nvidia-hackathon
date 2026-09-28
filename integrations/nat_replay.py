"""NeMo Agent Toolkit registration for the public PreDist read-only replay."""

from __future__ import annotations

from nat.plugin_api import (
    Builder,
    FunctionBaseConfig,
    FunctionGroup,
    FunctionGroupBaseConfig,
    FunctionInfo,
    register_function,
    register_function_group,
)

from poc.run import REPLAY, run_tool


class PublicReplayToolsConfig(FunctionGroupBaseConfig, name="public_predist_tools"):
    """Expose only the four existing public-data readers."""


@register_function_group(config_type=PublicReplayToolsConfig)
async def public_predist_tools(config: PublicReplayToolsConfig, _builder: Builder):
    group = FunctionGroup(config=config)

    async def get_recent_measurements(request: str) -> dict:
        """Read the public 24-hour measurement summary and interpretation limits."""
        return run_tool("get_recent_measurements")

    async def get_prior_incidents(request: str) -> dict:
        """Read earlier published faults; current report outcome is withheld."""
        return run_tool("get_prior_incidents")

    async def get_maintenance_timeline(request: str) -> dict:
        """Read earlier maintenance timestamps, without outcomes."""
        return run_tool("get_maintenance_timeline")

    async def get_signal_definitions(request: str) -> dict:
        """Read published sensor definitions and units."""
        return run_tool("get_signal_definitions")

    group.add_function("get_recent_measurements", get_recent_measurements)
    group.add_function("get_prior_incidents", get_prior_incidents)
    group.add_function("get_maintenance_timeline", get_maintenance_timeline)
    group.add_function("get_signal_definitions", get_signal_definitions)
    yield group


class PublicReplayWorkflowConfig(FunctionBaseConfig, name="public_predist_replay_workflow"):
    """Deterministically exercise the tools used by the saved Ultra investigation."""


@register_function(config_type=PublicReplayWorkflowConfig)
async def public_predist_replay_workflow(_config: PublicReplayWorkflowConfig, builder: Builder):
    names = (
        "get_recent_measurements",
        "get_prior_incidents",
        "get_maintenance_timeline",
    )
    group = await builder.get_function_group("public_replay")
    available = await group.get_accessible_functions()
    functions = {name: available[f"public_replay__{name}"] for name in names}

    async def replay(input_message: str) -> dict:
        if input_message != REPLAY["case_id"]:
            raise ValueError("Only the pinned public replay case ID is accepted")
        results = []
        for name in names:
            result = await functions[name].ainvoke(input_message)
            results.append({"tool": name, "result": result})
        return {"case_id": input_message, "tool_results": results}

    yield FunctionInfo.from_fn(replay, description="Run the pinned public PreDist evidence replay")
