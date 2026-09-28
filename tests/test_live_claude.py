"""Native-schema Sonnet isolation and failure behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evaluation.live_claude import run_live_claude
from poc.constrained_composer import plan_schema


class LiveClaudeTest(unittest.TestCase):
    def test_structured_plan_and_successful_source_read(self) -> None:
        evidence = {
            "case_id": "public-test",
            "sources": [{"id": "report", "kind": "customer_report"}],
            "facts": [{"id": "F-one", "source_id": "report", "text": "Reported heat loss"}],
        }
        bundle = {
            "files": {"case.json": "{}", "fact_catalog.json": "{}", "plan_schema.json": "{}"},
            "task": "Investigate.",
            "schema": plan_schema(evidence),
            "evidence": evidence,
            "corpus_sha256": "public-test-hash",
        }
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "fake-claude"
            executable.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "if '--version' in sys.argv: print('fake'); sys.exit()\n"
                "assert sys.argv[sys.argv.index('--model')+1] == 'claude-sonnet-5'\n"
                "assert '--json-schema' in sys.argv\n"
                "assert '--restricted' in sys.argv and '--safe-mode' in sys.argv\n"
                "assert json.loads(sys.argv[sys.argv.index('--json-schema')+1])['type']=='object'\n"
                "print(json.dumps({'type':'assistant','message':{'model':'claude-sonnet-5',"
                "'content':[{'type':'tool_use','name':'Read','id':'a',"
                "'input':{'file_path':'fact_catalog.json'}}]}}))\n"
                "print(json.dumps({'type':'user','message':{'content':[{'type':'tool_result',"
                "'tool_use_id':'a','content':'F-one: Reported heat loss'}]}}))\n"
                "plan={'limit_ids':[], 'next_checks':[{'id':'C-room-impact',"
                "'because_fact_ids':['F-one'],'rationale':'Confirm room heat.'},"
                "{'id':'C-more-data','because_fact_ids':['F-one'],"
                "'rationale':'Obtain measurements.'}]}\n"
                "print(json.dumps({'type':'result','is_error':False,'subtype':'success',"
                "'result':'irrelevant prose','structured_output':plan,'total_cost_usd':0.01}))\n"
            )
            executable.chmod(0o755)
            trace = run_live_claude(bundle, executable=executable)
        self.assertEqual(trace["validation"]["status"], "valid")
        self.assertEqual(trace["assembled_selection"]["observed_fact_ids"], ["F-one"])
        self.assertEqual(trace["source_read_names"], ["fact_catalog"])
        self.assertEqual(trace["visible_fact_ids"], ["F-one"])
        self.assertEqual(trace["display"]["status"], "reference_checked")
        self.assertEqual(trace["raw_answer"], "irrelevant prose")

    def test_missing_structured_output_never_falls_back_to_answer_text(self) -> None:
        evidence = {"case_id": "public-test", "facts": [{"id": "F-one"}]}
        bundle = {
            "files": {"case.json": "{}"},
            "task": "Investigate.",
            "schema": plan_schema(evidence),
            "evidence": evidence,
            "corpus_sha256": "hash",
        }
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "fake-claude"
            executable.write_text(
                "#!/usr/bin/env python3\n"
                "import json,sys\n"
                "if '--version' in sys.argv: print('fake'); sys.exit()\n"
                "print(json.dumps({'type':'assistant','message':{'model':'claude-sonnet-5'}}))\n"
                "print(json.dumps({'type':'result','is_error':False,'result':'{}'}))\n"
            )
            executable.chmod(0o755)
            trace = run_live_claude(bundle, executable=executable)
        self.assertEqual(trace["validation"]["status"], "provider_or_process_failure")
        self.assertEqual(trace["display"]["status"], "withheld")

    def test_unread_fact_id_is_rejected_even_when_in_native_schema(self) -> None:
        evidence = {
            "case_id": "public-test",
            "sources": [{"id": "report", "kind": "customer_report"}],
            "facts": [
                {"id": "F-one", "source_id": "report", "text": "Read fact"},
                {"id": "F-two", "source_id": "report", "text": "Unread fact"},
            ],
        }
        bundle = {
            "files": {"case.json": "{}", "fact_catalog.json": "{}"},
            "task": "Investigate.",
            "schema": plan_schema(evidence),
            "evidence": evidence,
            "corpus_sha256": "hash",
        }
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "fake-claude"
            executable.write_text(
                "#!/usr/bin/env python3\n"
                "import json,sys\n"
                "if '--version' in sys.argv: print('fake'); sys.exit()\n"
                "print(json.dumps({'type':'assistant','message':{'model':'claude-sonnet-5',"
                "'content':[{'type':'tool_use','name':'Read','id':'a',"
                "'input':{'file_path':'fact_catalog.json'}}]}}))\n"
                "print(json.dumps({'type':'user','message':{'content':[{'type':'tool_result',"
                "'tool_use_id':'a','content':'F-one: Read fact'}]}}))\n"
                "plan={'limit_ids':[], 'next_checks':[{'id':'C-room-impact',"
                "'because_fact_ids':['F-two'],'rationale':'Check room.'},"
                "{'id':'C-more-data','because_fact_ids':['F-two'],"
                "'rationale':'Check data.'}]}\n"
                "print(json.dumps({'type':'result','is_error':False,'structured_output':plan}))\n"
            )
            executable.chmod(0o755)
            trace = run_live_claude(bundle, executable=executable)
        self.assertEqual(trace["visible_fact_ids"], ["F-one"])
        self.assertEqual(trace["validation"]["status"], "invalid")
        self.assertEqual(trace["display"]["status"], "withheld")


if __name__ == "__main__":
    unittest.main()
