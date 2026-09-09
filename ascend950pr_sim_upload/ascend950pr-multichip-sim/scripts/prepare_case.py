#!/usr/bin/env python3
"""Clone a final nontrivial case, relocate its task paths, reset exported outputs."""
import argparse
import json
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('kind', choices=('megamoe', 'dispatch'))
p.add_argument('--output', type=Path, required=True)
p.add_argument('--bundle', type=Path, required=True, help='Extracted ascend950pr_sim_bundle directory')
a = p.parse_args()
bundle = a.bundle.resolve(strict=True)
out = a.output.resolve()
if out.exists():
    p.error('Output must be a new directory')
if any(out.is_relative_to(bundle / part) for part in ('results', 'evidence', 'references')):
    p.error('Choose a work directory outside packaged evidence')
shutil.copytree(bundle / 'results' / a.kind / 'case', out)
top = json.loads((out / 'top.json').read_text())
for rank in range(2):
    chip = out / f'chip_{rank}'
    top[f'chip{rank}']['die0']['case_path'] = str(chip) + '/'
    task = json.loads((chip / ('mega_task.json' if a.kind == 'megamoe' else 'dispatch_task.json')).read_text())
    for item in task['ast_output_array']:
        size = int(item['size'], 0) if isinstance(item['size'], str) else item['size']
        target = (chip / item['name']).resolve()
        if not target.is_relative_to(chip):
            raise ValueError('Output filename escapes chip directory')
        target.write_bytes(b'\xa5' * size)
(out / 'top.json').write_text(json.dumps(top, indent=2) + '\n')
print(out)
