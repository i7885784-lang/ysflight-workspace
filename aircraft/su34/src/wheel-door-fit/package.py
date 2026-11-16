from common import *
import json,os,base64
REPO=os.environ['GITHUB_REPOSITORY'];BRANCH=os.environ['TASK_BRANCH'];TAG='su34-wheel-door-fit-20261116';work=Path('delivery');work.mkdir(exist_ok=True)
def api(path):return json.loads(subprocess.check_output(['gh','api',path],text=True))
def native(bits):
 d=api(f'repos/{REPO}/contents/aircraft/su34/work/wheel-door-fit/native-{bits}.json?ref={BRANCH}');n=json.loads(base64.b64decode(d['content']));assert n['passed'] and n['model_sha256']==MODEL;return n
checks={b:native(b) for b in [32,64]}
payload=dict(tag_name=TAG,target_commitish=BRANCH,draft=True,name='Су-34: подгонка боковых створок и рамки',body='Локально обрезаны выступающие контуры OriginalSideDoorLWheel/RightWheel и прилегающая неподвижная рамка. Сохранены толщина, палитра, оси, родительские трансформации, все состояния анимации, стойки и колёса. Предыдущая правка передних створок сохранена. Движок и остальные самолёты прежние. Сравнение в screenshots/su34-wheel-door-fit. Разрядность PE и целостность ZIP проверены; нативные Windows проверки описаны в JSON и отчёте. Модель распространяется только через авторизованный черновик по aircraft/su34/PROJECT.md.')
r=next(x for x in api(f'repos/{REPO}/releases') if x['tag_name']==TAG);assert r['draft']
r=json.loads(subprocess.run(['gh','api','--method','PATCH',f'repos/{REPO}/releases/{r["id"]}','--input','-'],input=json.dumps(payload),text=True,capture_output=True,check=True).stdout);assert r['draft']
rows=[];model=None;baseline_model=None
for bits in [32,64]:
 p=baseline(bits,work);model=generate(p,work);arch=BASE[bits][0];out=work/f'Su34_WheelDoorFit_Windows_{arch}.zip'
 with zipfile.ZipFile(p) as old:
  exe=old.read(f'runtime/ysflight{bits}_gl1.exe');pe(exe,bits);assert sha(exe)==checks[bits]['exe_sha256'];baseline_model=old.read('runtime/aircraft/su34.dnm');assert old.read('runtime/aircraft/su34_coarse.dnm')==baseline_model
  passport=json.loads(old.read('runtime/ARCHITECTURE.json'));passport.update(exe_sha256=sha(exe),model_aircraft='SU-34_FULLBACK',model_sha256=MODEL,engine_recompiled=False,current_change='Local contour fit of two main wheel doors and their static surround; all rig and other meshes unchanged',native_windows_launch_verified=True,native_windows_run=os.environ['GITHUB_RUN_ID'])
  repl={'runtime/aircraft/su34.dnm':model,'runtime/aircraft/su34_coarse.dnm':model,'runtime/ARCHITECTURE.json':json.dumps(passport,indent=2).encode(),'runtime/SOURCE_DOWNLOADS.txt':(r['html_url']+'\nSu34_WheelDoorFit_CorrespondingSources.zip\n').encode()}
  with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for n in old.namelist():z.writestr(n,repl.get(n,old.read(n)))
   z.writestr('Su34_WheelDoorFit_README_RU.txt',payload['body'])
   exe32='ysflight32_gl1.exe'
   z.writestr('runtime/Play_Su34_Current.bat',f'@echo off\ncd /d "%~dp0"\nysflight{bits}_gl1.exe -script Start_Su34.script\n')
  with zipfile.ZipFile(out) as z:
   assert z.testzip() is None;assert all(z.read(n)==old.read(n) for n in old.namelist() if n not in repl)
 rows.append(dict(bits=bits,file=out.name,sha256=sha(out.read_bytes()),bytes=out.stat().st_size,exe_sha256=sha(exe),model_sha256=MODEL,native_windows_verified=True))
assert rows[0]['exe_sha256']!=rows[1]['exe_sha256']
source=work/'original-sources.zip'
with urllib.request.urlopen('https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/su30sm-nozzle-vectoring-20261115/Su30SM_VectorNozzles_FullSources.zip',timeout=120) as response:source.write_bytes(response.read())
assert sha(source.read_bytes())=='87f5f71df79754f8f8586fba358f89319e9b8958e6e88d708fe48b0994c06dfb'
sources=work/'Su34_WheelDoorFit_CorrespondingSources.zip'
with zipfile.ZipFile(source) as old,zipfile.ZipFile(sources,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 assert old.testzip() is None
 for n in old.namelist():z.writestr(n,old.read(n))
 for f in ROOT.glob('*.py'):z.write(f,'su34-wheel-door-fit/'+f.name)
 z.writestr('su34-wheel-door-fit/baseline/su34.dnm',baseline_model);z.writestr('su34-wheel-door-fit/generated/su34.dnm',model)
for bits,n in checks.items():(work/f'native-{bits}.json').write_text(json.dumps(n,indent=2))
(work/'packages.json').write_text(json.dumps(rows,indent=2));assets=[work/x['file'] for x in rows]+[sources,work/'packages.json',work/'native-32.json',work/'native-64.json'];sums=work/'SHA256SUMS.txt';sums.write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in assets));assets.append(sums)
for p in assets:subprocess.run(['gh','release','upload',TAG,str(p),'--repo',REPO],check=True)
# Native checks have finished; remove only our temporary private model transfer asset.
for temporary in api(f'repos/{REPO}/releases/{r["id"]}')['assets']:
 if temporary['name']=='Su34_WheelDoorFit_Model.dnm':subprocess.run(['gh','api','--method','DELETE',f'repos/{REPO}/releases/assets/{temporary["id"]}'],check=True)
d=api(f'repos/{REPO}/releases/{r["id"]}');assert d['draft']
for a in d['assets']:
 p=work/a['name'];v=work/'verify.tmp'
 with v.open('wb') as f:subprocess.run(['gh','api',f'repos/{REPO}/releases/assets/{a["id"]}','-H','Accept: application/octet-stream'],stdout=f,check=True)
 assert sha(v.read_bytes())==sha(p.read_bytes());v.unlink()
 try:urllib.request.urlopen(a['browser_download_url'],timeout=20);raise RuntimeError('SU34 draft exposed anonymously')
 except urllib.error.HTTPError as e:assert e.code==404
print(json.dumps(dict(release_id=d['id'],draft=True,url=d['html_url'],assets=[dict(name=a['name'],url=a['browser_download_url'],size=a['size']) for a in d['assets']]),ensure_ascii=False))
