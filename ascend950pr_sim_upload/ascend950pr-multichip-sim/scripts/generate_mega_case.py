#!/usr/bin/env python3
"""Experimental two-rank MegaMoe offline fixture; not a precision test.

Requires a key-0 BF16/E5M2 MegaMoe ELF and matching tiling.bin from host helper.
Preserves .text/.data virtual layout, including resolved PC-relative references.
"""
import argparse
import json
import struct
from pathlib import Path


def images(path):
    data = path.read_bytes()
    if data[:5] != b'\x7fELF\x02':
        raise ValueError('Expected ELF64')
    shoff = struct.unpack_from('<Q', data, 40)[0]
    entsize, count, names_idx = struct.unpack_from('<HHH', data, 58)
    sections = [struct.unpack_from('<IIQQQQIIQQ', data, shoff+i*entsize) for i in range(count)]
    names = sections[names_idx]
    strings = data[names[4]:names[4]+names[5]]
    named = {strings[s[0]:].split(b'\0')[0].decode(): s for s in sections}
    text = named['.text']
    image = bytearray(max(named[n][3]+named[n][5] for n in ('.text', '.data')))
    for n in ('.text', '.data'):
        s = named[n]
        image[s[3]:s[3]+s[5]] = data[s[4]:s[4]+s[5]]
    syms = named['.symtab']; st = sections[syms[6]]
    symstr = data[st[4]:st[4]+st[5]]
    entries = {}
    for off in range(syms[4],syms[4]+syms[5],syms[9]):
        n,info,other,idx,value,size=struct.unpack_from('<IBBHQQ',data,off)
        name=symstr[n:].split(b'\0')[0].decode()
        for kind in ('aic','aiv'):
            if name.endswith('_mix_'+kind): entries[kind]=value
    if set(entries) != {'aic','aiv'}: raise ValueError(entries)
    return {kind: bytes(image[start:]) for kind,start in entries.items()}


def main():
    p=argparse.ArgumentParser();p.add_argument('--elf',type=Path,required=True);p.add_argument('--tiling',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
    bins=images(a.elf); top={}
    for rank in range(2):
        d=root/f'chip_{rank}';d.mkdir(exist_ok=True);base=rank*0x10000000000
        def dump(name,obj): (d/name).write_text(json.dumps(obj,indent=2)+'\n')
        task=dict(sqe_type='AIC',mix=1,ratio=2,block_dim=2,group_dim=1,group_slice=16,hbm_para_addr=hex(base+0x8100000000),sub_hbm_para_addr=hex(base+0x8100000000),stack_phy_base=hex(base+0x8200000000),input_para_array=[],output_para_array=[])
        def arg(slot,name,data=None,size=0x100000,addr=None):
            address=base+0x9001000000+slot*0x100000 if addr is None else addr
            item=dict(name=name,size=hex(max(size,len(data or b''))),addr=hex(address),para_offset=slot,hbm_para_offset_en=1,para_type=0)
            if data is not None:
                (d/name).write_bytes(data);task['input_para_array'].append(item)
            else: task['output_para_array'].append(item)
            return address
        ctx=bytearray(16400);struct.pack_into('<IIQ',ctx,0,rank,2,0)
        for r in range(2):struct.pack_into('<Q',ctx,16+r*8,r*0x10000000000+0x8000000000)
        arg(0,'context.bin',ctx)
        arg(1,'x.bin',struct.pack('<H',0x3f80)*(16*1024))
        # Each rank sends half its tokens to the other rank.
        arg(2,'ids.bin',struct.pack('<16i',*([0,1]*8)))
        arg(3,'topk_weights.bin',struct.pack('<H',0x3f80)*16)
        for slot,length,fill in [(4,512*1024,0),(5,1024*256,0),(6,512*16*2,127),(7,1024*4*2,127)]:
            address=base+0x9001000000+slot*0x100000
            arg(slot,f'weight_{slot}.bin',struct.pack('<QQ',8,address+512)+bytes(496)+bytes([fill])*length)
        arg(19,'y.bin');arg(20,'counts.bin');arg(21,'workspace.bin',size=0x4000000,addr=base+0x9400000000)
        arg(22,'tiling.bin',a.tiling.read_bytes())
        for kind,b in bins.items():(d/f'{kind}.bin').write_bytes(b)
        task['BIN']=dict(name='aic.bin',addr=hex(base+0x40000000),sub_name='aiv.bin',sub_addr=hex(base+0x40100000))
        dump('mega_task.json',task)
        dump('mega_sq.json',dict(name='mega_sq',tasks=[dict(sqe_type='AIC',name='mega')]))
        dump('sq_top.json',dict(name='sq_top',sq_base_addr=hex(base+0x9010000000),cq_base_addr=hex(base+0x9018000000),sq_ns_swap_buffer_addr=hex(base+0x9028000000),sq=[dict(name='mega',id=0,stack_phy_base=hex(base+0x8200000000))]))
        top[f'chip{rank}']=dict(die0=dict(case_path=str(d)+'/',sq_file='sq_top.json'))
    (root/'top.json').write_text(json.dumps(top,indent=2)+'\n')
    print(root)

if __name__=='__main__':main()
