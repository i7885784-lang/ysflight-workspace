"""Repackage previously verified games; no native launch or repeated gear tests."""
from pathlib import Path
import sys,os,json,subprocess,zipfile,hashlib,struct,urllib.request,urllib.error
root=Path(__file__).resolve().parent;repo=os.environ['GITHUB_REPOSITORY'];branch=os.environ['TASK_BRANCH'];work=Path('delivery');work.mkdir(exist_ok=True);tag='su34-unarmed-intakes-20261117';sha=lambda b:hashlib.sha256(b).hexdigest()
def api(path):return json.loads(subprocess.check_output(['gh','api',path],text=True,encoding='utf-8'))
def download(asset,path):
 with path.open('wb') as f:subprocess.run(['gh','api',f'repos/{repo}/releases/assets/{asset["id"]}','-H','Accept: application/octet-stream'],stdout=f,check=True)
 assert 'sha256:'+sha(path.read_bytes())==asset['digest']
old=api(f'repos/{repo}/releases/448610840');assert old['draft'];assets={a['name']:a for a in old['assets']}
body='Су-34 без оружейных пилонов. Исправлено затемнение10 подтверждённых внутренних граней потолка обоих воздухозаборников: раньше они выглядели как светлые просветы.864 луча сечений и площадь задних экранов проверены; новых накладок внутри нет. Удалены6 подкрыльевых пилонов, центральный пилон, исходные направляющие законцовок и собственные дубли направляющих; отверстия в торцах крыльев закрыты по существующему контуру. Исходные вершины, остальные меши и все анимации сохранены. Удалены6оружейных точек, штатная загрузка ракет и стартовые боеприпасы Су-34. Другие самолёты, управление, физика и коллайдер не изменены. Реальные игровые кадры просмотрены подWine x64, повторных nativeWindowsзапусков нет. ZIP/PE32/PE32+ и неизменность остальных файлов проверяются упаковщиком. Запуск runtime/Play_Su34_Current.bat. Полные архивы остаются в авторизованном черновике согласно PROJECT.md.'
payload=dict(tag_name=tag,target_commitish=branch,draft=True,name='Су-34: цельные тёмные каналы и удалённые оружейные пилоны',body=body)
existing=next((x for x in api(f'repos/{repo}/releases') if x['tag_name']==tag),None)
r=existing if existing is not None else json.loads(subprocess.run(['gh','api','--method','POST',f'repos/{repo}/releases','--input','-'],input=json.dumps(payload),text=True,capture_output=True,check=True).stdout);assert r['draft'];rows=[];model=None
expected={32:'e649db35440467ae336ea104417ffed11dd3e5f2b4bc97e6a2e5981aa4e69872',64:'58f7a5fecc27f64bb0602d640d214f6159044f5fd2af62443f962abf097d2b51'}
for bits,arch in [(32,'x86'),(64,'x64')]:
 inp=work/f'old-{arch}.zip';download(assets[f'Su34_IntakeSeams_Windows_{arch}.zip'],inp)
 with zipfile.ZipFile(inp) as z:
  if model is None:
   (work/'baseline.dnm').write_bytes(z.read('runtime/aircraft/su34.dnm'));(work/'baseline.dat').write_bytes(z.read('runtime/aircraft/su34.dat'));subprocess.run([sys.executable,str(root/'repair.py'),'--baseline',str(work/'baseline.dnm'),'--output',str(work/'su34.dnm'),'--report',str(work/'shade.json'),'--dat-baseline',str(work/'baseline.dat'),'--dat-output',str(work/'su34.dat')],check=True);model=(work/'su34.dnm').read_bytes();assert sha(model)=='d4dc6f68fe3761a9a5d84b8823af728dedca023e8e7c8c7ff06dde5e931a81e7'
  dat=(work/'su34.dat').read_bytes();assert sha(dat)=='5f9ca92045f8beca148959957cc5baff7129a969da65368a91741a3a7f4bd7df'
  exe=z.read(f'runtime/ysflight{bits}_gl1.exe');assert sha(exe)==expected[bits];o=struct.unpack_from('<I',exe,0x3c)[0];assert exe[o:o+4]==b'PE\0\0';machine=struct.unpack_from('<H',exe,o+4)[0];assert machine==(0x14c if bits==32 else 0x8664);assert struct.unpack_from('<H',exe,o+24)[0]==(0x10b if bits==32 else 0x20b)
  passport=json.loads(z.read('runtime/ARCHITECTURE.json'));passport.update(model_sha256=sha(model),dat_sha256=sha(dat),current_change='Complete inward ceiling shade; no weapon pylons or default loadout; original EXEs and rig',native_windows_launch_verified=False,previous_exe_launch_verified=True,current_visual_review='Actual Wine x64 low-front, underside, frontal and oblique views; no native Windows relaunch')
  repl={'runtime/aircraft/su34.dnm':model,'runtime/aircraft/su34.dat':dat,'runtime/aircraft/su34_coarse.dnm':model,'runtime/ARCHITECTURE.json':json.dumps(passport,indent=2).encode(),'runtime/SOURCE_DOWNLOADS.txt':(r['html_url']+'\nSu34_UnarmedIntakes_CorrespondingSources.zip\n').encode(),'Su34_IntakeClean_README_RU.txt':body.encode(),'START_HERE_RU.txt':body.encode(),'SU34_SEAM_FIX_REPORT_RU.md':body.encode()};out=work/f'Su34_UnarmedIntakes_Windows_{arch}.zip'
  with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
   for n in z.namelist():dst.writestr(n,repl.get(n,z.read(n)))
  with zipfile.ZipFile(out) as verify:
   assert verify.testzip() is None;assert verify.read('runtime/aircraft/su34.dnm')==model;assert verify.read('runtime/aircraft/su34_coarse.dnm')==model;assert verify.read('runtime/aircraft/su34.dat')==dat
   for n in z.namelist():
    if n not in repl:assert verify.read(n)==z.read(n)
 rows.append(dict(bits=bits,file=out.name,sha256=sha(out.read_bytes()),bytes=out.stat().st_size,exe_sha256=sha(exe),machine=machine,model_sha256=sha(model),dat_sha256=sha(dat),repeat_native_launch_test=False))
 inp.unlink()
source=work/'previous-sources.zip';download(assets['Su34_IntakeSeams_CorrespondingSources.zip'],source);out=work/'Su34_UnarmedIntakes_CorrespondingSources.zip'
with zipfile.ZipFile(source) as oldsrc,zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
 for n in oldsrc.namelist():dst.writestr(n,oldsrc.read(n))
 
 for script in ['repair.py']:dst.write(root/script,'su34-unarmed-intakes/'+script)
 dst.writestr('su34-unarmed-intakes/baseline/su34.dat',(work/'baseline.dat').read_bytes());dst.writestr('su34-unarmed-intakes/generated/su34.dat',dat);dst.writestr('su34-unarmed-intakes/baseline/su34.dnm',(work/'baseline.dnm').read_bytes());dst.writestr('su34-unarmed-intakes/generated/su34.dnm',model);dst.writestr('su34-unarmed-intakes/README.txt','Run python su34-unarmed-intakes/repair.py --baseline su34-unarmed-intakes/baseline/su34.dnm --output su34.dnm --report shade.json --dat-baseline su34-unarmed-intakes/baseline/su34.dat --dat-output su34.dat; numpy2.3.5 shapely2.1.2 Pillow required. Previous engine and all upstream patch sources retained.\n')
with zipfile.ZipFile(out) as verify:
 assert verify.testzip() is None
 assert verify.read('su34-unarmed-intakes/generated/su34.dnm')==model
 assert sha(verify.read('su34-unarmed-intakes/baseline/su34.dnm'))=='4aaaedfe34aee1247861eec4d2547642acba1b4aa36b17ccc3d8fbef36909eb9'
(work/'packages.json').write_text(json.dumps(rows,indent=2));deliver=[work/x['file'] for x in rows]+[out,work/'packages.json'];sums=work/'SHA256SUMS.txt';sums.write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in deliver));deliver.append(sums)
for p in deliver:subprocess.run(['gh','release','upload',tag,str(p),'--repo',repo],check=True)
r=api(f'repos/{repo}/releases/{r["id"]}');assert r['draft']
for a in r['assets']:
 p=work/a['name'];assert a['digest']=='sha256:'+sha(p.read_bytes())
try:urllib.request.urlopen(r['assets'][0]['browser_download_url'],timeout=20);raise RuntimeError('Private model exposed')
except urllib.error.HTTPError as e:assert e.code==404
print(json.dumps(dict(release_id=r['id'],url=r['html_url'],draft=True,assets=[dict(name=a['name'],url=a['browser_download_url'],digest=a['digest'],size=a['size']) for a in r['assets']]),ensure_ascii=False))
