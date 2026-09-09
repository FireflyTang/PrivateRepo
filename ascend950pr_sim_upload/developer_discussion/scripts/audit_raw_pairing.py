#!/usr/bin/env python3
"""Describe raw stage imbalance without inventing missing instruction times."""
import argparse
import collections
import json
import mmap
import re
import struct
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('archive', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
record = struct.Struct('<QIIQB200s200s7x')
pattern = re.compile(rb'\(ID:\s*(\d+)\)\s*(\w+)')
result = {}
for f in sorted((a.archive / 'record').glob('chip*_instr.bin')):
    events = collections.defaultdict(list)
    with f.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        if len(mm) % record.size:
            raise ValueError('Incomplete raw entry')
        for tick, core, sub, pc, kind, label, param in record.iter_unpack(mm):
            m = pattern.search(label)
            if m:
                events[core, sub, int(m[1])].append((tick, kind, label.split(b'\0')[0].decode()))
    counts = collections.Counter()
    examples = {}
    for key, ev in events.items():
        starts = sum(k == 1 for t,k,l in ev)
        ends = sum(k == 0 for t,k,l in ev)
        if starts != ends:
            name = pattern.search(ev[0][2].encode())[2].decode()
            category = f'{name}: {starts} start / {ends} end'
            counts[category] += 1
            examples.setdefault(category, dict(core_sub_id=key, events=ev))
    result[f.name] = dict(imbalanced_categories=dict(counts), examples=examples)
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:v['imbalanced_categories'] for k,v in result.items()}, indent=2))
