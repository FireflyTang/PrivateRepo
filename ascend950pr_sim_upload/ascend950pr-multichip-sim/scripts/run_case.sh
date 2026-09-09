#!/usr/bin/env bash
# Run a supplied offline case in an isolated model directory.
# This does not generate the task queues or MegaMoE input data.
set -euo pipefail
if [[ $# != 1 ]]; then
    echo "Usage: bash $0 /absolute/path/to/complete_case" >&2
    exit 2
fi
: "${ASCEND_HOME_PATH:?Source the CANN set_env.sh first}"
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
case_dir=$(realpath -- "$1")
bundle_dir=$(cd -- "$script_dir/.." && pwd)
case "$case_dir/" in
    "$bundle_dir/results/"*|"$bundle_dir/evidence/"*)
        echo 'Prepare a new work case with prepare_case.py before running; packaged evidence is immutable.' >&2
        exit 2 ;;
esac
python3 - "$case_dir" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
top = json.loads((p / 'top.json').read_text())
chips = [k for k in top if k.startswith('chip')]
if len(chips) not in (1, 2, 4, 8):
    raise SystemExit('Expected 1, 2, 4 or 8 chips')
for chip in chips:
    for die, config in top[chip].items():
        if not config.get('case_path') or not config.get('sq_file'):
            raise SystemExit(f'{chip}.{die}: missing case_path or sq_file; topology alone cannot execute a kernel')
PY
run_root=${SIM_RUN_ROOT:-"$bundle_dir/work"}
mkdir -p "$run_root"
run_dir=$(mktemp -d "$run_root/run_XXXXXX")
model_dir="$run_dir/toolkit/tools/simulator/dav_3510/camodel"
mkdir -p "$model_dir"
# Copy only model files, not the installed model's transient logs/case.
python3 - "$ASCEND_HOME_PATH/tools/simulator/dav_3510/camodel" "$model_dir" <<'PY'
from pathlib import Path
import shutil, sys
for p in Path(sys.argv[1]).iterdir():
    if p.is_file() and not p.name.startswith('.'):
        shutil.copy2(p, Path(sys.argv[2]) / p.name)
PY
echo "Run directory: $run_dir"
ASCEND_HOME_PATH="$run_dir/toolkit" timeout --signal=INT --kill-after=20s "${SIM_TIMEOUT_SECONDS:-600}s" \
    npusim record -c "$case_dir" -o "$run_dir/output" 2>&1 | tee "$run_dir/record.log"
python3 - "$case_dir" "$run_dir/output" <<'PY'
import json, sys
from pathlib import Path
top = json.loads((Path(sys.argv[1]) / 'top.json').read_text())
archives = list(Path(sys.argv[2]).glob('npusim_*'))
if len(archives) != 1:
    raise SystemExit('Expected exactly one new archive')
record = archives[0] / 'record'
for chip in (k for k in top if k.startswith('chip')):
    chip_count = sum(k.startswith('chip') for k in top)
    instr_name = 'instr.bin' if chip_count == 1 else f'{chip}_instr.bin'
    for name in (instr_name, f'{chip}.db'):
        p = record / name
        if not p.is_file() or p.stat().st_size == 0:
            raise SystemExit(f'Capture incomplete: {p}; CLI SUCCESS alone does not prove kernel execution')
print(f'Nonempty per-chip capture files found: {archives[0]}')
print('Next validate database contents, output tensors, and generate the report.')
PY
