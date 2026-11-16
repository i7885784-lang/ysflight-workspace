from pathlib import Path
import argparse,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();root=Path(__file__).resolve().parent;temporary=Path(a.output).with_suffix('.nose.dnm')
subprocess.run([sys.executable,str(root/'nose_fix.py'),'--baseline',a.baseline,'--output',str(temporary),'--report',str(temporary.with_suffix('.json'))],check=True)
subprocess.run([sys.executable,str(root/'fit.py'),'--baseline',str(temporary),'--output',a.output,'--report',a.report],check=True)
