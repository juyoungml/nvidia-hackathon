"""Isolation and audit-shape checks for the Claude Code comparator."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from evaluation.claude_code import _source_read_names, main, run_claude_case
from evaluation.domain_mcp import TOOLS, handle, load_bundle
from poc.evidence_contract import build_case_bundle
from poc.system2 import _tool_evidence


class ClaudeCodeRunnerTest(unittest.TestCase):
    def test_file_agent_uses_only_supplied_bundle_and_records_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "fake-claude"
            executable.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "if '--version' in sys.argv: print('fake 1.0'); sys.exit()\n"
                "files = sorted(os.listdir('.'))\n"
                "message = {'type':'assistant','message':{'model':'claude-sonnet-5-test',"
                "'content':[{'type':'tool_use','name':'Read','id':'call-1',"
                "'input':{'file_path':'case.json'}}]}}\n"
                "result = {'type':'result','subtype':'success','is_error':False,"
                "'result':json.dumps({'files':files}),'usage':{'input_tokens':2},"
                "'total_cost_usd':0.01,'num_turns':1}\n"
                "print(json.dumps(message)); print(json.dumps(result))\n"
            )
            executable.chmod(0o755)
            trace = run_claude_case(
                files={"case.json": b"{}"},
                prompt="Read case.json",
                mode="file_agent",
                executable=executable,
            )
        self.assertEqual(json.loads(trace["raw_answer"])["files"], ["case.json"])
        self.assertEqual(trace["resolved_models"], ["claude-sonnet-5-test"])
        self.assertEqual(trace["tool_calls"][0]["name"], "Read")
        self.assertEqual(trace["claude_version"], "fake 1.0")
        self.assertEqual(trace["total_cost_usd"], 0.01)
        self.assertNotIn("--system-prompt", trace["flags"])

    def test_packet_mode_exposes_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "fake-claude"
            executable.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os\n"
                "print(json.dumps({'type':'result','is_error':False,"
                "'result':json.dumps(sorted(os.listdir('.')))}))\n"
            )
            executable.chmod(0o755)
            trace = run_claude_case(
                files={}, prompt="public packet", mode="packet", executable=executable
            )
        self.assertEqual(json.loads(trace["raw_answer"]), [])
        self.assertEqual(trace["file_sha256"], {})

    def test_domain_mode_passes_only_explicit_public_mcp_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "fake-claude"
            executable.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "if '--version' in sys.argv: print('fake 1.0'); sys.exit()\n"
                "p = sys.argv.index('--mcp-config')\n"
                "c = json.load(open(sys.argv[p+1]))\n"
                "print(json.dumps({'type':'result','is_error':False,"
                "'result':json.dumps(c['mcpServers']['public-domain']['args'])}))\n"
            )
            executable.chmod(0o755)
            trace = run_claude_case(
                files={"case.json": b"{}"},
                prompt="public task",
                mode="domain_tools",
                executable=executable,
            )
        self.assertIn("--safe-mode", trace["flags"])
        self.assertIn("--strict-mcp-config", trace["flags"])
        self.assertIn("--mcp-config", trace["flags"])
        self.assertEqual(trace["mcp_call_count"], 0)
        self.assertIn("domain_mcp.py", json.loads(trace["raw_answer"])[0])

    def test_rejects_private_or_nested_bundle_names(self) -> None:
        for name in (".env", "held-out-52.json", "../case.json", "nested/case.json"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    run_claude_case(files={name: b"x"}, prompt="x", mode="file_agent")

    def test_source_reads_exclude_directory_listing(self) -> None:
        calls = [
            {"name": "Glob", "input": {"pattern": "tools/*.json"}},
            {"name": "Read", "input": {"file_path": "/tmp/case/fact_catalog.json"}},
            {
                "name": "Read",
                "input": {"file_path": "/tmp/case/tools/get_recent_measurements.json"},
            },
        ]
        self.assertEqual(_source_read_names(calls), ["fact_catalog", "get_recent_measurements"])

    def test_existing_output_refused_before_model_call(self) -> None:
        replay = Path(__file__).resolve().parents[1] / "data/replay-52.json"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "trace.json"
            output.write_text("original trace\n")
            argv = ["claude_code.py", "--replay", str(replay), "--output", str(output)]
            with (
                patch("sys.argv", argv),
                patch("evaluation.claude_code.run_public_bundle") as run_model,
                redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as error,
            ):
                main()
            self.assertEqual(error.exception.code, 2)
            run_model.assert_not_called()
            self.assertEqual(output.read_text(), "original trace\n")

    def test_domain_mcp_serves_exact_public_tool_evidence(self) -> None:
        replay = json.loads(
            (Path(__file__).resolve().parents[1] / "data/replay-52.json").read_text()
        )
        bundle = build_case_bundle(replay, contract_version=2)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, body in bundle["files"].items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body)
            case, catalog, results = load_bundle(root)
            reads: set[str] = set()
            for index, name in enumerate(TOOLS, 1):
                request = {
                    "jsonrpc": "2.0",
                    "id": index,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": {}},
                }
                response = handle(request, case, catalog, results, reads, root / "mcp-calls.jsonl")
                self.assertFalse(response["result"]["isError"])
                payload = json.loads(response["result"]["content"][0]["text"])
                expected = _tool_evidence(replay, name, results[name])
                self.assertEqual(payload["tool_result"], expected["tool_result"])
                self.assertEqual(payload["facts"], expected["facts"])
            self.assertEqual(reads, set(TOOLS))
            self.assertEqual(len((root / "mcp-calls.jsonl").read_text().splitlines()), 4)


if __name__ == "__main__":
    unittest.main()
