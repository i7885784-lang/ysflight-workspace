from pathlib import Path
import hashlib,urllib.request,zipfile,struct,subprocess,sys
ROOT=Path(__file__).resolve().parent
BASE={32:('x86','4a30f79a697f558979e3f1b1f8d23ede083c0c0769ff79e54d58bd10912637a4'),64:('x64','62f5d07fe623880dbb89862bec7e77e00643efd13bcca0b100b361ff03d69d52')}
MODEL='6173c6cc9d8e383409ee19f3f5e54ab2c9a787481599c1cb8939fa389d337677'
def sha(b):return hashlib.sha256(b).hexdigest()
def pe(b,bits):
 o=struct.unpack_from('<I',b,0x3c)[0];assert b[o:o+4]==b'PE\0\0';assert struct.unpack_from('<H',b,o+4)[0]==(0x14c if bits==32 else 0x8664);assert struct.unpack_from('<H',b,o+24)[0]==(0x10b if bits==32 else 0x20b)
def baseline(bits,work):
 arch,h=BASE[bits];p=work/f'Su30SM_VectorNozzles_Windows_{arch}.zip';work.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  u='https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-nozzle-vectoring-20261115/'+p.name
  with urllib.request.urlopen(u,timeout=120) as r,p.open('wb') as f:
   import shutil;shutil.copyfileobj(r,f)
 assert sha(p.read_bytes())==h;return p
def generate(path,work):
 if sys.platform=='win32':
  import os,json
  repo=os.environ['GITHUB_REPOSITORY'];releases=json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/releases'],text=True,encoding='utf-8'));release=next(x for x in releases if x['tag_name']=='su34-intake-front-20261117');assert release['draft'];asset=next(x for x in release['assets'] if x['name']=='Su34_IntakeFront_Model.dnm')
  out=work/'su34.dnm'
  with out.open('wb') as f:subprocess.run(['gh','api',f'repos/{repo}/releases/assets/{asset["id"]}','-H','Accept: application/octet-stream'],stdout=f,check=True)
  b=out.read_bytes();assert sha(b)==MODEL;return b
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None;(work/'baseline.dnm').write_bytes(z.read('runtime/aircraft/su34.dnm'))
 subprocess.run([sys.executable,str(ROOT/'fix.py'),'--baseline',str(work/'baseline.dnm'),'--output',str(work/'su34.dnm'),'--report',str(work/'geometry.json')],check=True)
 b=(work/'su34.dnm').read_bytes();assert sha(b)==MODEL;return b
