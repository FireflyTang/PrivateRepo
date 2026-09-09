#!/usr/bin/env python3
"""Check native report Flag endpoints/details against unique raw instruction pairs.

This validates synchronization data, not every ordinary or multi-stage instruction.
Native WAIT starts may be clipped to the preceding instruction by msprof.
"""
import argparse
import collections
import json
import mmap
from pathlib import Path
import re
import struct

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('raw_file', type=Path)
p.add_argument('trace', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
events = json.loads(a.trace.read_text())['traceEvents']
cores = {int(re.match(r'core(\d+)\.', e['pid'])[1]) for e in events
         if e.get('name') in ('SET_FLAG', 'WAIT_FLAG')}
raw = collections.defaultdict(list)
pattern = re.compile(r'\(ID:\s*(\d+)\)\s*(SET_FLAG|WAIT_FLAG)\b')
record = struct.Struct('<QIIQB200s200s7x')
with a.raw_file.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as mm:
    for tick, core, sub, pc, kind, dec, exe in record.iter_unpack(mm):
        core %= 32
        if core not in cores:
            continue
        match = pattern.search(dec.split(b'\0', 1)[0].decode())
        if match:
            detail = ''.join(exe.split(b'\0', 1)[0].decode().split())
            raw[core, sub, int(match[1])].append((kind, tick, pc, match[2], detail))
lookup = {}
for key, values in raw.items():
    if len(values) != 2 or sorted(x[0] for x in values) != [0, 1]:
        raise ValueError(f'Nonunique raw Flag pair: {key}')
    end, start = sorted(values)
    if end[2:] != start[2:]:
        raise ValueError(f'Raw start/end identity mismatch: {key}')
    core, sub, ident = key
    pid = f'core{core}.' + ('cubecore0', 'veccore0', 'veccore1')[sub]
    k = (pid, end[3], end[2], end[1], end[4])
    if k in lookup:
        raise ValueError('Ambiguous native-to-raw match')
    lookup[k] = dict(start=start[1], end=end[1], detail=end[4], raw_id=ident)
begins = {}
seen = set()
groups = collections.defaultdict(dict)
clipped = 0
for event in events:
    if event.get('name') not in ('SET_FLAG', 'WAIT_FLAG') or event.get('ph') not in ('B', 'E'):
        continue
    key = event['pid'], event['name'], str(event['id'])
    if event['ph'] == 'B':
        if key in begins:
            raise ValueError('Duplicate native Flag begin')
        begins[key] = event
        continue
    begin = begins.pop(key)
    end_tick_float = event['ts'] * 1650
    end_tick = round(end_tick_float)
    if abs(end_tick_float - end_tick) > 0.05:
        raise ValueError('Native end timestamp does not resolve to raw tick')
    raw_key = (event['pid'], event['name'], int(begin['args']['pc_addr'], 16), end_tick,
               ''.join(begin['args']['detail'].split()))
    item = lookup[raw_key]
    if raw_key in seen:
        raise ValueError('Raw Flag used twice')
    seen.add(raw_key)
    for e in (begin,):
        if ''.join(e['args']['detail'].split()) != item['detail']:
            raise ValueError('Lost or changed Flag detail')
    start_tick = begin['ts'] * 1650
    if event['name'] == 'SET_FLAG':
        if abs(start_tick - (end_tick - 1)) > 0.05:
            raise ValueError('Unexpected native SET duration')
    elif not item['start'] - 0.05 <= start_tick <= item['end'] + 0.05:
        raise ValueError('Native WAIT outside raw interval')
    elif abs(start_tick - item['start']) > 0.05:
        clipped += 1
    groups[event['id']][event['name']] = item['detail']
if begins or len(seen) != len(lookup):
    raise ValueError('Native report lost raw Flags')
for group in groups.values():
    if set(group) != {'SET_FLAG', 'WAIT_FLAG'} or group['SET_FLAG'] != group['WAIT_FLAG']:
        raise ValueError('Wrong native SET/WAIT pairing')
result = dict(raw_flags=len(raw), matched_flags=len(seen), matched_pairs=len(groups),
              waits_clipped_by_native_exporter=clipped,
              detail_and_endpoints_match=True, frequency_mhz=1650,
              scope='All SET_FLAG/WAIT_FLAG on reported cores; ordinary instructions are not covered')
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
