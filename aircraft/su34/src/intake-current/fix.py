from pathlib import Path
import argparse,subprocess,sys,hashlib
root=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();out=Path(a.output);base=a.baseline
for stage in ['prototype','fill','refine']:
 target=out if stage=='refine' else out.with_suffix('.'+stage+'.dnm')
 subprocess.run([sys.executable,str(root/(stage+'.py')),'--baseline',str(base),'--output',str(target),'--report',str(target.with_suffix('.json'))],check=True);base=target
assert hashlib.sha256(out.read_bytes()).hexdigest()=='b6470cf3dcea7a07eac5df5ed17818268232a9fce170ac037b2e795e643c7365'
Path(a.report).write_text(out.with_suffix('.json').read_text())
