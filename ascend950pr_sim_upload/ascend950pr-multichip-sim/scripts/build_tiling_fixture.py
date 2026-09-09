#!/usr/bin/env python3
"""Reuse host tiling functions from an isolated configured ops-transformer build."""
import argparse
import os
import shlex
import subprocess
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--build-tree',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
root=a.build_tree.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
src=root/'mc2/mega_moe/op_host/op_tiling/arch35/mega_moe_tiling.cpp'
# Drop framework registration/exception constructor; retain original numeric functions.
source=src.read_text().split('IMPL_OP_OPTILING(MegaMoe)')[0]+'\n}\n'
source+=Path(__file__).with_name('tiling_fixture_main.inc').read_text()
(out/'helper.cpp').write_text(source)
flags=(root/'build/mc2/mega_moe/op_host/CMakeFiles/ophost_transformer_tiling_obj.dir/flags.make').read_text()
args=[]
for key in ('CXX_DEFINES','CXX_INCLUDES'):
    args+=shlex.split(next(l.split(' = ',1)[1] for l in flags.splitlines() if l.startswith(key+' = ')))
lib=Path(os.environ['ASCEND_HOME_PATH'])/'lib64'
cmd=['g++',*args,'-I'+str(src.parent),'-std=c++17','-O2','-ffunction-sections','-fdata-sections',
     '-Wl,--gc-sections',str(out/'helper.cpp'),'-L'+str(lib),'-Wl,-rpath,'+str(lib),
     '-lregister','-lgraph','-lunified_dlog','-lmetadef','-o',str(out/'helper')]
with (out/'build.log').open('w') as log:
    subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
subprocess.run([str(out/'helper'),str(out/'tiling.bin')],check=True)
