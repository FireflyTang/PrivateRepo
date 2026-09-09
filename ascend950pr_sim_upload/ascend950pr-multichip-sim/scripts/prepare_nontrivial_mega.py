#!/usr/bin/env python3
"""Sparse nonzero two-rank fixture with an independently evaluated BF16 golden.

Gate >=16 makes sigmoid rounding to BF16 stable; all surviving values are powers
of two, exactly representable by MX E5M2. Tests routing, both GEMMs and SwiGLU.
"""
from pathlib import Path
import argparse,json,shutil
import numpy as np
root=Path(__file__).resolve().parents[2]/'work'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True,help='Base case from generate_mega_case.py')
parser.add_argument('--output',type=Path,default=root/'mega_nontrivial_2p')
args=parser.parse_args();case=args.output.resolve()
if case.exists():
    raise SystemExit(f'Refusing to overwrite existing evidence: {case}; use --output NEW_CASE')
shutil.copytree(args.source,case)
top=json.loads((case/'top.json').read_text())
def bf16(x):
    a=np.asarray(x,dtype=np.float32).view(np.uint32)
    return ((a+0x7fff+((a>>16)&1))>>16).astype('<u2')
for rank in range(2):
    d=case/f'chip_{rank}';top[f'chip{rank}']['die0']['case_path']=str(d)+'/'
    x=np.zeros((16,1024),np.float32)
    x[:,0]=2.0**((np.arange(16)+rank)%2)
    x[:,1]=2.0**((np.arange(16)+rank)%3)
    bf16(x).tofile(d/'x.bin')
    ids=((np.arange(16)+rank)%2).astype('<i4');ids.tofile(d/'ids.bin')
    probs=np.where(np.arange(16)%3==0,0.5,1).astype(np.float32);bf16(probs).tofile(d/'topk_weights.bin')
    w1=np.zeros((512,1024),np.uint8);w1[:256,0]=0x4c
    w1[256:,1]=np.where(np.arange(256)%2==0,0x3c,0x40)
    w2=np.zeros((1024,256),np.uint8);w2[np.arange(1024),np.arange(1024)%256]=0x3c if rank==0 else 0x40
    for slot,w in [(4,w1),(5,w2)]:
        f=d/f'weight_{slot}.bin';header=f.read_bytes()[:512];f.write_bytes(header+w.tobytes())
    # Independent CPU formula for this sparse operator, in FP64 then BF16 RNE.
    gate=x[:,0].astype(np.float64)*16
    up=x[:,1].astype(np.float64)[:,None]*np.where(np.arange(1024)%2==0,1.,2.)
    expected=(gate/(1+np.exp(-gate)))[:,None]*up*(2.0**ids)[:,None]*probs[:,None]
    bf16(expected).tofile(d/'golden_y.bin')
    np.asarray([16],dtype='<i4').tofile(d/'golden_counts.bin')
    t=json.loads((d/'mega_task.json').read_text())
    t.update(latency=1,schem=1,group_slice=32,aic_icache_prefetch_cnt=0,aiv_icache_prefetch_cnt=0,aic_dcache_prefetch_cnt=64,aiv_dcache_prefetch_cnt=64,task_type=6)
    t['ast_output_array']=[]
    for slot,size,name in [(19,32768,'actual_y.bin'),(20,4,'actual_counts.bin'),(21,110080,'actual_workspace.bin')]:
        arg=next(z for z in t['output_para_array'] if z['para_offset']==slot)
        (d/name).write_bytes(b'\xa5'*size)
        t['ast_output_array'].append(dict(name=name,addr=arg['addr'],size=hex(size)))
    (d/'mega_task.json').write_text(json.dumps(t,indent=2)+'\n')
(case/'top.json').write_text(json.dumps(top,indent=2)+'\n')
print(case)
