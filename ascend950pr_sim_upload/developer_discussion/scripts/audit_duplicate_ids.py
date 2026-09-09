#!/usr/bin/env python3
"""Read-only audit of helper rejected IDs against the original instr.bin."""
import argparse,collections,json,mmap,re,sqlite3,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=a.archive/'record';lines=(r/'cannsim_helper.log').read_text().splitlines()
errors=[tuple(map(int,m.groups())) for l in lines if (m:=re.search(r'insert instr failed .*exec_id=(\d+) instr_id=(\d+) core=(\d+) sub_core=(\d+)',l))]
s=struct.Struct('<QIIQB200s200s7x');id_re=re.compile(rb'\(ID:\s*(\d+)\)');result={}
for db in sorted(r.glob('chip*.db')):
 rank=int(db.stem[4:]);c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True);entries={}
 for eid,i,core,sub in errors:
  row=c.execute('select SourceInstrAddr,ExecInstrTickStart,ExecInstrTickEnd,ExecInstrName,ExecInstrCoreId,CoreTypeId from ExecutedInstructions where ExecInstrId=?',(eid,)).fetchone()
  if row:entries[(core,sub,i)]=dict(exec_id=eid,db_pc=hex(row[0]),db_start=row[1],db_end=row[2],name=row[3],db_core=row[4],db_type=row[5],raw=[])
 with (r/f'chip{rank}_instr.bin').open('rb') as f:
  with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
   if len(mm)%s.size:raise ValueError('partial raw entry')
   for tick,core,sub,pc,kind,label,param in s.iter_unpack(mm):
    match=id_re.search(label)
    if not match:continue
    key=(core-rank*32,sub,int(match[1]))
    if key in entries:entries[key]['raw'].append(dict(tick=tick,kind=kind,pc=hex(pc),label=label.rstrip(b'\0').decode()))
 counts=collections.Counter()
 for e in entries.values():
  starts=[x for x in e['raw'] if x['kind']==1];ends=[x for x in e['raw'] if x['kind']==0]
  if len(starts)==len(ends)==1 and starts[0]['pc']==ends[0]['pc']:
   counts['single_complete_raw_pair']+=1
   if e['db_start']==e['db_end']<starts[0]['tick']:counts['db_zero_duration_before_raw_start']+=1
  else:counts['other_pairing']+=1
  counts['db_name_'+e['name']]+=1
 result[db.name]=dict(rejected_ids_in_db=len(entries),classification=dict(counts),details=list(entries.values()))
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{x:y for x,y in v.items() if x!='details'} for k,v in result.items()},indent=2))
