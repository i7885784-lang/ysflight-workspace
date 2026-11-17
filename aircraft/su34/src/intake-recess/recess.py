from pathlib import Path
import argparse
from place import generate
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();generate(a.baseline,a.output,a.report,-2.35)
