"""Run the 1 Hz image's exact COPY layout, not the full repository tree."""
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ResidentImageTests(unittest.TestCase):
    def test_image_can_seal_and_run_real_ticks_with_quantum_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for line in (ROOT/'Dockerfile.resident-1hz').read_text().splitlines():
                fields=shlex.split(line)
                if fields and fields[0]=='COPY':
                    source,destination=fields[1:]
                    target=root/destination.removeprefix('/app/')
                    target.parent.mkdir(parents=True,exist_ok=True)
                    if (ROOT/source).is_dir():
                        shutil.copytree(ROOT/source,target)
                    else:
                        shutil.copy2(ROOT/source,target)
            probe=subprocess.run([sys.executable,'engine/COSMIC_LOVE_VALIDATOR.py','image check'],cwd=root,capture_output=True,text=True,timeout=5)
            self.assertEqual(probe.returncode,0,probe.stderr)
            self.assertTrue(json.loads(probe.stdout.splitlines()[-1])['quantum']['U2_identity'])
            env={**os.environ,'INTERVAL_SEC':'.05','SUMMARY_EVERY':'1','AXIOM_EVERY':'1','TICK_SEAL':'1','STATUS_DIR':str(root/'status'),'PYTHONDONTWRITEBYTECODE':'1'}
            child=subprocess.Popen([sys.executable,'-u','scripts/resident_1hz_loop.py'],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
            try:
                with self.assertRaises(subprocess.TimeoutExpired):child.communicate(timeout=1)
            finally:
                os.killpg(child.pid,signal.SIGTERM)
                stdout,stderr=child.communicate(timeout=5)
            ticks=[json.loads(line) for line in stdout.splitlines() if '"system": "RESIDENT_1HZ"' in line]
            self.assertGreaterEqual(len(ticks),2,stdout+stderr)
            self.assertTrue(all(t['status']=='ok' and t['H_formal']==0 for t in ticks))
            self.assertEqual(stderr,'')

if __name__=='__main__':unittest.main()
