#!/usr/bin/env python3
"""Offline modern Xmind JSON archive inspection and copy-on-write editing."""
import argparse, hashlib, json, os, pathlib, sys, tempfile, uuid, zipfile

def digest(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def index(sheets):
    nodes = {}
    def visit(t, sheet, parent=None):
        if not isinstance(t, dict) or not isinstance(t.get('id'), str):
            raise ValueError('Invalid topic')
        if t['id'] in nodes: raise ValueError('Duplicate topic ID')
        nodes[t['id']] = (t, sheet, parent)
        for group in t.get('children', {}).values():
            if not isinstance(group, list): raise ValueError('Invalid children')
            for child in group: visit(child, sheet, t['id'])
    if not isinstance(sheets, list) or not sheets: raise ValueError('Expected sheet array')
    for sheet in sheets: visit(sheet['rootTopic'], sheet)
    return nodes

def run(a):
    source = pathlib.Path(a.source).resolve()
    before = digest(source)
    with zipfile.ZipFile(source) as z:
        names = z.namelist()
        if len(names) != len(set(names)): raise ValueError('Duplicate ZIP members')
        if 'content.json' not in names: raise ValueError('Only modern content.json archives supported')
        # Explicit processing budget, configurable for large user-selected documents.
        if sum(i.file_size for i in z.infolist()) > a.max_bytes:
            raise ValueError('Archive exceeds --max-bytes processing budget')
        sheets = json.loads(z.read('content.json'))
        nodes = index(sheets)
        if a.command == 'inspect':
            selected = nodes
            if a.topic_id:
                if a.topic_id not in nodes: raise ValueError('Unknown topic ID')
                def below(k):
                    while k is not None:
                        if k == a.topic_id: return True
                        k = nodes[k][2]
                    return False
                selected = {k: v for k, v in nodes.items() if below(k)}
            if a.query:
                selected = {k: v for k, v in selected.items() if a.query.casefold() in str(v[0].get('title', '')).casefold()}
            print(json.dumps({'source': str(source), 'sha256': before,
                'sheets': [{'id': s['id'], 'title': s.get('title'), 'rootTopicId': s['rootTopic']['id']} for s in sheets],
                'totalTopics': len(nodes), 'matchedTopics': len(selected),
                'topics': [{'id': k, 'sheetId': s['id'], 'parentId': p, 'title': t.get('title'),
                            'notes': t.get('notes')} for k, (t, s, p) in selected.items()]}, ensure_ascii=False, indent=2))
            return
        request = json.loads(pathlib.Path(a.request).read_text())
        if request.get('source_sha256') != before: raise ValueError('Source digest mismatch; inspect again')
        ops = request.get('operations')
        if not isinstance(ops, list) or not ops: raise ValueError('Expected nonempty operations')
        request_id = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        sequence = 0
        def new_id():
            nonlocal sequence
            sequence += 1
            return str(uuid.uuid5(uuid.NAMESPACE_URL, request_id + ':' + str(sequence)))
        changes = []
        for number, op in enumerate(ops, 1):
            if not isinstance(op, dict): raise ValueError('Operation must be an object')
            allowed = {'op', 'id', 'branch'} if op.get('op') == 'add_branch' else {'op', 'id', 'title'}
            if set(op) != allowed: raise ValueError('Missing or unknown operation fields')
            kind = op['op']
            if kind not in ('rename_topic', 'add_child', 'rename_sheet', 'add_branch'): raise ValueError('Unsupported operation')
            if kind != 'add_branch' and not isinstance(op.get('title'), str): raise ValueError('title must be a string')
            if kind == 'rename_sheet':
                matches = [s for s in sheets if s['id'] == op['id']]
                if len(matches) != 1: raise ValueError('Unknown or ambiguous sheet ID')
                target = sheet = matches[0]
            else:
                target, sheet, _ = nodes[op['id']]
            old = target.get('title')
            if kind == 'add_branch':
                def build(spec):
                    if not isinstance(spec, dict) or not isinstance(spec.get('title'), str): raise ValueError('Branch requires title')
                    if set(spec) - {'title', 'children'}: raise ValueError('Unknown branch fields')
                    children = spec.get('children', [])
                    if not isinstance(children, list): raise ValueError('children must be an array')
                    result = {'id': new_id(), 'class': 'topic', 'title': spec['title']}
                    if children: result['children'] = {'attached': [build(c) for c in children]}
                    return result
                child = build(op['branch'])
                target.setdefault('children', {}).setdefault('attached', []).append(child)
                changes.append({'op': kind, 'parentId': op['id'], 'branch': child})
                nodes = index(sheets)
            elif kind == 'add_child':
                child = {'id': new_id(), 'class': 'topic', 'title': op['title']}
                target.setdefault('children', {}).setdefault('attached', []).append(child)
                changes.append({'op': kind, 'parentId': op['id'], 'id': child['id'], 'title': child['title']})
                nodes = index(sheets)
            else:
                target['title'] = op['title']
                target.pop('titleUnedited', None)
                changes.append({'op': kind, 'id': op['id'], 'before': old, 'after': op['title']})
            changes[-1]['operationId'] = str(number)
            sheet['revisionId'] = new_id()
        index(sheets)
        record = {'schemaVersion': 1, 'requestId': request_id, 'source': str(source),
                  'source_sha256': before, 'changes': changes,
                  'limitations': ['Thumbnail retained from source; may be stale', 'Live UI and legacy XML not synchronized']}
        if digest(source) != before: raise ValueError('Source changed during planning')
        if a.command == 'plan':
            print(json.dumps({**record, 'status': 'planned'}, ensure_ascii=False, indent=2))
            return
        output = pathlib.Path(a.output).absolute()
        if output.exists() or output.resolve() == source: raise ValueError('Output must be a new file')
        tmp = None
        try:
            fd, tmp = tempfile.mkstemp(prefix='.xmind-', dir=output.parent)
            os.close(fd)
            with zipfile.ZipFile(tmp, 'w') as dest:
                dest.comment = z.comment
                for info in z.infolist():
                    payload = json.dumps(sheets, ensure_ascii=False).encode() if info.filename == 'content.json' else z.read(info)
                    dest.writestr(info, payload)
            with zipfile.ZipFile(tmp) as check:
                if check.testzip(): raise ValueError('Output CRC check failed')
                index(json.loads(check.read('content.json')))
            if digest(source) != before: raise ValueError('Source changed during editing')
            os.link(tmp, output)  # atomic publication; fails if destination already exists
        finally:
            if tmp and os.path.exists(tmp): os.unlink(tmp)
        result = {**record, 'status': 'committed', 'output': str(output), 'sha256': digest(output)}
        report = pathlib.Path(str(output) + '.changes.json')
        try:
            with report.open('x') as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
            result['changeRecord'] = str(report)
        except OSError as error:
            result['recordError'] = str(error)
            result['recordRecovery'] = 'Output exists; preserve this stdout as the change record. Do not rerun the edit.'
        print(json.dumps(result, ensure_ascii=False, indent=2))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['inspect', 'plan', 'edit'])
    p.add_argument('source')
    p.add_argument('--query', help='Case-insensitive topic title search during inspect')
    p.add_argument('--topic-id', help='Inspect only this topic and descendants')
    p.add_argument('--request')
    p.add_argument('--output')
    p.add_argument('--max-bytes', type=int, default=256 * 1024 * 1024)
    a = p.parse_args()
    if a.command == 'plan' and not a.request: p.error('plan requires --request')
    if a.command == 'edit' and (not a.request or not a.output): p.error('edit requires --request and --output')
    try: run(a)
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0
if __name__ == '__main__': sys.exit(main())
