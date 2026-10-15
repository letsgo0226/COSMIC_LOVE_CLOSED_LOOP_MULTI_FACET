"""Operational regression tests: failures stay failures and image inputs are present."""
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import resident_auto_deploy_loop as resident
import daemon_self_heal_loop as daemon
import account_turing_machine_run as account
from github_api import owned_repositories


def repo(name, owner="alice"):
    return {"name": name, "full_name": owner + "/" + name,
            "owner": {"login": owner}, "default_branch": "main", "private": False}


class Api:
    def __init__(self, mode, batches):
        self.mode = mode
        self.batches = iter(batches)
        self.paths = []
    def request(self, method, path):
        self.paths.append(path)
        rows = next(self.batches)
        return {"repositories": rows} if self.mode == "installation" else rows


class InventoryTests(unittest.TestCase):
    def test_repository_token_uses_public_owner_endpoint(self):
        api = Api("repository", [[repo("one")]])
        rows, truncated = owned_repositories(api, "alice")
        self.assertEqual(len(rows), 1)
        self.assertFalse(truncated)
        self.assertTrue(api.paths[0].startswith("/users/alice/repos?"))

    def test_installation_pagination_filters_foreign_owners(self):
        first = [repo(str(i)) for i in range(99)] + [repo("foreign", "bob")]
        api = Api("installation", [first, [repo("last")]])
        rows, truncated = owned_repositories(api, "alice")
        self.assertEqual(len(rows), 100)
        self.assertFalse(truncated)
        self.assertEqual(len(api.paths), 2)
        self.assertTrue(all(p.startswith("/installation/repositories?") for p in api.paths))
        self.assertTrue(all(r["owner"]["login"] == "alice" for r in rows))

    def test_exact_page_boundary_is_not_false_truncation(self):
        api = Api("user", [[repo(str(i)) for i in range(100)], []])
        rows, truncated = owned_repositories(api, "alice", 100)
        self.assertEqual(len(rows), 100)
        self.assertFalse(truncated)

    def test_budget_reports_actual_truncation(self):
        api = Api("public", [[repo(str(i)) for i in range(3)]])
        rows, truncated = owned_repositories(api, "alice", 2)
        self.assertEqual(len(rows), 2)
        self.assertTrue(truncated)

    def test_daemon_inventory_cache_avoids_repeated_api_calls(self):
        with tempfile.TemporaryDirectory() as temp, patch("account_turing_machine_run.tempfile.gettempdir", return_value=temp), patch.object(account, "TOKEN", ""), patch.object(account, "TOKEN_KIND", "public"), patch.object(account, "OWNER", "alice"), patch.object(account, "MAX_CELLS", 1000), patch.object(account, "owned_repositories", return_value=([repo("one")], False)) as listing, patch.dict(os.environ, {"CL_INVENTORY_CACHE_SEC": "600"}):
            self.assertEqual(account.list_repos(), account.list_repos())
            self.assertEqual(listing.call_count, 1)
            self.assertTrue(account.INVENTORY_META["cache_used"])
            self.assertFalse(account.INVENTORY_META["account_wide_coverage_verified"])


class HealthTests(unittest.TestCase):
    def test_required_child_failure_makes_resident_fail_even_with_valid_core(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "certificates"
            scripts = Path(temp) / "scripts"
            scripts.mkdir()
            (scripts / "bad.py").write_text("raise SystemExit(3)\n")
            with patch.object(resident, "OUT", out), patch.object(resident, "SCRIPTS", scripts), patch.object(resident, "STAGES", [("bad", "bad.py", True)]):
                self.assertEqual(resident.main(), 1)
            cert = json.loads((out / "LATEST_RESIDENT_AUTO_DEPLOY.json").read_text())
            self.assertTrue(cert["core_ok"])
            self.assertFalse(cert["controller_ok"])
            self.assertFalse(cert["all_required_stages_ok"])
            self.assertFalse(cert["deployment_ok"])
            self.assertEqual(cert["stages"][0]["returncode"], 3)
            self.assertEqual(cert["status"], "DEGRADED")

    def test_only_explicitly_optional_missing_stage_is_skipped(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(resident, "SCRIPTS", Path(temp)):
            self.assertEqual(resident.run_stage("required", "missing.py")["status"], "error")
            self.assertEqual(resident.run_stage("optional", "missing.py", False)["status"], "skipped")

    def test_daemon_missing_required_stage_is_unhealthy(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(daemon, "OUT", Path(temp)), patch.object(daemon, "SCRIPTS", Path(temp)), patch.object(daemon, "STAGES", [("missing", "missing.py")]), patch.object(daemon, "RUN_STAGES", True), patch.object(daemon, "ensure_minimal_certs", return_value=[]):
            state = daemon.cycle(0)
            self.assertTrue(state["core_ok"])
            self.assertFalse(state["daemon_healthy"])
            self.assertFalse(state["controller_ok"])
            self.assertEqual(state["errors"], 1)
            self.assertEqual(state["status"], "DEGRADED")

    def test_failed_regeneration_never_creates_passing_placeholder(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(daemon, "OUT", Path(temp)), patch.object(daemon, "SCRIPTS", Path(temp)):
            self.assertEqual(daemon.ensure_minimal_certs(), ["failed:LATEST_CLOSED_LOOP.json"])
            self.assertFalse((Path(temp) / "LATEST_CLOSED_LOOP.json").exists())

    def test_docker_copied_layout_runs_hardware_stage_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            stage = Path(temp)
            for line in (ROOT / "Dockerfile.daemon").read_text().splitlines():
                fields = shlex.split(line)
                if fields and fields[0] == "COPY":
                    source, destination = fields[1:]
                    relative = destination.removeprefix("/app/").rstrip("/")
                    shutil.copytree(ROOT / source.rstrip("/"), stage / relative)
            output = stage / "status"
            process = subprocess.run([sys.executable, str(stage / "scripts/hardware_vm_closed_loop.py")],
                                     cwd=stage, env={**os.environ, "STATUS_DIR": str(output), "PYTHONDONTWRITEBYTECODE": "1"},
                                     capture_output=True, text=True, timeout=10)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(json.loads((output / "LATEST_HARDWARE_VM_LOOP.json").read_text())["all_validated"])


if __name__ == "__main__":
    unittest.main()
