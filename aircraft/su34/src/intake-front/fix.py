from pathlib import Path
import argparse,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();root=Path(__file__).resolve().parent;temporary=Path(a.output).with_suffix('.deep.dnm')
subprocess.run([sys.executable,str(root/'deep_build.py'),'--baseline',a.baseline,'--output',str(temporary),'--report',str(temporary.with_suffix('.json'))],check=True)
subprocess.run([sys.executable,str(root/'position.py'),'--baseline',str(temporary),'--output',a.output,'--report',a.report],check=True)
