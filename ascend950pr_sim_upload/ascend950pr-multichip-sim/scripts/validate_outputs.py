#!/usr/bin/env python3
"""Numerical validation independent of simulator task completion / reports."""
import argparse
import collections
import json
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('kind', choices=['mega', 'dispatch'])
p.add_argument('case', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
result = {}
for rank in range(2):
    d = a.case / f'chip_{rank}'
    if a.kind == 'mega':
        actual = np.fromfile(d / 'actual_y.bin', '<u2')
        gold = np.fromfile(d / 'golden_y.bin', '<u2')
        if actual.shape != gold.shape:
            raise ValueError('Wrong y size')
        af = (actual.astype(np.uint32) << 16).view(np.float32)
        gf = (gold.astype(np.uint32) << 16).view(np.float32)
        counts = np.fromfile(d / 'actual_counts.bin', '<i4')
        gc = np.fromfile(d / 'golden_counts.bin', '<i4')
        result[f'chip{rank}'] = dict(elements=int(actual.size), mismatches=int(np.count_nonzero(actual != gold)), max_abs_error=float(np.max(np.abs(af-gf))), finite=bool(np.all(np.isfinite(af))), actual_first=af[:16].tolist(), expected_first=gf[:16].tolist(), counts=counts.tolist(), counts_correct=bool(np.array_equal(counts,gc)))
    else:
        actual = np.fromfile(d / 'actual_slot9.bin', 'i1', count=64*7168).reshape(64,7168)
        scales = np.fromfile(d / 'actual_slot10.bin', '<f4', count=64)
        triple = np.fromfile(d / 'actual_slot11.bin', '<i4', count=64*3).reshape(64,3)
        counts = np.fromfile(d / 'actual_slot12.bin', '<i8')
        recv = np.fromfile(d / 'actual_slot13.bin', '<i4')
        inputs = [np.fromfile(a.case/f'chip_{r}'/f'x_{r}.bin','<f2').reshape(8,7168).astype(np.float32) for r in range(2)]
        ids = [np.fromfile(a.case/f'chip_{r}'/f'expert_ids_{r}.bin','<i4').reshape(8,8) for r in range(2)]
        expected = {(r,t,k) for r in range(2) for t in range(8) for k in range(8) if rank*4 <= ids[r][t,k] < rank*4+4}
        got = [tuple(map(int,t)) for t in triple]
        bad_rows=[];bad_scale=[];bad_expert=[]
        for row,(r,t,k) in enumerate(got):
            if not (0<=r<2 and 0<=t<8 and 0<=k<8):
                bad_rows.append(row);continue
            x=inputs[r][t];scale=np.max(np.abs(x))/np.float32(127)
            q=np.rint(x/scale).clip(-128,127).astype(np.int8)
            if not np.array_equal(actual[row],q):bad_rows.append(row)
            if not np.isclose(scales[row],scale,rtol=1e-6,atol=0):bad_scale.append(row)
            if ids[r][t,k] != rank*4+row//16:bad_expert.append(row)
        result[f'chip{rank}']=dict(quant_bad_rows=bad_rows,scale_bad_rows=bad_scale,expert_group_bad_rows=bad_expert,triples_complete=collections.Counter(got)==collections.Counter(expected),counts=counts.tolist(),counts_correct=bool(np.array_equal(counts,[16]*4)),ep_recv_counts=recv.tolist(),ep_recv_counts_correct=bool(np.array_equal(recv,np.arange(1,9)*8)),empty_rows=np.flatnonzero(np.all(actual==0,axis=1)).tolist(),first_triples=triple[:20].tolist())
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if a.kind=='mega':
    ok=all(v['mismatches']==0 and v['finite'] and v['counts_correct'] for v in result.values())
else:
    ok=all(not v['quant_bad_rows'] and not v['scale_bad_rows'] and not v['expert_group_bad_rows'] and v['triples_complete'] and v['counts_correct'] and v['ep_recv_counts_correct'] for v in result.values())
raise SystemExit(0 if ok else 1)
