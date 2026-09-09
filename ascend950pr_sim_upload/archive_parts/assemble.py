#!/usr/bin/env python3
"""Verify every part and reconstruct the original tar.gz without overwriting files."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent
m=json.loads((root/'manifest.json').read_text())
out=root/m['output_name'];tmp=root/(m['output_name']+'.assembling')
if out.exists() or tmp.exists():raise SystemExit('Output already exists; choose a fresh directory')
h=hashlib.sha256();size=0
try:
 with tmp.open('xb') as stream:
  for part in m['parts']:
   name=part['name']
   if Path(name).name!=name:raise ValueError('Invalid part path')
   data=(root/name).read_bytes()
   if len(data)!=part['bytes'] or hashlib.sha256(data).hexdigest()!=part['sha256']:raise ValueError('Damaged part: '+name)
   stream.write(data);h.update(data);size+=len(data)
 if size!=m['bytes'] or h.hexdigest()!=m['sha256']:raise ValueError('Archive checksum mismatch')
 tmp.rename(out)
except BaseException:
 tmp.unlink(missing_ok=True)
 raise
print('SHA256 verified:',out)
