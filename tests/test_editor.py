import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'xmind.py'

class EditorTest(unittest.TestCase):
    def test_plan_commit_and_rejections(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'source.xmind'
            with zipfile.ZipFile(source, 'w') as z:
                z.writestr('content.json', json.dumps([{'id': 'sheet', 'title': 'Map', 'rootTopic': {'id': 'root', 'title': 'Root'}}]))
                z.writestr('resources/example.txt', b'preserve me')
            original = source.read_bytes()
            def call(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], text=True, capture_output=True)
            inspect = json.loads(call('inspect', source).stdout)
            request = {'source_sha256': inspect['sha256'], 'operations': [{'op': 'add_branch', 'id': 'root', 'branch': {'title': 'Plan', 'children': [{'title': 'Test'}]}}]}
            req = root / 'request.json'
            req.write_text(json.dumps(request))
            plan = call('plan', source, '--request', req)
            self.assertEqual(plan.returncode, 0, plan.stderr)
            self.assertEqual(len(list(root.iterdir())), 2)
            output = root / 'output.xmind'
            commit = call('edit', source, '--request', req, '--output', output)
            self.assertEqual(commit.returncode, 0, commit.stderr)
            self.assertEqual(json.loads(plan.stdout)['changes'], json.loads(commit.stdout)['changes'])
            self.assertTrue(Path(str(output) + '.changes.json').exists())
            with zipfile.ZipFile(output) as z:
                self.assertEqual(z.read('resources/example.txt'), b'preserve me')
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(hashlib.sha256(original).hexdigest(), inspect['sha256'])
            self.assertNotEqual(call('edit', source, '--request', req, '--output', output).returncode, 0)
            request['operations'].append({'op': 'rename_topic', 'id': 'missing', 'title': 'Bad'})
            req.write_text(json.dumps(request))
            bad = root / 'bad.xmind'
            self.assertNotEqual(call('edit', source, '--request', req, '--output', bad).returncode, 0)
            self.assertFalse(bad.exists())
            request['source_sha256'] = 'stale'
            req.write_text(json.dumps(request))
            self.assertNotEqual(call('plan', source, '--request', req).returncode, 0)

if __name__ == '__main__':
    unittest.main()
