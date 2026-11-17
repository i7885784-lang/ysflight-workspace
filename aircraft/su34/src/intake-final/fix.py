from pathlib import Path
import argparse,subprocess,sys
root=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();tmp=Path(a.output).with_suffix('.prototype.dnm');subprocess.run([sys.executable,str(root/'prototype.py'),'--baseline',a.baseline,'--output',str(tmp),'--report',str(tmp.with_suffix('.json'))],check=True);subprocess.run([sys.executable,str(root/'step.py'),'--baseline',str(tmp),'--output',a.output,'--report',a.report],check=True)
