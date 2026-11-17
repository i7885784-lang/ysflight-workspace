"""Repackage previously verified games; no native launch or repeated gear tests."""
from pathlib import Path
import sys,os,json,subprocess,zipfile,hashlib,struct,urllib.request,urllib.error
root=Path(__file__).resolve().parent;repo=os.environ['GITHUB_REPOSITORY'];branch=os.environ['TASK_BRANCH'];work=Path('delivery');work.mkdir(exist_ok=True);tag='su34-intake-recess-20261117';sha=lambda b:hashlib.sha256(b).hexdigest()
def api(path):return json.loads(subprocess.check_output(['gh','api',path],text=True,encoding='utf-8'))
def download(asset,path):
 with path.open('wb') as f:subprocess.run(['gh','api',f'repos/{repo}/releases/assets/{asset["id"]}','-H','Accept: application/octet-stream'],stdout=f,check=True)
 assert 'sha256:'+sha(path.read_bytes())==asset['digest']
old=api(f'repos/{repo}/releases/448183937');assert old['draft'];assets={a['name']:a for a in old['assets']}
body='Обе внутренние тёмные задние поверхности перенесены с Z=-1.40 на Z=-2.35 м, на 95 см глубже, и подогнаны к свободному сечению своих каналов. Их плоскости имеют одну глубину. Цвета, существующая обшивка, наружная геометрия, шасси, ниши и анимации не менялись. Цель — уменьшить видимость контуров отдельных вставок у входов. В игре просмотрены передний и соседний ракурсы под Wine x64. Повторные испытания запуска и циклы шасси не проводились по просьбе владельца. Используются прежние разные исполняемые файлы x86 и x64.'
payload=dict(tag_name=tag,target_commitish=branch,draft=True,name='Су-34: одинаковая глубина задних поверхностей впуска',body=body)
r=json.loads(subprocess.run(['gh','api','--method','POST',f'repos/{repo}/releases','--input','-'],input=json.dumps(payload),text=True,capture_output=True,check=True).stdout);assert r['draft'];rows=[];model=None
expected={32:'e649db35440467ae336ea104417ffed11dd3e5f2b4bc97e6a2e5981aa4e69872',64:'58f7a5fecc27f64bb0602d640d214f6159044f5fd2af62443f962abf097d2b51'}
for bits,arch in [(32,'x86'),(64,'x64')]:
 inp=work/f'old-{arch}.zip';download(assets[f'Su34_IntakeFront_Windows_{arch}.zip'],inp)
 with zipfile.ZipFile(inp) as z:
  if model is None:
   (work/'baseline.dnm').write_bytes(z.read('runtime/aircraft/su34.dnm'));subprocess.run([sys.executable,str(root/'recess.py'),'--baseline',str(work/'baseline.dnm'),'--output',str(work/'su34.dnm'),'--report',str(work/'shade.json')],check=True);model=(work/'su34.dnm').read_bytes();assert sha(model)=='a2f8a648d43a32e3e300f9aec83e82933182704e6e5d1ccefed95925602c3100'
  exe=z.read(f'runtime/ysflight{bits}_gl1.exe');assert sha(exe)==expected[bits];o=struct.unpack_from('<I',exe,0x3c)[0];assert exe[o:o+4]==b'PE\0\0';machine=struct.unpack_from('<H',exe,o+4)[0];assert machine==(0x14c if bits==32 else 0x8664)
  passport=json.loads(z.read('runtime/ARCHITECTURE.json'));passport.update(model_sha256=sha(model),current_change='Only rear intake surfaces recessed by 0.95m to common Z=-2.35',native_windows_launch_verified=False,previous_exe_launch_verified=True,current_visual_review='Two actual Wine x64 game views; no repeated native launch tests by owner request')
  repl={'runtime/aircraft/su34.dnm':model,'runtime/aircraft/su34_coarse.dnm':model,'runtime/ARCHITECTURE.json':json.dumps(passport,indent=2).encode(),'runtime/SOURCE_DOWNLOADS.txt':(r['html_url']+'\nSu34_IntakeRecess_CorrespondingSources.zip\n').encode(),'Su34_IntakeFront_README_RU.txt':body.encode()};out=work/f'Su34_IntakeRecess_Windows_{arch}.zip'
  with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
   for n in z.namelist():dst.writestr(n,repl.get(n,z.read(n)))
 rows.append(dict(bits=bits,file=out.name,sha256=sha(out.read_bytes()),bytes=out.stat().st_size,exe_sha256=sha(exe),machine=machine,model_sha256=sha(model),repeat_native_launch_test=False))
 inp.unlink()
source=work/'previous-sources.zip';download(assets['Su34_IntakeFront_CorrespondingSources.zip'],source);out=work/'Su34_IntakeRecess_CorrespondingSources.zip'
with zipfile.ZipFile(source) as oldsrc,zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
 for n in oldsrc.namelist():dst.writestr(n,oldsrc.read(n))
 dst.write(root/'recess.py','su34-intake-recess/recess.py');dst.write(root/'place.py','su34-intake-recess/place.py');dst.writestr('su34-intake-recess/baseline/su34.dnm',(work/'baseline.dnm').read_bytes());dst.writestr('su34-intake-recess/generated/su34.dnm',model);dst.writestr('su34-intake-recess/README.txt','Run python su34-intake-recess/recess.py --baseline su34-intake-recess/baseline/su34.dnm --output su34.dnm --report shade.json; numpy required. Previous engine and all upstream patch sources retained.\n')
(work/'packages.json').write_text(json.dumps(rows,indent=2));deliver=[work/x['file'] for x in rows]+[out,work/'packages.json'];sums=work/'SHA256SUMS.txt';sums.write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in deliver));deliver.append(sums)
for p in deliver:subprocess.run(['gh','release','upload',tag,str(p),'--repo',repo],check=True)
r=api(f'repos/{repo}/releases/{r["id"]}');assert r['draft']
for a in r['assets']:
 p=work/a['name'];assert a['digest']=='sha256:'+sha(p.read_bytes())
try:urllib.request.urlopen(r['assets'][0]['browser_download_url'],timeout=20);raise RuntimeError('Private model exposed')
except urllib.error.HTTPError as e:assert e.code==404
print(json.dumps(dict(release_id=r['id'],url=r['html_url'],draft=True,assets=[dict(name=a['name'],url=a['browser_download_url'],digest=a['digest'],size=a['size']) for a in r['assets']]),ensure_ascii=False))
