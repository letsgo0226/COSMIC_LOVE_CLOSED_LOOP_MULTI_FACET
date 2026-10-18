"""The managed AKASHA core is local-only; QTM legacy remains separately tested."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

CORE = Path(__file__).resolve().parents[1] / "lfp_atgc_tm_2kb.sh"


class AkashaManagedTests(unittest.TestCase):
    def test_core_size_and_self_encoding(self):
        data = CORE.read_bytes()
        self.assertEqual(len(data.splitlines()), 1)
        self.assertLess(len(data), 2048)
        result = subprocess.run(["sh", str(CORE), "check"], capture_output=True,
                                text=True, timeout=10, check=True)
        self.assertEqual(json.loads(result.stdout),
                         {"p": 55067263, "U2": True, "E257": True,
                          "size": len(data), "scope": "local-only"})

    def test_zero_and_unknown_are_deterministic(self):
        run = subprocess.run(["sh", str(CORE), "zero", "0101", "1010"],
                             capture_output=True, text=True, timeout=10, check=True)
        self.assertEqual(json.loads(run.stdout),
                         {"zero": "1111", "energy": 0, "unique": True})
        with tempfile.TemporaryDirectory() as folder:
            env = {**os.environ, "AKASHA42_DB": str(Path(folder) / "local.jsonl")}
            run = subprocess.run(["sh", str(CORE), "ask", "不存在", "is_a"],
                                 env=env, capture_output=True, text=True,
                                 timeout=10, check=True)
            self.assertEqual(json.loads(run.stdout),
                             {"status": "UNKNOWN", "matches": []})


if __name__ == "__main__":
    unittest.main()
