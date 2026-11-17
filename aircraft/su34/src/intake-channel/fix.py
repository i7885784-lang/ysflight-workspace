from pathlib import Path
import argparse,subprocess,sys
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root.parent/'intake-recess'));from place import generate
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();temp=a.output.with_suffix('.recess.dnm');generate(a.baseline,temp,temp.with_suffix('.json'),-3.1);subprocess.run([sys.executable,str(root/'channel.py'),'--baseline',str(temp),'--output',str(a.output),'--report',str(a.report)],check=True)
