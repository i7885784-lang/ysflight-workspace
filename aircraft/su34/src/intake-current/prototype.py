from pathlib import Path
import argparse,subprocess,sys
root=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();tmp=Path(a.output).with_suffix('.welded.dnm');subprocess.run([sys.executable,str(root/'weld.py'),'--baseline',a.baseline,'--output',str(tmp),'--report',a.report],check=True);subprocess.run([sys.executable,str(root/'shade.py'),'--baseline',str(tmp),'--output',a.output],check=True)
